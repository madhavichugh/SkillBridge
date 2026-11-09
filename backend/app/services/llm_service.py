"""
LLM Service module for SkillBridge.
Uses Google's official GenAI SDK (Gemini) for structured entity extraction,
recruiter-perspective rejection explanations, and quantified resume bullet rewrites.
Supports ALL engineering, technology, and business disciplines (ECE, Embedded,
VLSI, Mechanical, Robotics, Software, Data Science, Product, etc.).
Includes:
- Section-aware dynamic text parser extracting exact terms from the document
- Multi-domain technical catalog
- In-memory SHA-256 caching and exponential backoff
- Automatic role inference
"""

import json
import re
import hashlib
import time
from typing import Dict, Any, Optional, List, Tuple
from google import genai
from google.genai import types

from app.config import settings
from app.models.schemas import ExtractedEntities

# In-memory cache to prevent redundant LLM API calls and save tokens
_LLM_CACHE: Dict[str, Any] = {}

def get_hash(text: str) -> str:
    """Computes a SHA-256 hash string for caching."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def get_gemini_client() -> Optional[genai.Client]:
    """
    Returns an initialized Gemini client if an API key is configured.
    Returns None if no API key is provided, signaling fallback mode.
    """
    api_key = settings.gemini_api_key.strip()
    if not api_key or api_key.startswith("your_"):
        return None
    try:
        return genai.Client(api_key=api_key)
    except Exception as e:
        print(f"[SkillBridge] Warning: Failed to initialize Gemini client: {e}")
        return None

# -------------------------------------------------------------
# 1. Multi-Disciplinary Skills & Domain Catalog
# -------------------------------------------------------------

# Broad universal catalog covering Healthcare, Finance, Marketing, HR, Operations, Design, Education, Engineering & Tech
KNOWN_HARD_SKILLS = [
    # Healthcare & Clinical
    "Patient Care", "Clinical Assessment", "Electronic Health Records", "EHR", "EMR", "Epic", "Cerner",
    "Triage", "BLS", "ACLS", "PALS", "Medication Administration", "Phlebotomy", "Infection Control",
    "Vital Signs", "Wound Care", "HIPAA", "CPR", "Patient Education", "Clinical Documentation",

    # Business, Finance & Accounting
    "Financial Modeling", "Financial Analysis", "Accounting", "GAAP", "IFRS", "Budgeting", "Forecasting",
    "Auditing", "Tax Compliance", "Variance Analysis", "Cash Flow Management", "Risk Management",
    "QuickBooks", "SAP", "NetSuite", "Excel", "Financial Reporting", "P&L Management",

    # Marketing, Sales & Growth
    "SEO", "Search Engine Optimization", "SEM", "Google Analytics", "Content Marketing", "Content Strategy",
    "Social Media Marketing", "Email Marketing", "Copywriting", "HubSpot", "Marketo", "Lead Generation",
    "CRM", "Salesforce", "B2B Sales", "Client Relationship Management", "Conversion Rate Optimization", "CRO",
    "Market Research", "Digital Marketing", "Brand Strategy", "Campaign Management",

    # Human Resources & People
    "Talent Acquisition", "Employee Relations", "Onboarding", "Performance Management", "HRIS", "Workday",
    "Recruiting", "Sourcing", "Compensation & Benefits", "Labor Law Compliance", "SHRM", "HR Analytics",

    # Operations, Project Management & Supply Chain
    "Project Management", "PMP", "Scrum Master", "Agile Methodologies", "Kanban", "Lean Six Sigma",
    "Six Sigma", "Supply Chain Management", "Logistics", "Inventory Management", "Vendor Management",
    "Process Improvement", "Procurement", "Quality Assurance", "Operations Management",

    # Creative & Design
    "Graphic Design", "UI/UX Design", "Figma", "Adobe Photoshop", "Adobe Illustrator", "InDesign",
    "Wireframing", "Prototyping", "User Research", "Visual Design", "Typography",

    # Education & Training
    "Curriculum Development", "Instructional Design", "Classroom Management", "Lesson Planning",
    "Student Assessment", "Differentiated Instruction", "Educational Technology", "LMS", "E-Learning",

    # Electronics, ECE & Hardware
    "Verilog", "SystemVerilog", "VHDL", "FPGA", "VLSI", "ASIC", "Embedded C", "Embedded C++",
    "Microcontrollers", "8051", "ARM", "ARM Cortex", "ARM Cortex-M", "STM32", "Arduino", "Raspberry Pi",
    "PCB Design", "Altium", "Altium Designer", "KiCAD", "Eagle", "OrCAD", "Circuit Design",
    "Analog Circuits", "Digital Circuits", "Power Electronics", "Digital Signal Processing", "DSP",
    "Signal Processing", "MATLAB", "Simulink", "I2C", "SPI", "UART", "CAN Bus", "CAN", "RS-232", "RS-485",
    "BLE", "Bluetooth", "Zigbee", "LoRa", "RF Engineering", "Antenna Design", "SPICE", "LTSpice", "PSpice",
    "Keil", "Keil uVision", "Proteus", "Oscilloscope", "Logic Analyzer", "Multimeter", "Function Generator",
    "PLC", "SCADA", "Control Systems", "RTOS", "FreeRTOS", "Embedded Linux", "Firmware", "Sensors",
    "Sensors & Actuators", "Semiconductor Devices", "Microprocessors", "Wireless Communication",

    # Core Engineering & Mechanical
    "SolidWorks", "AutoCAD", "CATIA", "Creo", "ANSYS", "FEA", "CFD", "CAD/CAM", "Robotics",
    "ROS", "ROS2", "Mechatronics", "GD&T", "3D Printing", "CNC", "Thermal Analysis", "Hydraulics",

    # Data Science, AI & Analytics
    "Python", "R", "SQL", "Machine Learning", "Deep Learning", "Computer Vision", "NLP",
    "PyTorch", "TensorFlow", "Scikit-Learn", "OpenCV", "Pandas", "NumPy", "Data Analysis",
    "Statistics", "Power BI", "Tableau",

    # Software & Systems
    "C", "C++", "Java", "JavaScript", "TypeScript", "Go", "Rust", "C#", "Linux", "Bash",
    "REST API", "Microservices", "System Design", "Git", "GitHub", "Docker", "Kubernetes",
    "AWS", "Azure", "GCP", "CI/CD", "PostgreSQL", "MySQL", "MongoDB", "Redis", "Unit Testing",
    "React Native", "Flutter", "Mobile App Development", "Redux", "Firebase", "Expo", "Context API",
    "Push Notifications", "React Navigation"
]

KNOWN_SOFT_SKILLS = [
    "Communication", "Stakeholder Management", "Leadership", "Team Collaboration",
    "Problem Solving", "Analytical Thinking", "Critical Thinking", "Adaptability",
    "Project Planning", "Time Management", "Conflict Resolution", "Negotiation",
    "Active Listening", "Client Relationship Building", "Cross-Functional Collaboration",
    "Organization & Prioritization", "Troubleshooting", "Attention to Detail"
]

KNOWN_TOOLS = [
    # Business, Office & Management Tools
    "Excel", "Google Sheets", "PowerPoint", "Microsoft Office", "Tableau", "Power BI",
    "Salesforce", "HubSpot", "Jira", "Asana", "Trello", "Monday.com", "Notion", "Slack",
    "QuickBooks", "SAP", "NetSuite", "Workday", "Epic", "Cerner", "Canva", "Figma",

    # ECE & Hardware EDA tools
    "Altium Designer", "Altium", "KiCAD", "Eagle", "Keil", "Keil uVision", "Xilinx Vivado",
    "Quartus Prime", "MATLAB", "Simulink", "LTSpice", "PSpice", "Proteus", "LabVIEW",
    "Oscilloscope", "Logic Analyzer", "Multimeter", "Spectrum Analyzer", "STM32CubeIDE",

    # Engineering, Mobile & Tech Tools
    "SolidWorks", "AutoCAD", "CATIA", "ANSYS",
    "Git", "GitHub", "GitLab", "Linux", "VS Code", "Docker", "Postman",
    "Firebase", "Expo", "Android Studio", "Xcode"
]

KNOWN_DOMAINS = [
    # Healthcare & Life Sciences
    "Healthcare & Patient Care", "Clinical Research", "Nursing & Acute Care", "Public Health",

    # Business, Finance & Sales
    "Finance & Accounting", "Investment & Banking", "Digital Marketing & Growth",
    "Sales & Business Development", "Human Resources & Talent", "Operations & Supply Chain",

    # Engineering & Technology
    "Embedded Systems", "Electronics & Communication", "VLSI & Semiconductors", "Hardware Engineering",
    "Robotics & Automation", "Mechanical Engineering", "Software Engineering", "Cloud Computing",
    "Artificial Intelligence", "Data Engineering", "Education & Training", "Legal & Compliance"
]

# Patterns identifying bullet boilerplate prefixes to strip before token splitting
BULLET_PREFIX_PATTERNS = [
    r'^[•\*\-\d\.\s]+',  # Bullets, dashes, numbers: '• ', '1. ', '- '
    r'^[A-Za-z0-9\s&/+\-]{2,30}:\s*',  # Category labels: 'Languages:', 'Frameworks:'
    r'^(?:\d+\+?|\d+\s*-\s*\d+)\s*(?:years?|yrs?)(?:\s+of)?\s+(?:professional\s+)?(?:hands-on\s+)?(?:work\s+)?experience\s+(?:in|with|using|of)?\s*',
    r'^(?:hands-on\s+)?experience\s+(?:with|in|using|of)\s+',
    r'^(?:proven\s+)?(?:working\s+)?knowledge\s+(?:with|in|using|of)\s+',
    r'^(?:strong\s+)?proficiency\s+(?:with|in|using|of)\s+',
    r'^(?:strong\s+)?familiarity\s+(?:with|in|using|of)\s+',
    r'^(?:deep\s+)?understanding\s+(?:with|in|using|of)\s+',
    r'^(?:strong\s+)?programming\s+skills?\s+(?:with|in|using|of)\s+',
    r'^(?:solid\s+|strong\s+)?background\s+(?:with|in|using|of)\s+',
    r'^(?:internship\s+or\s+academic\s+projects\s+using|academic\s+projects\s+using|projects\s+using)\s+',
    r'^(?:demonstrated\s+)?ability\s+to\s+(?:work\s+with|use|develop|build|design)?\s*',
    r'^(?:skilled\s+in|exposure\s+to|proficient\s+in|experienced\s+in)\s+',
    r'^(?:responsible\s+for|expertise\s+in|competency\s+in)\s+',
]

# Patterns that classify an entire bullet as education (NOT skills)
DEGREE_PATTERNS = [
    r'\b(?:bachelor|master|doctor|ph\.?d|b\.?s\.?c?|m\.?s\.?c?|m\.?a|b\.?a|m\.?b\.?a|associate|diploma|b\.?tech|b\.?e|degree)\b',
    r'\b(?:graduate|undergraduate|postgraduate)\b',
    r'\bmajor\s+in\b',
    r'\bequivalent\s+degree\b',
    r'\baccredited\s+program\b'
]

# Blacklisted tokens and fragments that should NEVER be emitted as standalone skills
TOKEN_BLACKLIST = {
    'or a related field', 'related field', 'and experience', 'equivalent experience',
    'years of experience', 'or equivalent', 'preferred qualifications', 'minimum qualifications',
    'basic qualifications', 'requirements', 'what we offer', 'responsibilities',
    'duties', 'plus', 'strong plus', 'nice to have', 'bonus', 'ability', 'willingness',
    'candidate', 'team player', 'fast learner', 'self starter', 'good understanding',
    'strong background', 'qualification', 'qualifications', 'degree', 'internship',
    'experience', 'technologies', 'tools', 'skills', 'what we offer',
    'based on', 'based on experience', 'depending on', 'depending on experience',
    'as per industry standards', 'negotiable', 'market standard', 'best in industry',
    'salary', 'compensation', 'stipend', 'remuneration', 'ctc', 'lpa',
    'full time', 'part time', 'contract', 'remote', 'hybrid', 'on-site', 'onsite',
    'notice period', 'immediate joiner'
}

SKILL_SECTION_HEADERS = [
    r'technical\s+skills', r'core\s+skills', r'key\s+skills', r'skills\s*&\s*competencies',
    r'skills\s*&\s*abilities', r'skills', r'technologies', r'tools\s*&\s*technologies',
    r'tools\s*&\s*platforms', r'tools', r'platforms', r'core\s+competencies',
    r'competencies', r'areas\s+of\s+expertise', r'clinical\s+skills', r'professional\s+skills',
    r'specialized\s+skills', r'domain\s+knowledge', r'hardware\s*&\s*software',
    r'languages\s*&\s*frameworks', r'frameworks\s*&\s*libraries', r'frameworks',
    r'libraries', r'protocols', r'eda\s*&\s*tools', r'eda', r'testing',
    r'certifications\s*&\s*licenses', r'certifications', r'licenses', r'credentials',
    r'requirements\s*&\s*qualifications', r'required\s*qualifications',
    r'preferred\s*qualifications', r'minimum\s*qualifications', r'basic\s*qualifications',
    r'qualifications', r'requirements', r'job\s+requirements', r'what\s+you[\'\’]?ll\s+need',
    r'what\s+you\s+bring', r'what\s+we[\'\’]?re\s+looking\s+for'
]

NON_SKILL_SECTION_HEADERS = [
    r'experience', r'work\s+experience', r'professional\s+experience',
    r'employment\s+history', r'education', r'academic\s+background',
    r'what\s+we\s+offer', r'benefits', r'perks', r'compensation',
    r'salary', r'ctc', r'package', r'remuneration', r'stipend', r'pay\s+scale',
    r'about\s+us', r'about\s+the\s+company', r'about\s+the\s+role',
    r'who\s+we\s+are', r'equal\s+opportunity', r'how\s+to\s+apply',
    r'responsibilities', r'key\s+responsibilities', r'duties',
    r'summary', r'professional\s+summary', r'profile', r'objective'
]

def contains_word(text: str, keywords: List[str]) -> bool:
    """Checks whether any keyword exists as a whole standalone word (not a substring)."""
    for kw in keywords:
        pattern = r'\b' + re.escape(kw.lower()) + r'\b'
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False

def is_education_line(line: str) -> bool:
    """Returns True if the line states an education requirement (degree, diploma, etc.)."""
    lower = line.lower()
    return any(re.search(p, lower) for p in DEGREE_PATTERNS)

def is_salary_or_compensation_line(line: str) -> bool:
    """Returns True if the line specifies compensation, salary, CTC, LPA, stipend, or perks."""
    if any(sym in line for sym in ['₹', '$', '€', '£']):
        return True
    lower = line.lower()
    return any(re.search(p, lower) for p in [
        r'\b(?:lpa|ctc|per\s+annum|p\.a\.|per\s+month|p\.m\.|hourly|per\s+hour)\b',
        r'\b(?:salary|stipend|compensation|remuneration|package|pay\s+range)\b',
        r'\b\d+\s*-\s*\d+\s*(?:lpa|ctc|lac|lakh|k)\b',
        r'\b\d+\s*(?:lpa|ctc|lac|lakh|lakhs)\b',
        r'\b(?:based\s+on\s+experience|based\s+on|as\s+per\s+industry|market\s+standards?|negotiable)\b'
    ])

def strip_bullet_prefixes(line: str) -> str:
    """Strips bullet symbols, category headers, and common introductory boilerplate phrases."""
    cleaned = line.strip()
    changed = True
    while changed:
        changed = False
        for p in BULLET_PREFIX_PATTERNS:
            subbed = re.sub(p, '', cleaned, flags=re.IGNORECASE).strip()
            if subbed != cleaned:
                cleaned = subbed
                changed = True
    return cleaned

def clean_token(token: str) -> str:
    """Cleans edge punctuation, leading conjunctions, and trailing noise qualifiers."""
    t = token.strip(" \t\n\r.•*-:;,()[]{}\"'|\\/")
    if not t or is_salary_or_compensation_line(t):
        return ""
    strip_lead = r'^(?:and|or|with|in|of|using|such as|including|modern|advanced|strong|hands-on|solid|basic|practical|good|deep|in-depth|thorough|working|knowledge\s+of|understanding\s+of|proficiency\s+in|familiarity\s+with|experience\s+in|experience\s+with)\s+'
    changed = True
    while changed:
        changed = False
        new_t = re.sub(strip_lead, '', t, flags=re.IGNORECASE).strip(" \t\n\r.•*-:;,()[]{}\"'|\\/")
        if new_t != t:
            t = new_t
            changed = True
    # Strip trailing purpose clauses & qualifiers like 'for version control'
    t = re.sub(r'\s+for\s+(?:version\s+control|state\s+management|styling|testing|debugging|deployment|automation|development|mobile|web)$', '', t, flags=re.IGNORECASE)
    t = re.sub(r'\s+(?:is a strong plus|is a plus|is preferred|preferred|required|skills?|abilities|knowledge)$', '', t, flags=re.IGNORECASE)
    t = t.strip(" \t\n\r.•*-:;,()[]{}\"'|\\/")
    return t

def parse_bullet_to_skills(bullet: str) -> List[str]:
    """Parses a single bullet point into individual, high-quality skill names."""
    if is_education_line(bullet) or is_salary_or_compensation_line(bullet):
        return []
    line = strip_bullet_prefixes(bullet)
    unwrapped = re.sub(r'[\(\)\[\]\{\}]', ', ', line)
    tokens = re.split(r'[,;/|]|\b(?:and|or)\b', unwrapped)
    results = []
    for tok in tokens:
        c = clean_token(tok)
        if not c:
            continue
        lower_c = c.lower()
        if lower_c in TOKEN_BLACKLIST:
            continue
        if any(b in lower_c for b in ['related field', 'equivalent experience', 'years of experience', 'based on', 'depending on']):
            continue
        if len(c) < 2 or len(c) > 35:
            continue
        if not re.search(r'[a-zA-Z]', c):
            continue
        if c.islower():
            c = c.title()
        if c not in results:
            results.append(c)
    return results

def extract_skills_and_education_from_sections(text: str) -> Tuple[List[str], List[str]]:
    """
    Intelligently parses document text line-by-line:
    - Tracks skill/qualification sections and exits at non-skill sections (e.g. What We Offer, Salary).
    - Routes academic degree requirements to education (never hard skills).
    - Filters out compensation/salary numbers and dangling clauses (e.g. ₹4 LPA - ₹8 LPA, Based on).
    - Strips introductory boilerplate and splits multi-skill lists cleanly.
    """
    extracted_skills: List[str] = []
    extracted_education: List[str] = []

    lines = text.split("\n")
    in_skill_section = False

    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue

        # Skip salary or compensation lines completely
        if is_salary_or_compensation_line(line):
            continue

        clean_header = line.lower().strip(":•*- \t")
        is_bullet = bool(re.match(r'^[•\*\-\d]', line))

        # Check if line marks a non-skill section (only non-bullet lines)
        if not is_bullet:
            for p in NON_SKILL_SECTION_HEADERS:
                if re.match(r'^(?:' + p + r')(?:\s*:|\s*$)', clean_header):
                    in_skill_section = False
                    break

        # Check if line marks a skill section (only non-bullet lines)
        is_skill_header = False
        if not is_bullet:
            for p in SKILL_SECTION_HEADERS:
                if re.search(r'\b' + p + r'\b', clean_header):
                    is_skill_header = True
                    in_skill_section = True
                    colon_idx = line.find(":")
                    if colon_idx != -1 and colon_idx < len(line) - 1:
                        rest = line[colon_idx + 1:].strip()
                        if rest:
                            if is_education_line(rest):
                                extracted_education.append(rest)
                            elif not is_salary_or_compensation_line(rest):
                                for sk in parse_bullet_to_skills(rest):
                                    if sk not in extracted_skills:
                                        extracted_skills.append(sk)
                    break

        if is_skill_header:
            continue

        # If inside a skill section, process line
        if in_skill_section:
            if is_education_line(line):
                edu_clean = re.sub(r'^[•\*\-\d\.\s]+', '', line).strip()
                if edu_clean and edu_clean not in extracted_education:
                    extracted_education.append(edu_clean)
            elif not is_salary_or_compensation_line(line):
                for sk in parse_bullet_to_skills(line):
                    if sk not in extracted_skills:
                        extracted_skills.append(sk)
        else:
            # If not in an explicit skill section, check if this line is a bullet with skill prefix or category
            if re.match(r'^[•\*\-]\s*(?:[A-Za-z\s&/]{2,25}:\s*|experience\s+with|knowledge\s+of|proficiency\s+in|familiarity\s+with|hands-on\s+experience|internship|strong\s+programming|\d+\+?\s*years)', line, re.IGNORECASE):
                if is_education_line(line):
                    edu_clean = re.sub(r'^[•\*\-\d\.\s]+', '', line).strip()
                    if edu_clean and edu_clean not in extracted_education:
                        extracted_education.append(edu_clean)
                elif not is_salary_or_compensation_line(line):
                    for sk in parse_bullet_to_skills(line):
                        if sk not in extracted_skills:
                            extracted_skills.append(sk)

    return extracted_skills, extracted_education

    return extracted_skills, extracted_education

def extract_skills_from_text_sections(text: str) -> List[str]:
    """
    Dynamically scans document text for skill headings and extracts clean, genuine skills.
    Preserves exact function signature for callers.
    """
    skills, _ = extract_skills_and_education_from_sections(text)
    return skills

def infer_document_role(text: str) -> str:
    """
    Infers the target or candidate professional role from document content using word boundaries.
    Works for ANY industry across corporate, medical, creative, educational, and technical fields.
    """
    # 1. Look for explicit role headers in the top portion of the document
    top_chunk = text[:1000]
    explicit_match = re.search(
        r'(?:role|job title|position|title)\s*:\s*([^\n\r,;|]+)',
        top_chunk,
        re.IGNORECASE
    )
    if explicit_match:
        role_candidate = explicit_match.group(1).strip().strip("-•* \t")
        if 2 < len(role_candidate) < 50:
            return role_candidate.title()

    # 2. Check the top 4 non-empty lines (often candidate header or JD title)
    lines = [line.strip().strip("-•* \t") for line in top_chunk.split("\n") if line.strip()]
    for line in lines[:4]:
        line_clean = re.sub(r'[^a-zA-Z\s/&-]', '', line).strip()
        lower_line = line_clean.lower()
        if any(w in lower_line for w in ["nurse", "analyst", "manager", "specialist", "coordinator", "engineer", "developer", "accountant", "director", "consultant", "designer", "teacher", "executive", "strategist", "officer", "administrator"]):
            if 3 < len(line_clean) < 45 and not any(w in lower_line for w in ["resume", "curriculum", "email", "phone", "street", "city", "summary"]):
                return line_clean.title()

    # 3. Healthcare & Clinical
    if contains_word(text, ["registered nurse", "nurse", "nursing", "icu", "patient care", "clinic", "hospital", "triage", "physician"]):
        return "Registered Nurse / Healthcare Specialist"

    # 4. Marketing, Sales & Growth
    if contains_word(text, ["marketing manager", "seo specialist", "digital marketing", "content strategist", "social media manager"]):
        return "Digital Marketing Specialist"
    if contains_word(text, ["account executive", "sales executive", "sales manager", "business development"]):
        return "Sales & Business Development Representative"

    # 5. Finance & Accounting
    if contains_word(text, ["financial analyst", "financial modeling", "investment banking", "portfolio manager"]):
        return "Financial Analyst"
    if contains_word(text, ["accountant", "cpa", "auditor", "tax compliance", "bookkeeper"]):
        return "Accountant / Financial Specialist"

    # 6. Human Resources & People
    if contains_word(text, ["human resources", "talent acquisition", "hr generalist", "recruiter", "people operations"]):
        return "Human Resources Specialist"

    # 7. Creative & Design
    if contains_word(text, ["graphic designer", "ui/ux", "product designer", "art director", "visual designer"]):
        return "Graphic / UI-UX Designer"

    # 8. Operations & Project Management
    if contains_word(text, ["scrum master", "project manager", "pmp", "agile coach"]):
        return "Project Manager / Scrum Master"
    if contains_word(text, ["operations manager", "supply chain", "logistics coordinator"]):
        return "Operations / Supply Chain Specialist"

    # 9. Education & Teaching
    if contains_word(text, ["teacher", "educator", "instructional designer", "professor", "curriculum developer"]):
        return "Educator / Instructional Specialist"

    # 10. Legal & Compliance
    if contains_word(text, ["paralegal", "legal counsel", "attorney", "compliance officer"]):
        return "Legal & Compliance Specialist"

    # 11. Mobile & App Development
    if contains_word(text, ["react native", "flutter", "ios developer", "android developer", "mobile developer", "mobile engineer"]):
        return "Mobile Application Engineer"

    # 12. Hardware, Electronics & Robotics
    if contains_word(text, ["vlsi", "asic", "fpga", "verilog", "vhdl"]):
        return "VLSI / ASIC Design Engineer"
    elif contains_word(text, ["embedded", "firmware", "microcontroller", "arm cortex", "stm32", "rtos"]):
        return "Embedded Systems Engineer"
    elif contains_word(text, ["pcb", "altium", "schematic", "hardware design"]):
        return "Hardware & PCB Engineer"
    elif contains_word(text, ["robotics", "ros", "ros2", "automation", "plc", "scada"]):
        return "Robotics & Automation Engineer"
    elif contains_word(text, ["rf", "telecom", "antenna", "wireless", "telecommunication"]):
        return "RF & Wireless Systems Engineer"
    elif contains_word(text, ["electronics", "ece", "electrical", "eee", "circuit"]):
        return "Electrical & Electronics Engineer"
    elif contains_word(text, ["mechanical", "solidworks", "cad", "ansys"]):
        return "Mechanical Engineer"

    # 13. Software & Data
    elif contains_word(text, ["data scientist", "machine learning", "ai engineer"]):
        return "Data Scientist / AI Engineer"
    elif contains_word(text, ["devops", "cloud engineer", "sre"]):
        return "Cloud & DevOps Engineer"
    elif contains_word(text, ["frontend", "react"]):
        return "Frontend Engineer"
    elif contains_word(text, ["backend"]):
        return "Backend Engineer"
    elif contains_word(text, ["software engineer", "developer", "full stack"]):
        return "Software Engineer"

    return "Professional Specialist"

def fallback_extract_entities(text: str, is_jd: bool = False) -> ExtractedEntities:
    """
    Universal domain-agnostic entity extractor.
    Extracts genuine skills, tools, qualifications, and role directly from any document
    without assuming software or engineering backgrounds, and without leaking education
    degree majors or phantom default soft skills into JD requirements.
    """
    # 1. Dynamically extract items from text sections & bullets
    dynamic_skills, dynamic_edu = extract_skills_and_education_from_sections(text)

    # 2. Text without education lines prevents degree majors leaking into skills/domains
    text_without_edu_lines = "\n".join([line for line in text.split("\n") if not is_education_line(line)])
    lower_text_clean = " " + text_without_edu_lines.lower() + " "

    # 3. Match against universal catalog
    found_hard = []
    for skill in KNOWN_HARD_SKILLS:
        pattern = r'\b' + re.escape(skill.lower()) + r'\b'
        if re.search(pattern, lower_text_clean):
            found_hard.append(skill)

    # Combine dynamic skills and catalog matches preserving priority
    all_hard = []
    for s in dynamic_skills + found_hard:
        if s not in all_hard:
            all_hard.append(s)

    # 4. Extract soft skills
    found_soft = []
    for skill in KNOWN_SOFT_SKILLS:
        pattern = r'\b' + re.escape(skill.lower()) + r'\b'
        if re.search(pattern, lower_text_clean):
            found_soft.append(skill)
    # Only supply default soft skills for candidates (resumes), NEVER fabricate for a JD
    if not found_soft and not is_jd:
        found_soft = ["Communication", "Problem Solving", "Collaboration", "Time Management", "Analytical Thinking"]

    # 5. Extract tools & platforms
    found_tools = []
    for tool in KNOWN_TOOLS:
        pattern = r'\b' + re.escape(tool.lower()) + r'\b'
        if re.search(pattern, lower_text_clean):
            found_tools.append(tool)
    for sk in dynamic_skills:
        if any(sk.lower().endswith(suffix) for suffix in ["api", "sdk", "ide", "tool", "studio", "framework", "library"]) or sk in KNOWN_TOOLS:
            if sk not in found_tools:
                found_tools.append(sk)

    # 6. Extract domains
    found_domains = []
    for domain in KNOWN_DOMAINS:
        pattern = r'\b' + re.escape(domain.lower()) + r'\b'
        if re.search(pattern, lower_text_clean):
            found_domains.append(domain)

    # If domain list is empty, infer domain from context
    if not found_domains:
        if contains_word(text_without_edu_lines, ["nurse", "clinical", "patient", "hospital", "health"]):
            found_domains = ["Healthcare & Patient Care"]
        elif contains_word(text_without_edu_lines, ["financial", "accounting", "tax", "audit", "budget"]):
            found_domains = ["Finance & Accounting"]
        elif contains_word(text_without_edu_lines, ["marketing", "seo", "content", "brand", "sales"]):
            found_domains = ["Marketing & Growth"]
        elif contains_word(text_without_edu_lines, ["hr", "human resources", "talent", "recruiting"]):
            found_domains = ["Human Resources"]
        elif contains_word(text_without_edu_lines, ["vlsi", "asic", "fpga", "verilog", "vhdl"]):
            found_domains = ["VLSI & Semiconductors"]
        elif contains_word(text_without_edu_lines, ["embedded", "microcontroller", "arm", "pcb", "altium", "circuit", "electronics", "ece"]):
            found_domains = ["Embedded Systems", "Electronics & Communication"]
        elif contains_word(text_without_edu_lines, ["mechanical", "solidworks", "cad", "ansys"]):
            found_domains = ["Mechanical Engineering"]
        elif contains_word(text_without_edu_lines, ["software", "developer", "backend", "frontend", "cloud", "react native"]):
            found_domains = ["Software Engineering"]
        else:
            found_domains = ["Professional Practice & Operations"]

    # 7. Estimate years of experience via regex
    exp_matches = re.findall(r'(\d+)\+?\s*(?:years|yrs)', lower_text_clean)
    years_exp = 0.0
    if exp_matches:
        try:
            years_exp = max([float(m) for m in exp_matches if float(m) <= 40])
        except ValueError:
            years_exp = 1.0

    # 8. Extract bullet points / project / experience lines
    raw_lines = [line.strip("-•* \t") for line in text.split("\n") if len(line.strip()) > 30]
    project_samples = raw_lines[:6] if raw_lines else ["Executed core responsibilities and deliverables aligned with role expectations."]

    # 9. Extract education
    education = list(dict.fromkeys(dynamic_edu))
    edu_terms = [
        "Bachelor", "Master", "B.S.", "B.A.", "M.S.", "M.A.", "MBA", "Ph.D.", "Associate", "Diploma",
        "B.Tech", "B.E.", "B.Com", "BBA", "B.Sc", "M.Sc", "BSN", "MSN", "MD", "CPA", "Certification"
    ]
    for edu in edu_terms:
        if re.search(r'\b' + re.escape(edu.lower()) + r'\b', text.lower()):
            if edu not in education:
                education.append(edu)
    if not education:
        education.append("Bachelor's degree, professional certification, or equivalent practical experience")

    inferred = infer_document_role(text)

    # Clean partition between hard skills and tools so tools are not evaluated twice
    tools_lower = {t.lower() for t in found_tools}
    soft_lower = {s.lower() for s in found_soft}
    domain_lower = {d.lower() for d in found_domains}

    clean_hard = [s for s in all_hard if s.lower() not in tools_lower and s.lower() not in soft_lower and s.lower() not in domain_lower]
    if not clean_hard and all_hard:
        clean_hard = all_hard[:20]

    # Fallback if no skills detected
    if not clean_hard and not found_tools:
        capitalized = re.findall(r'\b[A-Z][A-Za-z0-9+#]{2,15}\b', text_without_edu_lines)
        filtered_caps = [w for w in capitalized if w.lower() not in ["the", "and", "with", "from", "for", "resume", "curriculum", "vitae", "project", "experience", "education", "summary"]]
        clean_hard = list(dict.fromkeys(filtered_caps))[:6]
        if not clean_hard:
            clean_hard = ["Core Professional Competencies"]

    return ExtractedEntities(
        hard_skills=clean_hard[:35],
        soft_skills=found_soft[:10],
        tools_and_tech=found_tools[:20] if found_tools else clean_hard[:8],
        domain_knowledge=found_domains[:8],
        years_of_experience=years_exp if years_exp > 0 else 2.0,
        education=education,
        projects_or_experiences=project_samples,
        inferred_role=inferred
    )

# -------------------------------------------------------------
# 2. Structured Gemini Extraction
# -------------------------------------------------------------

EXTRACTION_SYSTEM_PROMPT = """
You are an expert multi-disciplinary recruiter and parser capable of analyzing ANY job or career field
across Healthcare, Nursing, Business, Finance, Accounting, Marketing, Sales, Human Resources, Legal,
Education, Design, Operations, Engineering, and Technology.

Analyze the provided document (Resume or Job Description) and extract key attributes in strictly valid JSON format.
Follow this schema:
{
  "hard_skills": ["list of key domain skills, competencies, certifications, or qualifications"],
  "soft_skills": ["list of interpersonal/professional skills (e.g. Communication, Problem Solving, Leadership)"],
  "tools_and_tech": ["list of tools, software, platforms, or equipment used in this profession"],
  "domain_knowledge": ["list of relevant industry or functional knowledge areas"],
  "years_of_experience": 3.0,
  "education": ["list of degrees, licenses, or educational qualifications"],
  "projects_or_experiences": ["list of key accomplishment or experience bullet points from the text"],
  "inferred_role": "Detected target or candidate job title (e.g. Registered Nurse, Financial Analyst, Digital Marketing Specialist, Embedded Systems Engineer)"
}

CRITICAL EXTRACTION CONSTRAINTS:
- "hard_skills" MUST contain only concrete, standalone skills, tools, technologies, methodologies, or certifications.
- NEVER include academic degree statements in "hard_skills" (e.g. "Bachelor's degree in Computer Science" belongs ONLY in "education").
- NEVER include grammatical fragments, conjunctions, or clauses in "hard_skills" (e.g. "or a related field", "and experience", "plus", "preferred").
- Strip introductory boilerplate prefixes from bullet points (e.g. from "Experience with Redux", extract only "Redux").
- Multi-skill bullets must be parsed into distinct individual skills (e.g. "Firebase, Expo, or push notifications" -> "Firebase", "Expo", "Push Notifications").

Do NOT include markdown backticks or commentary. Return only raw JSON.
"""

def extract_entities_with_llm(doc_text: str, is_jd: bool = False) -> ExtractedEntities:
    """
    Extracts structured entities using Gemini API with caching and fallback.
    Works for any role/industry across the market.
    """
    cache_key = f"extract_{'jd' if is_jd else 'res'}_{get_hash(doc_text)}"
    if cache_key in _LLM_CACHE:
        return ExtractedEntities(**_LLM_CACHE[cache_key])

    client = get_gemini_client()
    if not client:
        entities = fallback_extract_entities(doc_text, is_jd=is_jd)
        _LLM_CACHE[cache_key] = entities.model_dump()
        return entities

    doc_type = "Job Description" if is_jd else "Candidate Resume"
    user_prompt = f"Please extract structured entities from this {doc_type}:\n\n{doc_text[:4000]}"

    for attempt in range(2):
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=EXTRACTION_SYSTEM_PROMPT,
                    response_mime_type="application/json",
                    temperature=0.1,
                )
            )

            response_text = response.text.strip()
            if response_text.startswith("```"):
                response_text = re.sub(r"^```(?:json)?|```$", "", response_text, flags=re.MULTILINE).strip()

            parsed_data = json.loads(response_text)
            entities = ExtractedEntities(**parsed_data)
            _LLM_CACHE[cache_key] = entities.model_dump()
            return entities

        except Exception as err:
            print(f"[SkillBridge] LLM extraction attempt {attempt + 1} failed: {err}")
            time.sleep(1)

    entities = fallback_extract_entities(doc_text, is_jd=is_jd)
    _LLM_CACHE[cache_key] = entities.model_dump()
    return entities
