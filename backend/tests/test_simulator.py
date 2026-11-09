"""
Unit and API integration tests for the Predictive Match Uplift Simulator.
Verifies deterministic score recalculation, category progress deltas, and API response.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models.schemas import SkillMatchItem, SimulateRequest
from app.services.scoring_service import simulate_skill_uplift

client = TestClient(app)

def test_simulate_skill_uplift_logic():
    """Tests the deterministic simulation algorithm."""
    matches = [
        SkillMatchItem(
            skill="Python",
            category="hard_skills",
            status="Strong match",
            similarity_score=1.0,
            matched_with="Python"
        ),
        SkillMatchItem(
            skill="PostgreSQL",
            category="hard_skills",
            status="Missing",
            similarity_score=0.2,
            matched_with=None
        ),
        SkillMatchItem(
            skill="Docker",
            category="tools_and_tech",
            status="Missing",
            similarity_score=0.1,
            matched_with=None
        ),
        SkillMatchItem(
            skill="Communication",
            category="soft_skills",
            status="Strong match",
            similarity_score=1.0,
            matched_with="Communication"
        )
    ]

    baseline_score = 50.0

    # 1. No skills added -> uplift = 0
    res_zero = simulate_skill_uplift(
        all_skill_matches=matches,
        acquired_skills=[],
        company_type="mid_size_product",
        baseline_score=baseline_score
    )
    assert res_zero.uplift == 0.0

    # 2. Add PostgreSQL -> score should strictly increase
    res_one = simulate_skill_uplift(
        all_skill_matches=matches,
        acquired_skills=["PostgreSQL"],
        company_type="mid_size_product",
        baseline_score=baseline_score
    )
    assert res_one.simulated_score > baseline_score
    assert res_one.uplift > 0.0

    # 3. Add both PostgreSQL and Docker -> higher uplift
    res_both = simulate_skill_uplift(
        all_skill_matches=matches,
        acquired_skills=["PostgreSQL", "Docker"],
        company_type="mid_size_product",
        baseline_score=baseline_score
    )
    assert res_both.simulated_score > res_one.simulated_score
    assert res_both.uplift > res_one.uplift
    assert "PostgreSQL" in res_both.explanation

def test_simulate_endpoint_api():
    """Tests the /api/simulate HTTP endpoint."""
    payload = {
        "company_type": "early_stage_startup",
        "current_overall_score": 60.0,
        "acquired_skills": ["Kafka", "AWS"],
        "all_skill_matches": [
            {
                "skill": "Python",
                "category": "hard_skills",
                "status": "Strong match",
                "similarity_score": 1.0,
                "importance_rank": 1
            },
            {
                "skill": "Kafka",
                "category": "hard_skills",
                "status": "Missing",
                "similarity_score": 0.1,
                "importance_rank": 2
            },
            {
                "skill": "AWS",
                "category": "tools_and_tech",
                "status": "Missing",
                "similarity_score": 0.1,
                "importance_rank": 3
            }
        ]
    }

    response = client.post("/api/simulate", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["baseline_score"] == 60.0
    assert data["simulated_score"] > 60.0
    assert data["uplift"] > 0.0
    assert len(data["updated_breakdowns"]) > 0
    assert "explanation" in data
