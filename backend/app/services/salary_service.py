"""
Salary Insights and Career Growth Estimation Service for SkillBridge.
Maps candidate role and experience to market compensation benchmarks (USD and INR)
across Electrical & Electronics (ECE), Embedded Systems, VLSI, Robotics, Mechanical,
Software, Cloud, Data Science, and Product Management.
Includes automatic role inference from JD/Resume and returns all available market roles.
"""

import json
import re
from pathlib import Path
from typing import Dict, Any, List, Optional
from app.models.schemas import (
    SalaryResponse,
    SalaryRange,
    SalaryGrowthItem,
    HighImpactSkill,
)

# Path to static benchmark JSON dataset
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
SALARY_FILE = DATA_DIR / "salary_data.json"

def _contains_word(text: str, keywords: List[str]) -> bool:
    """Checks whether any keyword exists as a whole standalone word (not a substring)."""
    for kw in keywords:
        pattern = r'\b' + re.escape(kw.lower()) + r'\b'
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False

def load_salary_data() -> Dict[str, Any]:
    """
    Loads salary benchmark dataset from salary_data.json.
    """
    if SALARY_FILE.exists():
        with open(SALARY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    return {"roles": {}}

def match_role_key(query_role: str) -> str:
    """
    Normalizes any freeform job title or resume role string into a known benchmark role key.
    Supports Healthcare, Finance, Marketing, Sales, HR, Operations, Design, Education,
    Legal, ECE, Hardware, Robotics, Mechanical, Software, and Cloud.
    """
    raw_clean = query_role.lower().strip()

    # 0. Direct match against known role keys in dataset
    data = load_salary_data()
    roles = data.get("roles", {})
    if raw_clean in roles:
        return raw_clean

    clean_role = raw_clean.replace("_", " ")
    if clean_role in roles:
        return clean_role

    # 1. Healthcare & Medicine
    if _contains_word(clean_role, ["nurse", "nursing", "icu", "clinical", "patient care", "hospital", "triage"]):
        return "registered_nurse"

    # 2. Finance & Banking
    if _contains_word(clean_role, ["financial analyst", "financial modeling", "investment", "portfolio", "finance"]):
        return "financial_analyst"

    # 3. Accounting & Tax
    if _contains_word(clean_role, ["accountant", "accounting", "cpa", "audit", "tax", "bookkeeper"]):
        return "accountant"

    # 4. Marketing, Content & SEO
    if _contains_word(clean_role, ["marketing", "seo", "content strategist", "social media", "brand manager", "growth marketer"]):
        return "marketing_specialist"

    # 5. Sales & Business Development
    if _contains_word(clean_role, ["sales", "account executive", "business development", "bdr", "sdr"]):
        return "sales_executive"

    # 6. Human Resources & People
    if _contains_word(clean_role, ["human resources", "talent acquisition", "hr generalist", "recruiter", "people ops", "hr"]):
        return "hr_specialist"

    # 7. Operations & Project Management
    if _contains_word(clean_role, ["operations", "supply chain", "logistics", "procurement"]):
        return "operations_manager"
    if _contains_word(clean_role, ["product manager", "project manager", "scrum master", "program manager"]):
        return "product_manager"

    # 8. Design & Creative
    if _contains_word(clean_role, ["designer", "graphic", "ui/ux", "product designer", "visual designer"]):
        return "graphic_designer"

    # 9. Education & Teaching
    if _contains_word(clean_role, ["teacher", "educator", "instructor", "instructional designer", "professor"]):
        return "teacher_educator"

    # 10. Legal & Compliance
    if _contains_word(clean_role, ["legal", "counsel", "attorney", "paralegal", "compliance"]):
        return "legal_counsel"

    # 11. VLSI & Semiconductors
    if _contains_word(clean_role, ["vlsi", "asic", "fpga", "verilog", "vhdl", "systemverilog", "rtl", "semiconductor"]):
        return "vlsi_design_engineer"

    # 12. Embedded Systems & Firmware
    if _contains_word(clean_role, ["embedded", "firmware", "microcontroller", "arm cortex", "stm32", "rtos", "freertos", "device driver"]):
        return "embedded_systems_engineer"

    # 13. Hardware & PCB Design
    if _contains_word(clean_role, ["pcb", "hardware", "altium", "kicad", "schematic", "signal integrity"]):
        return "hardware_engineer"

    # 14. RF & Wireless / Telecommunications
    if _contains_word(clean_role, ["rf", "telecom", "telecommunication", "antenna", "wireless", "microwave", "5g", "cellular"]):
        return "rf_telecom_engineer"

    # 15. Robotics & Automation
    if _contains_word(clean_role, ["robotics", "automation", "ros", "ros2", "plc", "scada", "mechatronics", "control systems"]):
        return "robotics_automation_engineer"

    # 16. Electrical & Electronics (ECE / EEE)
    if _contains_word(clean_role, ["electrical", "electronics", "ece", "eee", "circuit", "power electronics", "instrumentation", "analog", "dsp", "signal processing"]):
        return "electrical_engineer"

    # 17. Mechanical & CAD Engineering (uses word boundaries so 'cad' does not match 'academic')
    if _contains_word(clean_role, ["mechanical", "cad", "solidworks", "catia", "ansys", "fea", "cfd", "thermal", "automotive"]):
        return "mechanical_engineer"

    # 18. Cloud & DevOps
    if _contains_word(clean_role, ["devops", "cloud", "aws", "azure", "gcp", "kubernetes", "sre", "infrastructure", "terraform"]):
        return "cloud_devops_engineer"

    # 19. Data Science & AI
    if _contains_word(clean_role, ["data", "ai", "machine learning", "deep learning", "nlp", "computer vision", "analytics"]):
        return "data_scientist"

    # 20. Mobile & App Engineering
    if _contains_word(clean_role, ["mobile", "react native", "flutter", "ios", "android"]):
        return "frontend_engineer"

    # 21. Software & Web Engineering
    if _contains_word(clean_role, ["backend", "api", "database", "sql", "fastapi", "django", "spring boot"]):
        return "backend_engineer"
    if _contains_word(clean_role, ["frontend", "ui", "react", "vue", "angular", "css", "web"]):
        return "frontend_engineer"
    if _contains_word(clean_role, ["software", "full stack", "developer", "programmer", "coding"]):
        return "software_engineer"

    return "default"

def infer_role_from_text(resume_text: str, jd_text: str) -> str:
    """
    Automatically infers the target or candidate job role from the uploaded documents.
    Gives primary weight to the target Job Description header, with fallback to resume.
    """
    # 1. Check for explicit role heading in JD
    top_jd = jd_text[:800]
    explicit = re.search(r'(?:role|job title|position|title)\s*:\s*([^\n\r,;|]+)', top_jd, re.IGNORECASE)
    if explicit:
        matched_str = explicit.group(1).strip()
        matched_key = match_role_key(matched_str)
        if matched_key != "default":
            return matched_key

    combined = (jd_text[:1200] + " " + resume_text[:1200]).lower()

    # 2. Healthcare & Nursing
    if _contains_word(combined, ["nurse", "nursing", "icu", "clinical", "patient care", "hospital"]):
        return "registered_nurse"

    # 3. Finance & Accounting
    if _contains_word(combined, ["financial analyst", "financial modeling", "investment", "valuation"]):
        return "financial_analyst"
    if _contains_word(combined, ["accountant", "accounting", "cpa", "tax compliance", "audit"]):
        return "accountant"

    # 4. Marketing & Sales
    if _contains_word(combined, ["marketing", "seo", "content strategist", "growth marketer"]):
        return "marketing_specialist"
    if _contains_word(combined, ["account executive", "sales executive", "sales representative"]):
        return "sales_executive"

    # 5. Human Resources & Operations
    if _contains_word(combined, ["human resources", "talent acquisition", "hr generalist", "recruiter"]):
        return "hr_specialist"
    if _contains_word(combined, ["operations manager", "supply chain", "logistics"]):
        return "operations_manager"
    if _contains_word(combined, ["product manager", "scrum master"]):
        return "product_manager"

    # 6. Design & Education
    if _contains_word(combined, ["graphic designer", "ui/ux", "product designer"]):
        return "graphic_designer"
    if _contains_word(combined, ["teacher", "educator", "instructional designer"]):
        return "teacher_educator"
    if _contains_word(combined, ["legal counsel", "paralegal", "compliance"]):
        return "legal_counsel"

    # 7. Hardware, ECE & Robotics
    if _contains_word(combined, ["vlsi", "asic", "fpga", "verilog", "vhdl"]):
        return "vlsi_design_engineer"
    elif _contains_word(combined, ["embedded", "firmware", "microcontroller", "arm cortex", "stm32", "rtos"]):
        return "embedded_systems_engineer"
    elif _contains_word(combined, ["pcb", "altium", "schematic", "hardware design"]):
        return "hardware_engineer"
    elif _contains_word(combined, ["robotics", "ros", "ros2", "automation", "plc"]):
        return "robotics_automation_engineer"
    elif _contains_word(combined, ["rf", "telecom", "antenna", "wireless"]):
        return "rf_telecom_engineer"
    elif _contains_word(combined, ["electronics", "ece", "electrical", "eee", "circuit"]):
        return "electrical_engineer"
    elif _contains_word(combined, ["mechanical", "solidworks", "cad", "ansys"]):
        return "mechanical_engineer"

    # 8. Mobile & App Development
    elif _contains_word(combined, ["react native", "flutter", "ios developer", "android developer", "mobile developer"]):
        return "frontend_engineer"

    # 9. Software & Data
    elif _contains_word(combined, ["data scientist", "machine learning", "ai engineer"]):
        return "data_scientist"
    elif _contains_word(combined, ["devops", "cloud engineer", "sre"]):
        return "cloud_devops_engineer"
    elif _contains_word(combined, ["frontend", "react"]):
        return "frontend_engineer"
    elif _contains_word(combined, ["backend"]):
        return "backend_engineer"
    elif _contains_word(combined, ["software engineer", "developer", "full stack"]):
        return "software_engineer"

    return "default"

def compute_salary_insights(
    role: str = "electrical_engineer",
    currency: str = "USD",
    years_exp: float = 3.0,
    skills_acquired: List[str] = None
) -> SalaryResponse:
    """
    Computes indicative salary ranges, growth projections, and skill premiums.
    Returns all available market roles so the user can easily explore any role.
    """
    data = load_salary_data()
    roles = data.get("roles", {})

    role_key = match_role_key(role)
    role_info = roles.get(role_key, roles.get("default", roles.get("electrical_engineer")))

    curr_key = "inr" if currency.upper() == "INR" else "usd"
    base_range = role_info.get(curr_key, { "min": 78000, "median": 108000, "max": 155000 })

    # Experience tier multiplier
    if years_exp < 2.0:
        tier_mult = 0.8
    elif years_exp <= 4.5:
        tier_mult = 1.0
    elif years_exp <= 8.0:
        tier_mult = 1.45
    else:
        tier_mult = 1.8

    # Apply experience tier adjustment
    calc_min = round(base_range["min"] * tier_mult)
    calc_med = round(base_range["median"] * tier_mult)
    calc_max = round(base_range["max"] * tier_mult)

    # Format 1, 3, 5 year growth projections
    growth_data: List[SalaryGrowthItem] = []
    for item in role_info.get("growth_projection", []):
        year_name = item.get("year", "Year")
        scaled_usd = round(item.get("usd", 108000) * (tier_mult / 1.0))
        scaled_inr = round(item.get("inr", 1250000) * (tier_mult / 1.0))
        growth_data.append(
            SalaryGrowthItem(
                year=year_name,
                usd=scaled_usd,
                inr=scaled_inr
            )
        )

    # High impact skill premiums
    high_impact: List[HighImpactSkill] = [
        HighImpactSkill(**h) for h in role_info.get("high_impact_skills", [])
    ]

    # Package list of all available roles for the frontend catalog
    all_roles_list = []
    for k, v in roles.items():
        if k != "default":
            all_roles_list.append({
                "id": k,
                "title": v.get("title", k.replace("_", " ").title()),
                "category": v.get("category", "General Engineering")
            })

    # Resolve human-friendly title
    display_title = role_info.get("title", "Professional Specialist")
    if role_key == "default" and role and role.lower() not in ["default", "general_professional", "software_engineer", "electrical_engineer"]:
        display_title = role.replace("_", " ").title()

    return SalaryResponse(
        role_key=role_key,
        role_title=display_title,
        category=role_info.get("category", "Professional Practice"),
        currency=currency.upper(),
        range=SalaryRange(
            min=calc_min,
            median=calc_med,
            max=calc_max
        ),
        growth_projection=growth_data,
        high_impact_skills=high_impact,
        all_available_roles=all_roles_list,
        disclaimer=(
            "Indicative estimate based on market compensation benchmarks and skill premiums across professional disciplines. "
            "Figures are not compensation guarantees. Actual offers depend on candidate interview performance, "
            "employer tier/funding, equity or benefits incentives, and location."
        )
    )
