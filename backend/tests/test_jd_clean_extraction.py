"""
Unit tests verifying clean, genuine extraction from Job Descriptions and Resumes.
Ensures no noisy sentence fragments ('or a related field.', 'and experience)', etc.)
and no academic degree requirements ('Bachelor's degree in...') ever pollute hard skills.
"""

import pytest
from app.services.llm_service import (
    extract_skills_from_text_sections,
    extract_skills_and_education_from_sections,
    fallback_extract_entities,
    infer_document_role,
)
from app.services.scoring_service import compute_overall_alignment

USER_JD_SNIPPET = """
Preferred Qualifications
• Bachelor's degree in Computer Science, Information Technology, or a related field.
• Experience with Redux, React Navigation, or Context API.
• Knowledge of Firebase, Expo, or push notifications.
• Internship or academic projects using React Native.
What We Offer
• Competitive salary and comprehensive benefits.
"""

ECE_CANDIDATE_RESUME = """
Rahul Sharma
Electrical & Electronics Engineer (ECE)
Email: rahul@example.com

Technical Skills:
• Programming Languages: Embedded C, C++, Python, MATLAB
• Hardware & Microcontrollers: STM32, ARM Cortex-M4, Arduino, ESP32
• Protocols: I2C, SPI, UART, CAN, PWM
• Tools & EDA: Altium Designer, KiCad, Keil uVision, STM32CubeIDE

Education:
Bachelor of Technology in Electronics and Communication Engineering (ECE)
"""

def test_user_jd_clean_skills_extraction():
    """Verifies that only genuine skills are extracted from the user's preferred qualifications."""
    skills, edu = extract_skills_and_education_from_sections(USER_JD_SNIPPET)

    # 1. Genuine technical skills must be present
    assert "Redux" in skills
    assert "React Navigation" in skills
    assert "Context API" in skills
    assert "Firebase" in skills
    assert "Expo" in skills
    assert "Push Notifications" in skills
    assert "React Native" in skills

    # 2. Garbage fragments must be eliminated
    assert "or a related field." not in skills
    assert "and experience)" not in skills
    assert "What We Offer" not in skills

    # 3. Degrees must be routed to education, NOT skills
    assert not any("bachelor" in s.lower() for s in skills)
    assert not any("degree" in s.lower() for s in skills)
    assert any("bachelor" in e.lower() for e in edu)

def test_user_jd_entities_no_mechanical_spill():
    """Verifies fallback_extract_entities on user JD correctly infers mobile/software without mechanical spillage."""
    entities = fallback_extract_entities(USER_JD_SNIPPET, is_jd=True)

    # Hard skills check
    assert "Redux" in entities.hard_skills
    assert "React Native" in entities.hard_skills
    assert "Firebase" in entities.tools_and_tech
    assert "Expo" in entities.tools_and_tech
    assert "Firebase" not in entities.hard_skills

    # No degree or fragments in hard skills
    for s in entities.hard_skills:
        assert "related field" not in s.lower()
        assert "experience)" not in s.lower()
        assert "bachelor" not in s.lower()
        assert "what we offer" not in s.lower()

    # Education must contain degree
    assert any("bachelor" in e.lower() for e in entities.education)

    # Role and domain must be software/mobile, NOT mechanical
    assert "Mobile" in entities.inferred_role or "Software" in entities.inferred_role
    assert entities.inferred_role != "Mechanical Engineer"
    assert entities.domain_knowledge != ["Mechanical Engineering"]

def test_ece_resume_vs_mobile_jd_alignment():
    """
    Simulates the exact user scenario: ECE resume uploaded against Mobile/React Native JD.
    Verifies that the missing skills list contains ONLY genuine JD requirements.
    """
    res_entities = fallback_extract_entities(ECE_CANDIDATE_RESUME, is_jd=False)
    jd_entities = fallback_extract_entities(USER_JD_SNIPPET, is_jd=True)

    score, breakdowns, matches = compute_overall_alignment(
        resume_entities=res_entities,
        jd_entities=jd_entities,
        company_type="mid_size_product"
    )

    # Candidate has ECE background, JD wants React Native / Mobile -> Should have low/medium score
    assert 0.0 <= score <= 60.0

    missing_items = [m.skill for m in matches if m.status == "Missing"]

    # All missing items must be real skills
    assert any("Redux" in s for s in missing_items)
    assert any("React Native" in s for s in missing_items)

    # Garbage fragments MUST NOT be in missing items
    for m in missing_items:
        assert "related field" not in m.lower()
        assert "and experience" not in m.lower()
        assert "bachelor" not in m.lower()
        assert "what we offer" not in m.lower()
        assert m.lower() != "mechanical engineering"

def test_no_duplicate_skills_and_no_salary_tokens():
    """
    Directly tests the user's scenario:
    1. JD mentions: Git, GitHub for version control, Firebase, Expo, Context API, Redux.
    2. JD has salary section: 'Salary: ₹4 LPA – ₹8 LPA (Based on experience)'.
    3. Resume matches Git, GitHub, Firebase, Expo, Context API.
    Verifies:
    - Zero duplicate entries in matches list (Git, GitHub, Firebase, Expo, Context API appear once).
    - Neither '₹4 LPA – ₹8 LPA', '4-8 LPA', nor 'Based on' ever appears in skills or matches.
    """
    user_jd_with_salary = """
Role: React Native Mobile Developer
Preferred Qualifications:
• Experience with Git and GitHub for version control
• Knowledge of Firebase, Expo, and Context API
• Experience with Redux and React Navigation
Salary & Remuneration:
• ₹4 LPA – ₹8 LPA (Based on experience)
"""
    user_resume = """
Full Stack Mobile Developer
Technical Skills:
• Git, GitHub, Firebase, Expo, Context API, JavaScript, React Native
"""
    res_entities = fallback_extract_entities(user_resume, is_jd=False)
    jd_entities = fallback_extract_entities(user_jd_with_salary, is_jd=True)

    # 1. Salary lines must not leak into any category of extracted entities
    all_jd_extracted = (
        jd_entities.hard_skills + 
        jd_entities.tools_and_tech + 
        jd_entities.soft_skills + 
        jd_entities.domain_knowledge
    )
    for skill in all_jd_extracted:
        s_lower = skill.lower()
        assert "lpa" not in s_lower
        assert "₹" not in s_lower
        assert "based on" not in s_lower
        assert "salary" not in s_lower
        assert "remuneration" not in s_lower

    # 2. Compute alignment
    score, breakdowns, matches = compute_overall_alignment(
        resume_entities=res_entities,
        jd_entities=jd_entities,
        company_type="mid_size_product"
    )

    # 3. Check for duplicates in matches
    matched_skill_names = [m.skill.lower() for m in matches]
    assert len(matched_skill_names) == len(set(matched_skill_names)), f"Duplicates detected in matches: {matched_skill_names}"

    # Specific skills must appear at most once
    for skill_name in ["git", "github", "firebase", "expo", "context api"]:
        count = sum(1 for s in matched_skill_names if s == skill_name)
        assert count <= 1, f"Skill '{skill_name}' appeared {count} times in matches!"

    # 4. Check that missing items do NOT contain salary or 'based on'
    missing_skills = [m.skill.lower() for m in matches if m.status == "Missing"]
    for m in missing_skills:
        assert "lpa" not in m
        assert "₹" not in m
        assert "based on" not in m
        assert "salary" not in m

