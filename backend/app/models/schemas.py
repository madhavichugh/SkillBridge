"""
Pydantic schemas and data models for SkillBridge.
Defines strict types, defaults, and API validation.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

# -------------------------------------------------------------
# 1. Extracted Entity Models
# -------------------------------------------------------------

class ExtractedEntities(BaseModel):
    """Structured entities extracted from either a resume or a job description."""
    hard_skills: List[str] = Field(default_factory=list, description="Technical and specialized domain skills")
    soft_skills: List[str] = Field(default_factory=list, description="Interpersonal and teamwork skills")
    tools_and_tech: List[str] = Field(default_factory=list, description="Hardware, software tools, platforms, and EDA/DevOps suites")
    domain_knowledge: List[str] = Field(default_factory=list, description="Industry or engineering domains (e.g., Embedded Systems, VLSI, Power Electronics, FinTech)")
    years_of_experience: float = Field(default=0.0, description="Estimated years of relevant experience")
    education: List[str] = Field(default_factory=list, description="Degrees, fields of study, or certifications")
    projects_or_experiences: List[str] = Field(default_factory=list, description="Raw bullet points or summaries of projects/work history")
    inferred_role: Optional[str] = Field(default=None, description="Inferred target or candidate role")

class ResumeParseResponse(BaseModel):
    """Response returned when a resume file is parsed."""
    raw_text: str = Field(..., description="Extracted raw text from PDF/DOCX")
    entities: ExtractedEntities = Field(..., description="Structured entities extracted from the resume")

class JDParseResponse(BaseModel):
    """Response returned when JD text is parsed."""
    raw_text: str = Field(..., description="Original JD text")
    entities: ExtractedEntities = Field(..., description="Structured entities extracted from the JD")

# -------------------------------------------------------------
# 2. Skill Matching & Gap Models
# -------------------------------------------------------------

class SkillMatchItem(BaseModel):
    """Evaluation of a single JD requirement against the candidate's resume."""
    skill: str = Field(..., description="Requirement from the job description")
    category: str = Field(..., description="Category: hard_skills, soft_skills, tools_and_tech, or domain_knowledge")
    status: str = Field(..., description="'Strong match', 'Underrepresented', or 'Missing'")
    similarity_score: float = Field(..., description="Cosine similarity score (0.0 to 1.0)")
    matched_with: Optional[str] = Field(None, description="Most similar skill found in candidate's resume")
    importance_rank: int = Field(default=1, description="Rank based on emphasis, frequency, and company context")

class CategoryBreakdown(BaseModel):
    """Score breakdown for a specific skill category."""
    category_name: str = Field(..., description="Key of the category (e.g. hard_skills)")
    display_name: str = Field(..., description="Human-readable title")
    raw_score: float = Field(..., description="Percentage match in this category (0-100)")
    weight: float = Field(..., description="Weight assigned by company profile (e.g. 0.35)")
    weighted_score: float = Field(..., description="raw_score * weight")
    total_items: int = Field(default=0, description="Total requirements in JD for this category")
    matched_items: int = Field(default=0, description="Count of strong + partial matches")

class RejectionReason(BaseModel):
    """Recruiter-style explanation for potential disqualification."""
    title: str = Field(..., description="Recruiter headline (e.g., 'Limited Production SQL Experience')")
    reason: str = Field(..., description="Detailed recruiter perspective on why this presents a hiring risk")
    linked_gap: str = Field(..., description="The specific missing or underrepresented skill")
    resume_evidence: str = Field(..., description="What the resume actually shows (or misses)")
    actionable_fix: str = Field(..., description="Recommended fix or project to close this gap")

class FullAnalysisResponse(BaseModel):
    """Complete analysis combining score, gap categorization, and rejection explanations."""
    session_id: str = Field(..., description="Unique ID for this analysis session")
    overall_score: float = Field(..., description="Overall alignment score (0-100)")
    company_type: str = Field(..., description="Selected company profile key")
    company_name: str = Field(..., description="Human-readable company profile name")
    category_breakdowns: List[CategoryBreakdown] = Field(default_factory=list)
    skill_matches: List[SkillMatchItem] = Field(default_factory=list)
    rejection_reasons: List[RejectionReason] = Field(default_factory=list)
    resume_entities: ExtractedEntities
    jd_entities: ExtractedEntities
    inferred_role: Optional[str] = Field(default="Engineering Specialist", description="Detected job role from JD/Resume")

# -------------------------------------------------------------
# 3. Simulator Models
# -------------------------------------------------------------

class SimulateRequest(BaseModel):
    """Request payload to simulate score uplift when candidate acquires skills."""
    session_id: Optional[str] = Field(None, description="Optional existing session ID")
    company_type: str = Field(default="mid_size_product")
    current_overall_score: float = Field(..., description="Baseline alignment score")
    acquired_skills: List[str] = Field(default_factory=list, description="Skills candidate plans to learn")
    all_skill_matches: List[SkillMatchItem] = Field(default_factory=list, description="Current match evaluations")

class SimulateResponse(BaseModel):
    """Uplift response showing before/after scores and explainable delta."""
    baseline_score: float = Field(..., description="Original score before simulation")
    simulated_score: float = Field(..., description="New score after adding acquired skills")
    uplift: float = Field(..., description="Difference (simulated_score - baseline_score)")
    updated_breakdowns: List[CategoryBreakdown] = Field(default_factory=list)
    explanation: str = Field(..., description="Clear explanation of why the score improved")

# -------------------------------------------------------------
# 4. Roadmap & Rewriter Models
# -------------------------------------------------------------

class RoadmapStep(BaseModel):
    """Single step in the prioritized learning roadmap."""
    step_number: int
    skill: str
    impact_score: float = Field(..., description="Predicted alignment score boost")
    effort_level: str = Field(..., description="'Low', 'Medium', or 'High'")
    why_it_matters: str = Field(..., description="Why recruiters look for this skill")
    suggested_project: str = Field(..., description="Practical project type to prove competency")
    estimated_weeks: int = Field(..., description="Estimated time investment")

class RoadmapRequest(BaseModel):
    missing_skills: List[str] = Field(default_factory=list, description="Skills candidate needs to acquire")
    target_role: Optional[str] = Field(default="Software Engineer", description="Target role title")
    company_type: Optional[str] = Field(default="mid_size_product", description="Company culture profile")

class RoadmapResponse(BaseModel):
    steps: List[RoadmapStep] = Field(default_factory=list)

class RewriteProjectRequest(BaseModel):
    """Request to re-frame a project/experience bullet."""
    original_text: str = Field(..., description="Candidate's current bullet point or summary")
    target_role: Optional[str] = Field(default="Software Engineer", description="Target role title")
    company_type: Optional[str] = Field(default="mid_size_product", description="Company profile context")
    target_skills: List[str] = Field(default_factory=list, description="Skills to highlight")

class RewriteProjectResponse(BaseModel):
    rewritten_text: str = Field(..., description="Action-verb driven bullet with [X%] metric placeholders")
    action_verbs_used: List[str] = Field(default_factory=list)
    metrics_to_fill: List[str] = Field(default_factory=list, description="List of placeholders like [X%] the user must complete")
    explanation: str = Field(..., description="Why this version performs better with recruiters and ATS")

class GenerateBulletRequest(BaseModel):
    """Request to generate ATS bullets for a newly learned or missing skill."""
    skill: str = Field(..., description="Target skill to showcase")
    role_context: Optional[str] = Field(default="Software Engineer")

class GenerateBulletResponse(BaseModel):
    skill: str
    bullet_options: List[str] = Field(..., description="2-3 tailored ATS-ready resume bullet options")

# -------------------------------------------------------------
# 5. Salary Models
# -------------------------------------------------------------

class SalaryRange(BaseModel):
    min: float
    median: float
    max: float

class SalaryGrowthItem(BaseModel):
    year: str
    usd: float
    inr: float

class HighImpactSkill(BaseModel):
    skill: str
    premium_percent: int

class SalaryResponse(BaseModel):
    role_key: str
    role_title: str
    category: Optional[str] = "General Engineering"
    currency: str = Field(..., description="'USD' or 'INR'")
    range: SalaryRange
    growth_projection: List[SalaryGrowthItem]
    high_impact_skills: List[HighImpactSkill]
    all_available_roles: Optional[List[Dict[str, Any]]] = Field(default_factory=list, description="All roles available across engineering and technology")
    disclaimer: str = Field(
        default="Indicative estimate based on industry benchmarks. Actual compensation varies by location, level, and company."
    )
