"""
Scoring service module for SkillBridge.
Computes deterministic match scores, categorizes gaps (Strong match, Underrepresented, Missing),
applies company context weight matrices, and calculates category breakdowns.
Includes the predictive match uplift simulator.
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

from app.config import settings
from app.models.schemas import (
    ExtractedEntities,
    SkillMatchItem,
    CategoryBreakdown,
    SimulateResponse,
)
from app.services.embedding_service import find_best_semantic_match

# Locate company profiles configuration JSON
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
PROFILES_FILE = DATA_DIR / "company_profiles.json"

def load_company_profiles() -> Dict[str, Any]:
    """
    Reads company weight profiles from company_profiles.json.
    Falls back to balanced defaults if file is missing.
    """
    if PROFILES_FILE.exists():
        with open(PROFILES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    # Default fallback profile
    return {
        "mid_size_product": {
            "name": "Mid-Size Product Company",
            "weights": {
                "hard_skills": 0.35,
                "tools_and_tech": 0.25,
                "soft_skills": 0.20,
                "domain_knowledge": 0.15,
                "education_and_exp": 0.05
            }
        }
    }

def evaluate_skill_category(
    category_key: str,
    jd_items: List[str],
    resume_items: List[str]
) -> Tuple[List[SkillMatchItem], float, int]:
    """
    Evaluates a list of JD requirements against candidate resume items for a specific category.

    WHAT:
    - Finds best semantic match using cosine similarity.
    - Classifies as 'Strong match', 'Underrepresented', or 'Missing'.
    - Computes raw score (0-100) based on credit assigned.

    WHY:
    Separating category evaluation ensures clear, transparent breakdowns for the user.
    """
    if not jd_items:
        return ([], 100.0, 0)

    matches: List[SkillMatchItem] = []
    total_credit = 0.0
    matched_count = 0

    strong_thresh = settings.similarity_threshold_strong
    partial_thresh = settings.similarity_threshold_partial

    for req in jd_items:
        sim_score, matched_skill = find_best_semantic_match(req, resume_items)

        if sim_score >= strong_thresh:
            status = "Strong match"
            credit = 1.0
            matched_count += 1
        elif sim_score >= partial_thresh:
            status = "Underrepresented"
            credit = sim_score
            matched_count += 1
        else:
            status = "Missing"
            credit = 0.0

        total_credit += credit

        matches.append(
            SkillMatchItem(
                skill=req,
                category=category_key,
                status=status,
                similarity_score=sim_score,
                matched_with=matched_skill if status != "Missing" else None,
            )
        )

    raw_score = round((total_credit / len(jd_items)) * 100.0, 1)
    return (matches, raw_score, matched_count)

def calculate_experience_score(jd_years: float, res_years: float) -> float:
    """
    Calculates candidate experience alignment score (0-100).
    Candidate receives full points if they meet or exceed JD requirements.
    """
    if jd_years <= 0:
        return 100.0
    if res_years >= jd_years:
        return 100.0
    return round((res_years / jd_years) * 100.0, 1)

def compute_overall_alignment(
    resume_entities: ExtractedEntities,
    jd_entities: ExtractedEntities,
    company_type: str = "mid_size_product"
) -> Tuple[float, List[CategoryBreakdown], List[SkillMatchItem]]:
    """
    Main scoring function computing the weighted alignment score and category breakdowns.
    """
    profiles = load_company_profiles()
    profile = profiles.get(company_type, profiles.get("mid_size_product"))
    weights = profile.get("weights", {
        "hard_skills": 0.35,
        "tools_and_tech": 0.25,
        "domain_knowledge": 0.20,
        "soft_skills": 0.15,
        "education_and_exp": 0.05
    })

    all_matches: List[SkillMatchItem] = []
    breakdowns: List[CategoryBreakdown] = []

    # 1. Hard Skills
    hard_matches, hard_score, hard_matched_cnt = evaluate_skill_category(
        "hard_skills", jd_entities.hard_skills, resume_entities.hard_skills
    )
    all_matches.extend(hard_matches)
    w_hard = weights.get("hard_skills", 0.35)
    breakdowns.append(
        CategoryBreakdown(
            category_name="hard_skills",
            display_name="Hard Skills",
            raw_score=hard_score,
            weight=w_hard,
            weighted_score=round(hard_score * w_hard, 2),
            total_items=len(jd_entities.hard_skills),
            matched_items=hard_matched_cnt
        )
    )

    # 2. Tools & Technologies
    tools_matches, tools_score, tools_matched_cnt = evaluate_skill_category(
        "tools_and_tech", jd_entities.tools_and_tech, resume_entities.tools_and_tech
    )
    all_matches.extend(tools_matches)
    w_tools = weights.get("tools_and_tech", 0.25)
    breakdowns.append(
        CategoryBreakdown(
            category_name="tools_and_tech",
            display_name="Tools & Tech",
            raw_score=tools_score,
            weight=w_tools,
            weighted_score=round(tools_score * w_tools, 2),
            total_items=len(jd_entities.tools_and_tech),
            matched_items=tools_matched_cnt
        )
    )

    # 3. Domain Knowledge
    domain_matches, domain_score, domain_matched_cnt = evaluate_skill_category(
        "domain_knowledge", jd_entities.domain_knowledge, resume_entities.domain_knowledge
    )
    all_matches.extend(domain_matches)
    w_domain = weights.get("domain_knowledge", 0.20)
    breakdowns.append(
        CategoryBreakdown(
            category_name="domain_knowledge",
            display_name="Domain Knowledge",
            raw_score=domain_score,
            weight=w_domain,
            weighted_score=round(domain_score * w_domain, 2),
            total_items=len(jd_entities.domain_knowledge),
            matched_items=domain_matched_cnt
        )
    )

    # 4. Soft Skills
    soft_matches, soft_score, soft_matched_cnt = evaluate_skill_category(
        "soft_skills", jd_entities.soft_skills, resume_entities.soft_skills
    )
    all_matches.extend(soft_matches)
    w_soft = weights.get("soft_skills", 0.15)
    breakdowns.append(
        CategoryBreakdown(
            category_name="soft_skills",
            display_name="Soft Skills",
            raw_score=soft_score,
            weight=w_soft,
            weighted_score=round(soft_score * w_soft, 2),
            total_items=len(jd_entities.soft_skills),
            matched_items=soft_matched_cnt
        )
    )

    # 5. Experience & Education
    exp_score = calculate_experience_score(jd_entities.years_of_experience, resume_entities.years_of_experience)
    w_exp = weights.get("education_and_exp", 0.05)
    breakdowns.append(
        CategoryBreakdown(
            category_name="education_and_exp",
            display_name="Experience & Education",
            raw_score=exp_score,
            weight=w_exp,
            weighted_score=round(exp_score * w_exp, 2),
            total_items=1,
            matched_items=1 if exp_score >= 75.0 else 0
        )
    )

    overall_score = sum(b.weighted_score for b in breakdowns)
    overall_score = max(0.0, min(100.0, round(overall_score, 1)))

    # Deduplicate matches across categories so no skill is displayed or reported twice
    status_priority = {"Strong match": 3, "Underrepresented": 2, "Missing": 1}
    best_matches_by_skill: Dict[str, SkillMatchItem] = {}
    for m in all_matches:
        norm_key = m.skill.strip().lower()
        if norm_key not in best_matches_by_skill:
            best_matches_by_skill[norm_key] = m
        else:
            existing = best_matches_by_skill[norm_key]
            existing_rank = (status_priority.get(existing.status, 0), existing.similarity_score)
            new_rank = (status_priority.get(m.status, 0), m.similarity_score)
            if new_rank > existing_rank:
                best_matches_by_skill[norm_key] = m

    all_matches = list(best_matches_by_skill.values())

    return (overall_score, breakdowns, all_matches)

# -------------------------------------------------------------
# Phase 4: Predictive Match Uplift Simulator
# -------------------------------------------------------------

def simulate_skill_uplift(
    all_skill_matches: List[SkillMatchItem],
    acquired_skills: List[str],
    company_type: str = "mid_size_product",
    baseline_score: float = 0.0,
    experience_score: float = 100.0
) -> SimulateResponse:
    """
    Deterministically simulates the score uplift when a candidate decides to learn missing skills.

    WHAT:
    1. Copies the match list and flips any acquired skill from Missing/Underrepresented to Strong match (1.0 credit).
    2. Recalculates category raw scores using the exact same formula.
    3. Re-applies the company weight profile.
    4. Computes the net uplift: new_score - baseline_score.
    5. Crafts an explainable summary explaining the exact category deltas and weighted contribution.

    WHY:
    Consistency is critical. By using the identical scoring formula, numbers are predictable,
    transparent, and fully trustworthy for the candidate.
    """
    profiles = load_company_profiles()
    profile = profiles.get(company_type, profiles.get("mid_size_product"))
    weights = profile.get("weights", {
        "hard_skills": 0.35,
        "tools_and_tech": 0.25,
        "domain_knowledge": 0.20,
        "soft_skills": 0.15,
        "education_and_exp": 0.05
    })
    company_name = profile.get("name", "Target Company")

    acquired_set = {s.strip().lower() for s in acquired_skills}

    # Group matches by category
    categories_dict: Dict[str, List[SkillMatchItem]] = {
        "hard_skills": [],
        "tools_and_tech": [],
        "domain_knowledge": [],
        "soft_skills": [],
    }

    display_names = {
        "hard_skills": "Hard Skills",
        "tools_and_tech": "Tools & Tech",
        "domain_knowledge": "Domain Knowledge",
        "soft_skills": "Soft Skills",
        "education_and_exp": "Experience & Education",
    }

    for item in all_skill_matches:
        if item.category in categories_dict:
            categories_dict[item.category].append(item)

    updated_breakdowns: List[CategoryBreakdown] = []

    # Recalculate each skill category
    for cat_key, items in categories_dict.items():
        if not items:
            raw_score = 100.0
            matched_cnt = 0
            total_cnt = 0
        else:
            total_credit = 0.0
            matched_cnt = 0
            total_cnt = len(items)

            for item in items:
                # Check if this item is marked as acquired in the simulator
                is_acquired = item.skill.strip().lower() in acquired_set

                if is_acquired or item.status == "Strong match":
                    credit = 1.0
                    matched_cnt += 1
                elif item.status == "Underrepresented":
                    credit = item.similarity_score
                    matched_cnt += 1
                else:
                    credit = 0.0

                total_credit += credit

            raw_score = round((total_credit / total_cnt) * 100.0, 1)

        w = weights.get(cat_key, 0.20)
        updated_breakdowns.append(
            CategoryBreakdown(
                category_name=cat_key,
                display_name=display_names.get(cat_key, cat_key),
                raw_score=raw_score,
                weight=w,
                weighted_score=round(raw_score * w, 2),
                total_items=total_cnt,
                matched_items=matched_cnt
            )
        )

    # Also include Experience & Education category
    w_exp = weights.get("education_and_exp", 0.05)
    updated_breakdowns.append(
        CategoryBreakdown(
            category_name="education_and_exp",
            display_name="Experience & Education",
            raw_score=experience_score,
            weight=w_exp,
            weighted_score=round(experience_score * w_exp, 2),
            total_items=1,
            matched_items=1 if experience_score >= 75.0 else 0
        )
    )

    # Compute new simulated overall score
    simulated_score = sum(b.weighted_score for b in updated_breakdowns)
    simulated_score = max(0.0, min(100.0, round(simulated_score, 1)))

    if not acquired_skills:
        uplift = 0.0
        if baseline_score > 0:
            simulated_score = baseline_score
    else:
        uplift = max(0.0, round(simulated_score - baseline_score, 1))

    # Create plain-English explanation
    if acquired_skills:
        skill_str = ", ".join(acquired_skills[:3])
        if len(acquired_skills) > 3:
            skill_str += f" and {len(acquired_skills) - 3} other skills"
        explanation = (
            f"Learning {skill_str} elevates your alignment from {baseline_score}% to {simulated_score}% "
            f"(+{uplift}% net uplift). Under {company_name} weighting, closing these gaps directly raises "
            f"your candidacy into the top-tier interview applicant pool."
        )
    else:
        explanation = "Toggle one or more missing skills below to project your score improvement in real time."

    return SimulateResponse(
        baseline_score=baseline_score,
        simulated_score=simulated_score,
        uplift=uplift,
        updated_breakdowns=updated_breakdowns,
        explanation=explanation
    )
