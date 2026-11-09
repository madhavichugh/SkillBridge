"""
End-to-end integration test for the /api/analyze endpoint.
Simulates a candidate uploading a resume and JD, verifying the full response.
"""

import io
from fastapi.testclient import TestClient
from app.main import app
import docx

client = TestClient(app)

def test_analyze_endpoint_end_to_end():
    # 1. Create in-memory mock resume docx
    doc = docx.Document()
    doc.add_paragraph("Alex Rivera - Full Stack Engineer")
    doc.add_paragraph("Skills: Python, React, PostgreSQL, Docker, Git, REST APIs")
    doc.add_paragraph("Experience: 3 years building cloud web services in an agile squad.")
    
    buffer = io.BytesIO()
    doc.save(buffer)
    resume_bytes = buffer.getvalue()

    # 2. Mock JD text
    jd_text = (
        "We are hiring a Software Engineer with at least 3 years of experience. "
        "Required skills: Python, React, PostgreSQL, Docker, Kubernetes, and Git. "
        "Domain knowledge in Web Development and Microservices. Strong agile collaboration."
    )

    # 3. Post to /api/analyze
    response = client.post(
        "/api/analyze",
        data={
            "jd_text": jd_text,
            "company_type": "mid_size_product"
        },
        files={
            "resume_file": ("Alex_Resume.docx", resume_bytes, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        }
    )

    assert response.status_code == 200
    data = response.json()

    # 4. Verify response structure and scoring
    assert "session_id" in data
    assert "overall_score" in data
    assert 0.0 <= data["overall_score"] <= 100.0
    assert data["company_type"] == "mid_size_product"
    assert len(data["category_breakdowns"]) == 5
    assert len(data["skill_matches"]) > 0

    # Verify that session is retrievable via GET /api/analysis/{session_id}
    session_id = data["session_id"]
    get_res = client.get(f"/api/analysis/{session_id}")
    assert get_res.status_code == 200
    assert get_res.json()["session_id"] == session_id
