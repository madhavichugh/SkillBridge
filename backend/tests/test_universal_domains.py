"""
Comprehensive validation test suite across 4 diverse industries:
1. Healthcare (Registered Nurse) - Non-Engineering
2. Marketing & Growth (Digital Marketing Specialist) - Non-Engineering
3. Finance (Senior Financial Analyst) - Non-Engineering
4. Hardware / ECE (Embedded Firmware Engineer) - Engineering
Verifies universal entity extraction, role detection, semantic alignment,
recruiter screening rejection generation, and salary benchmarking.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.llm_service import extract_entities_with_llm, infer_document_role
from app.services.scoring_service import compute_overall_alignment
from app.services.gap_service import prioritize_gaps, generate_rejection_reasons
from app.services.salary_service import compute_salary_insights, match_role_key

client = TestClient(app)

# -------------------------------------------------------------
# Pair 1: Healthcare (Registered Nurse)
# -------------------------------------------------------------
NURSE_RESUME = """
Sarah Jenkins, BSN, RN
Registered Nurse - Emergency Services
Email: sarah.nurse@example.com

Professional Summary:
Compassionate and detail-oriented Registered Nurse with 4 years of clinical acute care experience.
Skilled in triage assessment, medication administration, and electronic health record documentation.

Clinical Skills & Certifications:
• Certifications: Registered Nurse (RN), BLS, ACLS
• Clinical Competencies: Triage Assessment, Patient Care, IV Therapy, Medication Administration, Vital Signs, Wound Care
• Systems & Tools: Epic EHR, Cerner, Pyxis Medication Dispenser, Medical Telemetry Monitors
• Knowledge: HIPAA Compliance, Infection Control Protocols, Patient Education, Clinical Documentation

Work Experience:
Emergency Department Staff Nurse | St. Jude Medical Center (2021 – Present)
• Delivered direct patient care to 25+ acute care patients per shift in a fast-paced Level II Trauma center.
• Administered intravenous medications and blood products adhering to strict safety protocols.
• Documented patient health histories, care interventions, and physician orders in Epic EHR.
"""

NURSE_JD = """
Position: Emergency Room Registered Nurse (RN)
Organization: Metropolitan General Hospital

Requirements & Qualifications:
• Active Registered Nurse (RN) state license.
• 2+ years of acute care or emergency department nursing experience.
• Current BLS and ACLS certifications required; PALS preferred.
• Demonstrated clinical proficiency in Triage Assessment, IV Infusion, and Medication Administration.
• Hands-on proficiency with Electronic Health Records (Epic EHR preferred).
• Understanding of Phlebotomy and Ventilator Management is a plus.
• Strong patient communication, critical thinking, and crisis management abilities.
• Bachelor of Science in Nursing (BSN) or Associate Degree in Nursing.
"""

# -------------------------------------------------------------
# Pair 2: Marketing & Growth (Digital Marketing / SEO)
# -------------------------------------------------------------
MARKETING_RESUME = """
Elena Rostova
Digital Marketing Specialist
Email: elena.marketing@example.com

Professional Summary:
Results-driven digital marketer with 3.5 years of experience managing organic search and inbound growth campaigns.
Proficient in technical SEO, Google Analytics, content strategy, and conversion optimization.

Key Skills & Tools:
• Core Competencies: Search Engine Optimization (SEO), Content Strategy, Inbound Marketing, Copywriting, Email Marketing
• Tools & Platforms: Google Analytics, Google Search Console, HubSpot, WordPress, Canva, Mailchimp, Ahrefs
• Analytics & Concepts: Keyword Research, On-Page Optimization, Conversion Rate Optimization (CRO), A/B Testing

Professional Experience:
Growth Marketing Specialist | Pulse Growth Agency (2022 – Present)
• Executed organic SEO strategy across 15 client accounts, increasing monthly organic traffic by 42%.
• Created targeted email nurturing workflows in HubSpot, achieving a 28% open rate and 4.5% CTR.
• Conducted keyword research and competitor gap audits using Ahrefs and Google Search Console.
"""

MARKETING_JD = """
Job Title: Senior SEO & Growth Marketing Specialist
Company: Omnichannel Consumer Brands

We are seeking a proactive Growth Marketing Specialist to lead search engine optimization and inbound demand generation.

Key Requirements:
• 3+ years of hands-on experience in Search Engine Optimization (SEO) and content marketing.
• Advanced proficiency with Google Analytics (GA4) and Google Search Console.
• Deep expertise in Technical SEO, Keyword Research, and site architecture audits.
• Experience managing marketing automation and lead generation workflows in HubSpot.
• Knowledge of Paid SEM (Google Ads) and Conversion Rate Optimization (CRO) frameworks.
• Strong analytical thinking, campaign ROI tracking, and cross-functional communication.
• Bachelor's degree in Marketing, Business, Communications, or equivalent practical experience.
"""

# -------------------------------------------------------------
# Pair 3: Finance & Accounting (Financial Analyst)
# -------------------------------------------------------------
FINANCE_RESUME = """
David Chen
Senior Financial Analyst
Email: david.finance@example.com

Professional Summary:
Analytical finance professional with 4 years of corporate FP&A and financial modeling experience.
Proven ability to prepare annual operating budgets, build DCF valuation models, and identify cost variances.

Core Competencies & Tools:
• Financial Analysis: Financial Modeling, DCF Valuation, Variance Analysis, Budgeting, Forecasting, Cash Flow Analysis
• Systems & Software: Advanced Excel, Power BI, QuickBooks, NetSuite, Tableau
• Standards: GAAP Compliance, Financial Reporting, P&L Analysis, Scenario Planning

Experience:
Corporate Financial Analyst | Pinnacle Global Media (2021 – Present)
• Developed dynamic 3-statement financial forecast models supporting annual budgeting across 6 operational units.
• Analyzed monthly financial performance and variance against budget, presenting quarterly insights to department heads.
• Automated weekly revenue reporting dashboards in Power BI and Excel, saving 6 hours per week.
"""

FINANCE_JD = """
Role: Corporate Financial Planning & Analysis (FP&A) Manager
Company: Apex Capital Holdings

Requirements & Qualifications:
• 3+ years of progressive corporate finance or FP&A experience.
• Mastery of Financial Modeling, DCF Valuation, and multi-scenario forecasting.
• Proven track record managing Variance Analysis and annual operational Budgeting.
• Deep expertise in Advanced Excel (macros, Power Query) and enterprise ERP systems (SAP or NetSuite).
• Working understanding of GAAP Compliance and corporate financial governance.
• Experience with Capital Budgeting and M&A due diligence is a strong plus.
• Bachelor’s degree in Finance, Accounting, Economics, or related quantitative field; CFA/CPA a plus.
"""

# -------------------------------------------------------------
# Pair 4: Hardware & ECE (Embedded Systems Engineer)
# -------------------------------------------------------------
ECE_RESUME = """
Rahul Sharma
Embedded Systems & Firmware Engineer
Email: rahul.ece@example.com

Technical Skills:
• Languages: Embedded C, C++, Python
• Hardware: STM32, ARM Cortex-M, Microcontrollers, Arduino
• Protocols: I2C, SPI, UART, PWM, ADC
• Tools: Altium Designer, KiCad, STM32CubeIDE, Logic Analyzer, Digital Oscilloscope
• Domains: Embedded Systems, Firmware Architecture, PCB Design, Device Drivers

Experience:
Embedded Engineer | MicroTech Devices (2022 – Present)
• Programmed bare-metal firmware in Embedded C for STM32 microcontrollers.
• Designed 2-layer PCBs using Altium Designer and debugged bus signals using oscilloscopes.
"""

ECE_JD = """
Role: Embedded Systems & Firmware Engineer
Company: Core Hardware Innovations

Requirements:
• 2+ years of experience in Embedded C firmware development for ARM Cortex microcontrollers.
• Hands-on expertise with FreeRTOS, real-time scheduling, and device drivers.
• Proficiency with peripheral protocols including I2C, SPI, UART, and CAN Bus.
• Experience using Altium Designer for schematic capture and PCB layout.
• Familiarity with digital oscilloscopes and logic analyzer testing.
• Bachelor’s degree in Electrical & Electronics Engineering (ECE) or equivalent.
"""


def test_field_1_healthcare_nurse():
    """Validates Healthcare domain: non-engineering role detection, skill extraction, and scoring."""
    entities_res = extract_entities_with_llm(NURSE_RESUME, is_jd=False)
    entities_jd = extract_entities_with_llm(NURSE_JD, is_jd=True)

    # 1. Role Detection
    assert any(w in entities_res.inferred_role.lower() for w in ["nurse", "emergency", "health"])
    assert any(w in entities_jd.inferred_role.lower() for w in ["nurse", "emergency", "health"])

    # 2. Generic Clinical Skill Extraction (no software bias)
    res_skills_lower = [s.lower() for s in entities_res.hard_skills + entities_res.tools_and_tech]
    assert any("triage" in s for s in res_skills_lower)
    assert any("epic" in s for s in res_skills_lower)
    assert any("acls" in s or "bls" in s or "rn" in s for s in res_skills_lower)
    # Ensure no software skills were falsely injected
    assert "javascript" not in res_skills_lower
    assert "python" not in res_skills_lower
    assert "sql" not in res_skills_lower

    # 3. Semantic Alignment Scoring
    score, breakdowns, matches = compute_overall_alignment(entities_res, entities_jd)
    assert score > 60.0

    # 4. Salary Benchmark matching
    salary = compute_salary_insights(role=entities_jd.inferred_role, currency="USD")
    assert salary.role_key == "registered_nurse"
    assert "nurse" in salary.role_title.lower() or "clinical" in salary.role_title.lower()
    assert salary.range.median > 70000


def test_field_2_marketing_growth():
    """Validates Marketing & SEO domain: non-engineering role detection, skill extraction, and scoring."""
    entities_res = extract_entities_with_llm(MARKETING_RESUME, is_jd=False)
    entities_jd = extract_entities_with_llm(MARKETING_JD, is_jd=True)

    # 1. Role Detection
    assert any(w in entities_jd.inferred_role.lower() for w in ["marketing", "seo", "growth"])

    # 2. Generic Marketing Skill Extraction
    res_skills_lower = [s.lower() for s in entities_res.hard_skills + entities_res.tools_and_tech]
    assert any("seo" in s for s in res_skills_lower)
    assert any("google analytics" in s for s in res_skills_lower)
    assert any("hubspot" in s for s in res_skills_lower)
    # Ensure no false software engineering skills
    assert "docker" not in res_skills_lower
    assert "c++" not in res_skills_lower

    # 3. Alignment Scoring
    score, breakdowns, matches = compute_overall_alignment(entities_res, entities_jd)
    assert score > 60.0

    # 4. Salary Benchmark
    salary = compute_salary_insights(role=entities_jd.inferred_role, currency="USD")
    assert salary.role_key == "marketing_specialist"
    assert "marketing" in salary.role_title.lower()


def test_field_3_finance_analyst():
    """Validates Finance & Accounting domain: non-engineering role detection, skill extraction, and scoring."""
    entities_res = extract_entities_with_llm(FINANCE_RESUME, is_jd=False)
    entities_jd = extract_entities_with_llm(FINANCE_JD, is_jd=True)

    # 1. Role Detection
    assert any(w in entities_jd.inferred_role.lower() for w in ["financial", "finance", "fp&a", "analyst"])

    # 2. Finance Skill Extraction
    res_skills_lower = [s.lower() for s in entities_res.hard_skills + entities_res.tools_and_tech]
    assert any("financial modeling" in s for s in res_skills_lower)
    assert any("dcf" in s or "valuation" in s for s in res_skills_lower)
    assert any("excel" in s for s in res_skills_lower)
    assert any("budgeting" in s or "variance" in s for s in res_skills_lower)

    # 3. Alignment Scoring
    score, breakdowns, matches = compute_overall_alignment(entities_res, entities_jd)
    assert score > 60.0

    # 4. Salary Benchmark
    salary = compute_salary_insights(role=entities_jd.inferred_role, currency="INR")
    assert salary.role_key == "financial_analyst"
    assert "financial" in salary.role_title.lower()


def test_field_4_hardware_ece_preservation():
    """Validates that hardware and ECE engineering capabilities remain fully functional."""
    entities_res = extract_entities_with_llm(ECE_RESUME, is_jd=False)
    entities_jd = extract_entities_with_llm(ECE_JD, is_jd=True)

    # 1. Role Detection
    assert any(w in entities_jd.inferred_role.lower() for w in ["embedded", "firmware", "hardware", "electrical"])

    # 2. ECE Skill Extraction
    res_skills_lower = [s.lower() for s in entities_res.hard_skills + entities_res.tools_and_tech]
    assert any("embedded c" in s for s in res_skills_lower)
    assert any("stm32" in s or "arm" in s for s in res_skills_lower)
    assert any("altium" in s for s in res_skills_lower)

    # 3. Alignment Scoring
    score, breakdowns, matches = compute_overall_alignment(entities_res, entities_jd)
    assert score > 60.0

    # 4. Salary Benchmark
    salary = compute_salary_insights(role=entities_jd.inferred_role, currency="USD")
    assert salary.role_key in ["embedded_systems_engineer", "electrical_engineer", "hardware_engineer"]


def test_api_analyze_universal_nursing():
    """Integration test: API POST /api/analyze with a nursing resume and JD."""
    files = {
        "resume_file": ("sarah_nurse.txt", NURSE_RESUME.encode("utf-8"), "text/plain")
    }
    data = {
        "jd_text": NURSE_JD,
        "company_type": "mid_size_product"
    }

    response = client.post("/api/analyze", files=files, data=data)
    assert response.status_code == 200
    res = response.json()

    assert res["overall_score"] > 50.0
    assert any(w in res["inferred_role"].lower() for w in ["nurse", "emergency", "health", "specialist"])
    # Check that rejection reasons do not use tech jargon like 'software', 'production code', 'github'
    for r in res["rejection_reasons"]:
        assert "git repository" not in r["actionable_fix"].lower()
        assert "ci/cd" not in r["reason"].lower()
