"""
Unit tests for the gap analysis and rejection reason service.
Verifies gap ranking, severity sorting, and recruiter perspective explanations.
"""

import pytest
from app.models.schemas import SkillMatchItem, ExtractedEntities
from app.services.gap_service import prioritize_gaps, generate_rejection_reasons

def test_prioritize_gaps_ranking():
    """
    Tests that missing requirements are prioritized higher than partial matches,
    and items with higher JD mention frequency get ranked first.
    """
    matches = [
        SkillMatchItem(
            skill="Python",
            category="hard_skills",
            status="Strong match",
            similarity_score=1.0,
            matched_with="Python"
        ),
        SkillMatchItem(
            skill="Kafka",
            category="hard_skills",
            status="Missing",
            similarity_score=0.15,
            matched_with=None
        ),
        SkillMatchItem(
            skill="Docker",
            category="tools_and_tech",
            status="Underrepresented",
            similarity_score=0.62,
            matched_with="Git"
        ),
        SkillMatchItem(
            skill="PostgreSQL",
            category="hard_skills",
            status="Missing",
            similarity_score=0.20,
            matched_with=None
        )
    ]

    # JD text with repeated mention of Kafka
    jd_text = (
        "We need Kafka expertise. You will build high-throughput Kafka streaming pipelines. "
        "Experience with PostgreSQL and Docker is also required."
    )

    ranked = prioritize_gaps(matches, jd_text, company_type="mid_size_product")

    # Strong matches should be filtered out from the gaps
    assert all(item.status != "Strong match" for item in ranked)
    assert len(ranked) == 3

    # Kafka is mentioned multiple times and is Missing, so it should rank #1
    assert ranked[0].skill == "Kafka"
    assert ranked[0].importance_rank == 1
    assert ranked[1].importance_rank == 2
    assert ranked[2].importance_rank == 3

def test_generate_rejection_reasons():
    """
    Tests that recruiter rejection reasons are generated with all required fields
    and linked to specific resume gaps.
    """
    gaps = [
        SkillMatchItem(
            skill="PostgreSQL",
            category="hard_skills",
            status="Missing",
            similarity_score=0.20,
            importance_rank=1
        ),
        SkillMatchItem(
            skill="Docker",
            category="tools_and_tech",
            status="Missing",
            similarity_score=0.10,
            importance_rank=2
        )
    ]

    resume_entities = ExtractedEntities(
        hard_skills=["Python", "Flask", "SQLite"],
        soft_skills=["Communication"],
        tools_and_tech=["Git"],
        domain_knowledge=["Web Apps"],
        years_of_experience=2.0
    )

    jd_text = "Looking for a backend engineer with PostgreSQL and Docker deployment expertise."

    reasons = generate_rejection_reasons(gaps, resume_entities, jd_text, company_type="enterprise_bank")

    assert len(reasons) >= 2
    for r in reasons:
        assert r.title
        assert r.reason
        assert r.linked_gap in ["PostgreSQL", "Docker"]
        assert r.resume_evidence
        assert r.actionable_fix
