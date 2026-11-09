"""
Dedicated unit and integration tests for Electrical, Electronics, and Hardware domains.
Ensures SkillBridge accurately analyzes ECE resumes without falling back to software developer defaults.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.llm_service import extract_entities_with_llm, infer_document_role
from app.services.scoring_service import compute_overall_alignment
from app.services.salary_service import infer_role_from_text, match_role_key, compute_salary_insights

client = TestClient(app)

ECE_RESUME_TEXT = """
Rahul Sharma
Electrical and Electronics Engineer (ECE)
Email: rahul@example.com

Technical Skills:
Languages: Embedded C, C++, Python, MATLAB
Hardware: ARM Cortex-M4, STM32, Arduino, ESP32, 8051
Protocols: I2C, SPI, UART, CAN, PWM, ADC
EDA & Tools: Altium Designer, KiCad, Keil uVision, STM32CubeIDE, MATLAB, Simulink
Testing: Oscilloscope, Logic Analyzer, Multimeter, Soldering
Domain: Embedded Systems, Digital Electronics, PCB Design, Signal Processing

Work Experience:
Embedded Hardware Engineer (2022 - Present)
Programmed bare-metal firmware in Embedded C for STM32 microcontrollers.
Designed 2-layer PCBs using Altium Designer and validated sensor telemetry over I2C.
"""

ECE_JD_TEXT = """
Job Title: Embedded Systems & Firmware Engineer
Company: Robotics & Core Hardware Corp

We are seeking an Embedded Systems Engineer to develop low-level firmware and device drivers.

Requirements:
- 2+ years of experience in Embedded C and ARM Cortex microcontrollers.
- Hands-on experience with FreeRTOS and communication protocols (I2C, SPI, UART, CAN).
- Experience with Altium Designer or KiCad for PCB debugging.
- Familiarity with Oscilloscope and Logic Analyzer testing.
- Bachelor's degree in Electrical & Electronics Engineering (ECE).
"""

def test_ece_skill_extraction_no_software_bias():
    """Verifies that ECE entities are extracted accurately without defaulting to web software skills."""
    res_entities = extract_entities_with_llm(ECE_RESUME_TEXT, is_jd=False)
    
    # Check that real ECE skills are present
    extracted_lower = [s.lower() for s in res_entities.hard_skills + res_entities.tools_and_tech]
    assert any("embedded c" in s for s in extracted_lower)
    assert any("stm32" in s or "arm cortex" in s for s in extracted_lower)
    assert any("altium" in s or "kicad" in s for s in extracted_lower)
    assert any("i2c" in s or "spi" in s or "uart" in s for s in extracted_lower)

    # Check that web software skills were NOT falsely injected
    assert "javascript" not in extracted_lower
    assert "react" not in extracted_lower
    assert "html5" not in extracted_lower

def test_ece_role_inference():
    """Verifies that role detection identifies ECE / Embedded domain from text."""
    inferred_role = infer_role_from_text(ECE_RESUME_TEXT, ECE_JD_TEXT)
    assert inferred_role in ["embedded_systems_engineer", "electrical_engineer", "hardware_engineer"]

def test_ece_scoring_alignment():
    """Verifies semantic alignment between ECE resume and ECE JD."""
    res_entities = extract_entities_with_llm(ECE_RESUME_TEXT, is_jd=False)
    jd_entities = extract_entities_with_llm(ECE_JD_TEXT, is_jd=True)

    score, breakdowns, matches = compute_overall_alignment(
        resume_entities=res_entities,
        jd_entities=jd_entities,
        company_type="mid_size_product"
    )

    # Candidate has Embedded C, STM32, I2C, SPI, Altium -> Should have high alignment (> 60%)
    assert score > 60.0
    assert len(matches) > 0

    # Strong matches should include hardware/embedded skills
    strong_matches = [m.skill for m in matches if m.status == "Strong match"]
    assert any("embedded c" in m.lower() or "i2c" in m.lower() or "altium" in m.lower() or "arm" in m.lower() for m in strong_matches)

def test_ece_analyze_api():
    """Verifies full /api/analyze flow with an ECE resume and JD."""
    files = {
        "resume_file": ("rahul_ece_resume.txt", ECE_RESUME_TEXT.encode("utf-8"), "text/plain")
    }
    data = {
        "jd_text": ECE_JD_TEXT,
        "company_type": "mid_size_product"
    }

    response = client.post("/api/analyze", files=files, data=data)
    assert response.status_code == 200
    res_data = response.json()

    assert "session_id" in res_data
    assert res_data["overall_score"] > 50.0
    assert res_data["inferred_role"] is not None
    assert any(k in res_data["inferred_role"].lower() for k in ["embedded", "electrical", "hardware", "engineering"])
