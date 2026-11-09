"""
Gap Analysis and Recruiter Rejection Explanation Service for SkillBridge.
Prioritizes candidate skill gaps based on JD frequency, category weights, and severity.
Generates recruiter-style explanations linking each gap to concrete resume evidence.
"""

import json
import re
import time
from typing import List, Dict, Any, Optional
from google.genai import types

from app.models.schemas import SkillMatchItem, ExtractedEntities, RejectionReason
from app.services.llm_service import get_gemini_client, get_hash, _LLM_CACHE
from app.services.scoring_service import load_company_profiles

def prioritize_gaps(
    matches: List[SkillMatchItem],
    jd_text: str,
    company_type: str = "mid_size_product"
) -> List[SkillMatchItem]:
    """
    Ranks skill gaps by business and hiring importance.

    WHAT:
    1. Filters requirements that are 'Missing' or 'Underrepresented'.
    2. Calculates priority weight based on:
       - Category weight from the company profile (e.g. enterprise bank values security higher).
       - JD mention frequency (how often the skill or related keywords appear in the JD).
       - Gap severity ('Missing' has higher penalty than 'Underrepresented').
    3. Assigns an importance rank (1 being the most critical gap).

    WHY:
    Candidates shouldn't try to learn everything at once. They need to know which 2-3 gaps
    will immediately disqualify them in recruiter screenings.
    """
    profiles = load_company_profiles()
    profile = profiles.get(company_type, profiles.get("mid_size_product"))
    weights = profile.get("weights", {})

    lower_jd = jd_text.lower()
    gaps: List[SkillMatchItem] = []

    for item in matches:
        if item.status in ["Missing", "Underrepresented"]:
            # 1. Base category weight (default 0.25)
            cat_weight = weights.get(item.category, 0.25)

            # 2. JD frequency boost: count occurrences of skill name in JD
            skill_token = item.skill.lower().strip()
            occurrences = len(re.findall(r'\b' + re.escape(skill_token) + r'\b', lower_jd))
            frequency_boost = min(occurrences * 0.15, 0.45)

            # 3. Severity factor: Missing is more critical than partial match
            severity = 1.0 if item.status == "Missing" else 0.6

            # Priority score formula
            priority_score = (cat_weight * 1.5 + frequency_boost) * severity

            # Store temporarily as attribute or tuple
            gaps.append((priority_score, item))

    # Sort in descending order of priority score
    gaps.sort(key=lambda x: x[0], reverse=True)

    # Assign integer rank (1, 2, 3...)
    ranked_gaps: List[SkillMatchItem] = []
    for rank, (_, item) in enumerate(gaps, start=1):
        item.importance_rank = rank
        ranked_gaps.append(item)

    return ranked_gaps

# -------------------------------------------------------------
# Recruiter-Perspective Rejection Reason Generation
# -------------------------------------------------------------

RECRUITER_SYSTEM_PROMPT = """
You are an executive hiring manager and talent acquisition leader across diverse corporate, healthcare,
institutional, creative, and technical sectors.
Review the candidate's skill gaps against the target job requirements.
Write 3 to 4 realistic, constructive "Potential Rejection Reasons" from an internal hiring team screening perspective.

Format your response as strictly valid JSON matching this schema:
[
  {
    "title": "Short headline (e.g. 'Limited Demonstrable Track Record in Financial Modeling')",
    "reason": "Recruiter-style explanation of why this gap creates hiring risk for this specific role.",
    "linked_gap": "The exact missing or underrepresented skill",
    "resume_evidence": "What the resume currently displays or omits as concrete evidence",
    "actionable_fix": "Clear advice on a project, credential, or case study the candidate should complete to overcome this rejection reason"
  }
]
Do NOT output markdown backticks. Return only raw JSON.
"""

def fallback_rejection_reasons(
    gaps: List[SkillMatchItem],
    resume_entities: ExtractedEntities,
    company_type: str
) -> List[RejectionReason]:
    """
    Generates realistic, recruiter-perspective rejection reasons using heuristics
    when Gemini API is unconfigured or unreachable. Works for any profession.
    """
    reasons: List[RejectionReason] = []
    top_gaps = gaps[:4]

    company_labels = {
        "early_stage_startup": "an agile growth organization where team members must execute autonomously",
        "enterprise_bank": "an established enterprise institution with strict standards, compliance, and governance",
        "big_tech": "a fast-paced scale organization demanding high output, domain rigor, and reliability",
        "mid_size_product": "a market-leading organization prioritizing cross-functional execution and outcome delivery",
        "consulting_service": "a client-focused advisory firm where professionals interface directly with stakeholders"
    }
    context_desc = company_labels.get(company_type, "a competitive hiring organization")

    for gap in top_gaps:
        skill_name = gap.skill
        cat = gap.category

        if cat == "hard_skills":
            title = f"Limited Demonstrable Track Record in {skill_name}"
            reason = (
                f"For {context_desc}, {skill_name} is considered a vital qualification for daily responsibilities. "
                "The hiring team will likely screen out candidates who cannot demonstrate practical, verified experience with this requirement."
            )
            evidence = (
                f"The resume does not explicitly list '{skill_name}' under core skills, certifications, or bullet points, "
                f"suggesting limited applied exposure compared to competing applicants."
            )
            fix = (
                f"Complete a credential, case study, or documented project demonstrating {skill_name}, and add a quantified achievement bullet to your resume."
            )
        elif cat == "tools_and_tech":
            title = f"Tooling & Platform Requirement Gap ({skill_name})"
            reason = (
                f"Professionals at {context_desc} rely on {skill_name} for daily operational workflows. "
                f"Without hands-on familiarity, onboarding and deliverable timelines could be delayed."
            )
            evidence = (
                f"'{skill_name}' is not currently highlighted in the candidate's tools or skills sections."
            )
            fix = (
                f"Attain certified or documented proficiency with {skill_name} and add a concrete example of its application to your work history."
            )
        elif cat == "domain_knowledge":
            title = f"Need for Direct Domain Experience in {skill_name}"
            reason = (
                f"This position requires functional intuition around {skill_name}. Hiring teams prioritize candidates who understand industry best practices and core standards in this area."
            )
            evidence = (
                f"While the candidate presents strong foundational skills, there is minimal explicit work history in {skill_name}."
            )
            fix = (
                f"Review standard operating frameworks in {skill_name} and showcase relevant coursework, projects, or transferrable accomplishments."
            )
        else:
            title = f"Need Stronger Evidence of {skill_name}"
            reason = (
                f"Reviewers look for clear demonstration of {skill_name} in team collaboration, stakeholder interaction, and execution leadership."
            )
            evidence = (
                f"Bullet points focus on routine activities without highlighting measurable impact, stakeholder coordination, or {skill_name}."
            )
            fix = (
                f"Re-frame your experience bullet points to explicitly showcase how you applied {skill_name} to drive project or business outcomes."
            )

        reasons.append(
            RejectionReason(
                title=title,
                reason=reason,
                linked_gap=skill_name,
                resume_evidence=evidence,
                actionable_fix=fix
            )
        )

    return reasons

def generate_rejection_reasons(
    gaps: List[SkillMatchItem],
    resume_entities: ExtractedEntities,
    jd_text: str,
    company_type: str = "mid_size_product"
) -> List[RejectionReason]:
    """
    Generates 3-4 realistic recruiter rejection explanations linking gaps to resume evidence.
    """
    if not gaps:
        return []

    top_gaps = gaps[:4]
    gap_summary = ", ".join([f"{g.skill} ({g.category}, status: {g.status})" for g in top_gaps])
    cache_key = f"rejection_{company_type}_{get_hash(gap_summary)}"

    if cache_key in _LLM_CACHE:
        return [RejectionReason(**item) for item in _LLM_CACHE[cache_key]]

    client = get_gemini_client()
    if not client:
        reasons = fallback_rejection_reasons(gaps, resume_entities, company_type)
        _LLM_CACHE[cache_key] = [r.model_dump() for r in reasons]
        return reasons

    prompt = (
        f"Company Type: {company_type}\n"
        f"Target JD excerpt:\n{jd_text[:1200]}\n\n"
        f"Candidate Resume Skills: {resume_entities.hard_skills + resume_entities.tools_and_tech}\n"
        f"Candidate Experience: {resume_entities.years_of_experience} years\n"
        f"Key Skill Gaps Identified: {gap_summary}\n\n"
        "Generate 3-4 recruiter-style rejection reasons based on this data."
    )

    for attempt in range(2):
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=RECRUITER_SYSTEM_PROMPT,
                    response_mime_type="application/json",
                    temperature=0.2,
                )
            )

            resp_text = response.text.strip()
            if resp_text.startswith("```"):
                resp_text = re.sub(r"^```(?:json)?|```$", "", resp_text, flags=re.MULTILINE).strip()

            parsed = json.loads(resp_text)
            if isinstance(parsed, list):
                reasons = [RejectionReason(**item) for item in parsed]
                _LLM_CACHE[cache_key] = [r.model_dump() for r in reasons]
                return reasons

        except Exception as e:
            print(f"[SkillBridge] Rejection reasons LLM call attempt {attempt+1} failed: {e}")
            time.sleep(1)

    # Fallback if LLM fails
    reasons = fallback_rejection_reasons(gaps, resume_entities, company_type)
    _LLM_CACHE[cache_key] = [r.model_dump() for r in reasons]
    return reasons
