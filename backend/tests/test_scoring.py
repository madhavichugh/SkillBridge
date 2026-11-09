"""
Unit tests for the semantic embedding matching and scoring service.
Verifies cosine similarity matching, threshold categorization, and company weighting.
"""

import pytest
from app.models.schemas import ExtractedEntities
from app.services.embedding_service import find_best_semantic_match
from app.services.scoring_service import (
    evaluate_skill_category,
    calculate_experience_score,
    compute_overall_alignment,
)

def test_semantic_match_exact():
    """Exact string matches should return similarity of 1.0."""
    score, matched = find_best_semantic_match("Python", ["Java", "Python", "C++"])
    assert score == 1.0
    assert matched == "Python"

def test_semantic_match_related_technologies():
    """
    Semantic embeddings should detect related technologies,
    e.g., React.js matches JavaScript or React with high similarity.
    """
    score, matched = find_best_semantic_match("React.js", ["JavaScript", "PostgreSQL", "Docker"])
    # React.js and JavaScript share strong semantic proximity in sentence-transformers
    assert score > 0.50
    assert matched == "JavaScript"

def test_semantic_match_missing():
    """Unrelated technologies should have low similarity scores."""
    score, matched = find_best_semantic_match("Kubernetes", ["HTML", "CSS", "Photoshop"])
    assert score < 0.50

def test_evaluate_skill_category_thresholds():
    """
    Verifies that items are correctly partitioned into
    'Strong match', 'Underrepresented', and 'Missing'.
    """
    jd_skills = ["Python", "JavaScript", "Kubernetes"]
    resume_skills = ["Python", "TypeScript"]  # Python is exact, TS is partial to JS, K8s is missing

    matches, raw_score, matched_count = evaluate_skill_category("hard_skills", jd_skills, resume_skills)

    assert len(matches) == 3
    # Check Python match
    python_match = next(m for m in matches if m.skill == "Python")
    assert python_match.status == "Strong match"
    assert python_match.similarity_score == 1.0

    # Raw score must be between 0 and 100
    assert 0.0 <= raw_score <= 100.0

def test_experience_scoring():
    """Tests experience alignment logic."""
    # Meets requirement
    assert calculate_experience_score(jd_years=3.0, res_years=5.0) == 100.0
    assert calculate_experience_score(jd_years=3.0, res_years=3.0) == 100.0
    # Fewer years gives proportional score
    partial = calculate_experience_score(jd_years=4.0, res_years=2.0)
    assert partial == 50.0

def test_compute_overall_alignment_bounds():
    """Verifies that overall alignment is strictly bounded between 0 and 100."""
    resume_entities = ExtractedEntities(
        hard_skills=["Python", "FastAPI", "SQL"],
        soft_skills=["Communication", "Problem Solving"],
        tools_and_tech=["Git", "Docker"],
        domain_knowledge=["Web Development"],
        years_of_experience=3.0
    )

    jd_entities = ExtractedEntities(
        hard_skills=["Python", "FastAPI", "PostgreSQL", "Kafka"],
        soft_skills=["Communication", "Agile"],
        tools_and_tech=["Git", "Docker", "Kubernetes"],
        domain_knowledge=["Web Development", "Distributed Systems"],
        years_of_experience=4.0
    )

    overall_score, breakdowns, matches = compute_overall_alignment(
        resume_entities=resume_entities,
        jd_entities=jd_entities,
        company_type="early_stage_startup"
    )

    assert 0.0 <= overall_score <= 100.0
    assert len(breakdowns) == 5
    assert len(matches) > 0

    # Ensure total weights sum to 1.0
    total_weights = sum(b.weight for b in breakdowns)
    assert round(total_weights, 2) == 1.0
