"""
Unit and API integration tests for the Roadmap, Bullet Rewriter, and Project Re-framer.
Verifies XYZ structure, [X%] metric placeholders, ATS bullet generation, and roadmap sequencing.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.rewriter_service import (
    generate_learning_roadmap,
    rewrite_project_bullet,
    generate_resume_bullets
)

client = TestClient(app)

def test_generate_learning_roadmap():
    """Tests roadmap generation, ordering, and field presence."""
    skills = ["PostgreSQL", "Docker", "Kubernetes"]
    steps = generate_learning_roadmap(skills, target_role="Backend Engineer", company_type="mid_size_product")

    assert len(steps) >= 3
    # Verify sequential step numbers
    for idx, step in enumerate(steps, start=1):
        assert step.step_number == idx
        assert step.skill
        assert step.effort_level in ["Low", "Medium", "High"]
        assert step.why_it_matters
        assert step.suggested_project
        assert step.estimated_weeks > 0

def test_rewrite_project_bullet_placeholders():
    """
    CRITICAL REQUIREMENT TEST:
    Verify that project re-framing uses strong action verbs and inserts
    explicit [X%] or [N] placeholders instead of fabricating unverified numbers.
    """
    original = "Built a Flask API and connected it to SQLite database for an inventory app."
    result = rewrite_project_bullet(original, target_role="Backend Developer", target_skills=["PostgreSQL"])

    assert result.rewritten_text
    assert len(result.action_verbs_used) > 0
    # Must contain bracketed metric placeholders like [X%] or [N]
    assert "[" in result.rewritten_text and "]" in result.rewritten_text
    assert len(result.metrics_to_fill) > 0
    assert result.explanation

def test_generate_resume_bullets():
    """Tests that ATS bullet generator returns 2-3 tailored options."""
    result = generate_resume_bullets(skill="Docker", role_context="DevOps Engineer")

    assert result.skill == "Docker"
    assert len(result.bullet_options) >= 2
    for b in result.bullet_options:
        assert "Docker" in b or "container" in b.lower()
        # Should include placeholders for customization
        assert "[" in b and "]" in b

def test_api_endpoints_phase5():
    """Tests the three Phase 5 HTTP endpoints."""
    # 1. /api/roadmap
    roadmap_res = client.post("/api/roadmap", json={"missing_skills": ["Kafka", "AWS"]})
    assert roadmap_res.status_code == 200
    assert len(roadmap_res.json()["steps"]) > 0

    # 2. /api/rewrite-project
    rewrite_res = client.post("/api/rewrite-project", json={
        "original_text": "Helped team deploy services to cloud.",
        "target_role": "Cloud Engineer"
    })
    assert rewrite_res.status_code == 200
    assert "[" in rewrite_res.json()["rewritten_text"]

    # 3. /api/generate-bullet
    bullet_res = client.post("/api/generate-bullet", json={"skill": "FastAPI"})
    assert bullet_res.status_code == 200
    assert len(bullet_res.json()["bullet_options"]) >= 2

def test_ece_hardware_roadmap_and_bullets():
    """Verifies that ECE and Hardware skills generate domain-specific curricula and ATS bullets."""
    skills = ["Embedded C", "Altium", "Verilog"]
    steps = generate_learning_roadmap(skills, target_role="Electrical Engineer", company_type="mid_size_product")
    assert len(steps) >= 3
    assert any("microcontroller" in s.why_it_matters.lower() or "circuit" in s.why_it_matters.lower() or "fpga" in s.why_it_matters.lower() for s in steps)

    bullets = generate_resume_bullets(skill="FreeRTOS", role_context="Embedded Systems Engineer")
    assert len(bullets.bullet_options) >= 2
    assert any("FreeRTOS" in b for b in bullets.bullet_options)
    assert any("[" in b for b in bullets.bullet_options)
