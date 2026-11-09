"""
Main FastAPI application entry point for SkillBridge.
Sets up CORS, route controllers, database lifecycle, and friendly error handlers.
"""

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List
import uuid

from app.config import settings
from app.db.database import init_db, save_analysis, get_analysis, delete_analysis, delete_all_user_data
from app.models.schemas import (
    FullAnalysisResponse,
    ExtractedEntities,
    SimulateRequest,
    SimulateResponse,
    RoadmapResponse,
    RewriteProjectRequest,
    RewriteProjectResponse,
    GenerateBulletRequest,
    GenerateBulletResponse,
    SalaryResponse,
)
from app.services.parser_service import extract_resume_text, validate_jd_text
from app.services.llm_service import extract_entities_with_llm
from app.services.scoring_service import compute_overall_alignment, load_company_profiles, simulate_skill_uplift
from app.services.gap_service import prioritize_gaps, generate_rejection_reasons
from app.services.rewriter_service import generate_learning_roadmap, rewrite_project_bullet, generate_resume_bullets
from app.services.salary_service import compute_salary_insights, infer_role_from_text
from app.models.schemas import RoadmapRequest

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run database table initialization when the server starts."""
    init_db()
    yield

# Create FastAPI app instance with metadata
app = FastAPI(
    title="SkillBridge API",
    description="AI-powered career guidance platform bridging the gap between resume and job descriptions.",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS so React (Vite) running on localhost:5173 can talk to FastAPI
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    """Health check and welcome endpoint."""
    return {
        "app": "SkillBridge API",
        "status": "online",
        "version": "1.0.0",
        "privacy_note": "SkillBridge does not retain your resume longer than your active session. You can purge all data via DELETE /api/data."
    }

@app.get("/health")
def health_check():
    """Simple ping check for monitoring."""
    return {"status": "healthy"}

# -------------------------------------------------------------
# Phase 2: Resume & JD Parsing and Semantic Analysis Endpoints
# -------------------------------------------------------------

@app.post("/api/parse")
@app.post("/parse")
async def parse_documents(
    resume_file: Optional[UploadFile] = File(None),
    jd_text: Optional[str] = Form(None)
):
    """
    Parses an uploaded resume file and/or JD text into structured entities.
    Useful for modular testing and pre-flight validation.
    """
    parsed_res_entities = None
    parsed_jd_entities = None

    if resume_file:
        file_bytes = await resume_file.read()
        res_text = extract_resume_text(resume_file.filename, file_bytes)
        parsed_res_entities = extract_entities_with_llm(res_text, is_jd=False)

    if jd_text:
        clean_jd = validate_jd_text(jd_text)
        parsed_jd_entities = extract_entities_with_llm(clean_jd, is_jd=True)

    return {
        "resume_entities": parsed_res_entities,
        "jd_entities": parsed_jd_entities
    }

@app.post("/api/analyze", response_model=FullAnalysisResponse)
@app.post("/analyze", response_model=FullAnalysisResponse)
async def analyze_fit(
    resume_file: UploadFile = File(...),
    jd_text: str = Form(...),
    company_type: str = Form("mid_size_product")
):
    """
    Core analysis endpoint:
    1. Validates and extracts text from resume (PDF/DOCX) and raw JD.
    2. Extracts structured entities (hard skills, soft skills, tools, domain, exp).
    3. Runs semantic embedding cosine similarity matching.
    4. Computes category breakdowns and overall alignment score using company weight profile.
    5. Saves session to SQLite database.
    """
    # 1. Validate inputs and extract raw text
    file_bytes = await resume_file.read()
    res_text = extract_resume_text(resume_file.filename, file_bytes)
    clean_jd = validate_jd_text(jd_text)

    # 2. Extract structured entities with LLM (or robust local fallback)
    res_entities = extract_entities_with_llm(res_text, is_jd=False)
    jd_entities = extract_entities_with_llm(clean_jd, is_jd=True)

    # 3. Compute overall alignment score and category breakdowns
    overall_score, breakdowns, matches = compute_overall_alignment(
        resume_entities=res_entities,
        jd_entities=jd_entities,
        company_type=company_type
    )

    # 4. Phase 3: Prioritize gaps and generate recruiter-style rejection reasons
    ranked_gaps = prioritize_gaps(matches, clean_jd, company_type)
    rejection_reasons = generate_rejection_reasons(ranked_gaps, res_entities, clean_jd, company_type)

    # 5. Resolve human-readable company profile name
    profiles = load_company_profiles()
    comp_info = profiles.get(company_type, profiles.get("mid_size_product"))
    comp_name = comp_info.get("name", "Mid-Size Product Company")

    # 6. Infer candidate/target role from entities and raw text
    detected_role = (
        jd_entities.inferred_role
        or res_entities.inferred_role
        or infer_role_from_text(res_text, clean_jd)
    )

    # 7. Persist analysis session to SQLite
    session_id = str(uuid.uuid4())
    response_data = FullAnalysisResponse(
        session_id=session_id,
        overall_score=overall_score,
        company_type=company_type,
        company_name=comp_name,
        category_breakdowns=breakdowns,
        skill_matches=matches,
        rejection_reasons=rejection_reasons,
        resume_entities=res_entities,
        jd_entities=jd_entities,
        inferred_role=detected_role,
    )

    save_analysis(
        session_id=session_id,
        company_type=company_type,
        overall_score=overall_score,
        data=response_data.model_dump()
    )

    return response_data

@app.get("/api/analysis/{session_id}", response_model=FullAnalysisResponse)
def fetch_analysis(session_id: str):
    """Retrieves a previously computed analysis from SQLite."""
    data = get_analysis(session_id)
    if not data:
        raise HTTPException(status_code=404, detail="Analysis session not found.")
    return FullAnalysisResponse(**data)

# -------------------------------------------------------------
# Phase 4: Predictive Match Uplift Simulator Endpoint
# -------------------------------------------------------------

@app.post("/api/simulate", response_model=SimulateResponse)
@app.post("/simulate", response_model=SimulateResponse)
def simulate_match(req: SimulateRequest):
    """
    Predictive Match Uplift Simulator:
    Recalculates alignment score and category progress when the user toggles
    skills they plan to acquire, using the identical deterministic formula.
    """
    sim_result = simulate_skill_uplift(
        all_skill_matches=req.all_skill_matches,
        acquired_skills=req.acquired_skills,
        company_type=req.company_type,
        baseline_score=req.current_overall_score
    )
    return sim_result

# -------------------------------------------------------------
# Phase 5: Learning Roadmap & Bullet Rewriter Endpoints
# -------------------------------------------------------------

@app.post("/api/roadmap", response_model=RoadmapResponse)
@app.post("/roadmap", response_model=RoadmapResponse)
def get_roadmap(req: RoadmapRequest):
    """
    Generates an effort-vs-impact ranked step-by-step learning roadmap
    for the candidate's highest priority missing skills.
    """
    steps = generate_learning_roadmap(
        missing_skills=req.missing_skills,
        target_role=req.target_role or "Software Engineer",
        company_type=req.company_type or "mid_size_product"
    )
    return RoadmapResponse(steps=steps)

@app.post("/api/rewrite-project", response_model=RewriteProjectResponse)
@app.post("/rewrite-project", response_model=RewriteProjectResponse)
def rewrite_experience(req: RewriteProjectRequest):
    """
    Re-frames a candidate's project or experience bullet using strong industry
    action verbs and XYZ structure with explicit [X%] metric placeholders.
    """
    rewritten = rewrite_project_bullet(
        original_text=req.original_text,
        target_role=req.target_role or "Software Engineer",
        company_type=req.company_type or "mid_size_product",
        target_skills=req.target_skills or []
    )
    return rewritten

@app.post("/api/generate-bullet", response_model=GenerateBulletResponse)
@app.post("/generate-bullet", response_model=GenerateBulletResponse)
def generate_bullet(req: GenerateBulletRequest):
    """
    Generates 2-3 tailored ATS-ready resume bullets for an acquired or missing skill.
    """
    result = generate_resume_bullets(
        skill=req.skill,
        role_context=req.role_context or "Software Engineer"
    )
    return result

# -------------------------------------------------------------
# Phase 6: Salary Insights & Career Growth Estimation Endpoint
# -------------------------------------------------------------

@app.get("/api/salary", response_model=SalaryResponse)
@app.get("/salary", response_model=SalaryResponse)
def get_salary(
    role: Optional[str] = "software_engineer",
    currency: Optional[str] = None,
    region: Optional[str] = None,
    years_exp: Optional[float] = 3.0,
    skills: Optional[str] = ""
):
    """
    Returns indicative salary ranges (min, median, max), 1/3/5 year growth projections,
    and high-impact skill compensation premiums for USD and INR.
    Supports both currency='USD'|'INR' and region='US'|'India'.
    """
    selected_curr = "USD"
    if currency:
        selected_curr = currency.upper()
    elif region:
        reg_lower = region.lower()
        if "in" in reg_lower or "india" in reg_lower or "inr" in reg_lower:
            selected_curr = "INR"

    skill_list = [s.strip() for s in skills.split(",") if s.strip()] if skills else []
    return compute_salary_insights(
        role=role or "software_engineer",
        currency=selected_curr,
        years_exp=years_exp or 3.0,
        skills_acquired=skill_list
    )

# -------------------------------------------------------------
# Privacy & Session Management Endpoints
# -------------------------------------------------------------

@app.delete("/api/data/{session_id}")
def purge_session(session_id: str):
    """Delete a specific analysis session from SQLite."""
    success = delete_analysis(session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found or already deleted.")
    return {"message": f"Session {session_id} successfully deleted."}

@app.delete("/api/data")
def purge_all_data():
    """Wipe all stored analysis data for user privacy."""
    count = delete_all_user_data()
    return {"message": f"All user data purged. {count} records deleted."}
