"""
Rewriter and Learning Roadmap Service for SkillBridge.
Provides:
1. Prioritized learning roadmap ordered by score impact vs. effort to learn.
2. Targeted experience and project re-framing with strong action verbs and [X%] metric placeholders (no fake numbers).
3. One-click ATS resume bullet generation for newly acquired or underrepresented skills.
"""

import json
import re
import time
from typing import List, Dict, Any, Optional
from google.genai import types

from app.models.schemas import (
    RoadmapStep,
    RoadmapResponse,
    RewriteProjectRequest,
    RewriteProjectResponse,
    GenerateBulletRequest,
    GenerateBulletResponse,
)
from app.services.llm_service import get_gemini_client, get_hash, _LLM_CACHE

# -------------------------------------------------------------
# 1. Learning Roadmap Generator
# -------------------------------------------------------------

ROADMAP_SYSTEM_PROMPT = """
You are an executive career coach and professional curriculum architect across diverse industries
(Healthcare, Business, Finance, Marketing, Sales, Operations, Education, Legal, Engineering, and Tech).
Create an ordered, step-by-step learning roadmap for the candidate to acquire high-impact missing qualifications.
Order the sequence by highest alignment impact vs. realistic learning effort.

For each skill or qualification, output:
- step_number: 1, 2, 3...
- skill: skill or credential name
- impact_score: score boost (e.g. 15.0)
- effort_level: "Low", "Medium", or "High"
- why_it_matters: why hiring managers specifically look for this competency
- suggested_project: practical hands-on project, case study, or certification to showcase on a portfolio or resume
- estimated_weeks: integer weeks to reach job-readiness

Return strictly valid JSON matching this schema:
[
  {
    "step_number": 1,
    "skill": "Strategic Financial Modeling & Forecasting",
    "impact_score": 14.0,
    "effort_level": "Medium",
    "why_it_matters": "Essential for corporate budget planning, variance analysis, and executive decision-making.",
    "suggested_project": "Build a comprehensive 3-statement financial model with scenario sensitivity analysis.",
    "estimated_weeks": 3
  }
]
Do NOT output markdown backticks. Return only raw JSON.
"""

# Curated reference metadata for standard tech skills (used in fallback mode)
SKILL_CURRICULUM_DATA = {
    "sql": {
        "effort": "Medium",
        "weeks": 3,
        "impact": 14.0,
        "why": "Recruiters and hiring managers test database indexing, joins, and transactions in almost every technical interview.",
        "project": "Design a relational schema with PostgreSQL, write complex CTEs, and optimize slow queries using EXPLAIN ANALYZE."
    },
    "postgresql": {
        "effort": "Medium",
        "weeks": 3,
        "impact": 14.0,
        "why": "Standard industry open-source relational database for production web backends.",
        "project": "Build an e-commerce order management system with ACID transactions, indexing, and connection pooling."
    },
    "docker": {
        "effort": "Low",
        "weeks": 2,
        "impact": 12.0,
        "why": "Containerization proves you can package applications that run consistently across development, staging, and production.",
        "project": "Containerize a multi-service app (API + database + cache) using Docker Compose with multi-stage production builds."
    },
    "kubernetes": {
        "effort": "High",
        "weeks": 5,
        "impact": 15.0,
        "why": "Critical for cloud-native infrastructure, microservice autoscaling, and zero-downtime rollouts.",
        "project": "Deploy a containerized microservice to a local Minikube cluster with Deployments, Services, and Ingress routing."
    },
    "aws": {
        "effort": "Medium",
        "weeks": 4,
        "impact": 13.0,
        "why": "Cloud infrastructure knowledge is mandatory for modern engineering roles across startups and enterprises.",
        "project": "Host a containerized web service on AWS ECS with RDS PostgreSQL, S3 bucket storage, and CloudWatch logs."
    },
    "redis": {
        "effort": "Low",
        "weeks": 2,
        "impact": 10.0,
        "why": "High-throughput systems rely on distributed in-memory caching to protect relational databases.",
        "project": "Implement an API rate-limiter and caching layer using Redis with cache-aside and TTL eviction policies."
    },
    "kafka": {
        "effort": "High",
        "weeks": 4,
        "impact": 15.0,
        "why": "Event streaming architectures are the standard for decoupled, asynchronous enterprise microservices.",
        "project": "Build an event-driven notification service with Kafka producers, consumer groups, and dead-letter queues."
    },
    "fastapi": {
        "effort": "Low",
        "weeks": 2,
        "impact": 11.0,
        "why": "Modern, high-performance async Python framework rapidly overtaking legacy frameworks in AI and microservices.",
        "project": "Build an asynchronous RESTful API with Pydantic validation, JWT authentication, and automated OpenAPI docs."
    },
    "typescript": {
        "effort": "Medium",
        "weeks": 3,
        "impact": 12.0,
        "why": "Static typing prevents entire classes of runtime errors in large enterprise codebases.",
        "project": "Migrate a JavaScript React or Node application to strict TypeScript with custom interfaces and generics."
    },
    "system design": {
        "effort": "High",
        "weeks": 6,
        "impact": 18.0,
        "why": "The definitive differentiator for mid-level and senior engineering promotions and offers.",
        "project": "Write an architectural design document for a URL shortener or rate limiter detailing throughput, storage, and failover."
    },
    # Electrical & Electronics, Embedded Systems, and VLSI
    "verilog": {
        "effort": "High",
        "weeks": 5,
        "impact": 16.0,
        "why": "Core hardware description language required for FPGA logic synthesis and digital ASIC design.",
        "project": "Design, simulate, and synthesize an AXI4-Lite peripheral slave or UART transceiver module with ModelSim testbench."
    },
    "systemverilog": {
        "effort": "High",
        "weeks": 5,
        "impact": 17.0,
        "why": "The industry standard for advanced hardware verification (UVM) and complex digital IC architectures.",
        "project": "Build a constrained-random verification testbench with assertions and functional coverage for an asynchronous FIFO."
    },
    "vhdl": {
        "effort": "High",
        "weeks": 5,
        "impact": 15.0,
        "why": "Standard HDL widely used in defense, aerospace, and safety-critical FPGA systems.",
        "project": "Implement a pipelined CORDIC math coprocessor on an FPGA development board."
    },
    "embedded c": {
        "effort": "Medium",
        "weeks": 4,
        "impact": 16.0,
        "why": "Indispensable foundation for bare-metal firmware, driver programming, and low-latency microcontrollers.",
        "project": "Write custom low-level device drivers (I2C, SPI, DMA) for sensor data acquisition on an ARM Cortex-M microcontroller."
    },
    "altium": {
        "effort": "Medium",
        "weeks": 4,
        "impact": 15.0,
        "why": "Industry-leading EDA tool for multilayer PCB schematic capture, high-speed routing, and design for manufacturing.",
        "project": "Design a 4-layer mixed-signal PCB incorporating power regulators, microcontroller, and impedance-matched RF/USB traces."
    },
    "pcb design": {
        "effort": "Medium",
        "weeks": 4,
        "impact": 15.0,
        "why": "Crucial hardware skill to convert circuit ideas into manufactured, EMC-compliant physical boards.",
        "project": "Layout a compact sensor breakout board with differential pairs, ground planes, and complete Gerber/BOM fabrication outputs."
    },
    "kicad": {
        "effort": "Low",
        "weeks": 2,
        "impact": 12.0,
        "why": "Popular open-source EDA suite used across modern hardware startups, research labs, and prototyping.",
        "project": "Design a 2-layer IoT sensor telemetry board with USB-C power delivery and KiCad 3D visualization."
    },
    "matlab": {
        "effort": "Medium",
        "weeks": 3,
        "impact": 14.0,
        "why": "Gold-standard numerical computing and algorithm simulation environment for signal processing and controls.",
        "project": "Simulate and design a digital FIR/IIR low-pass filter and evaluate frequency response against noisy sensor telemetry."
    },
    "simulink": {
        "effort": "Medium",
        "weeks": 3,
        "impact": 14.0,
        "why": "Standard model-based design and hardware-in-the-loop (HIL) testing platform for automotive and aerospace control loops.",
        "project": "Model a closed-loop PID DC motor controller with state-space representation and pulse-width modulation (PWM)."
    },
    "rtos": {
        "effort": "High",
        "weeks": 4,
        "impact": 16.0,
        "why": "Essential for deterministic real-time execution, task scheduling, mutexes, and queues in complex embedded systems.",
        "project": "Build a multi-tasking telemetry logger in FreeRTOS managing inter-task communication via queues and preemptive priorities."
    },
    "freertos": {
        "effort": "High",
        "weeks": 4,
        "impact": 16.0,
        "why": "The most widely deployed real-time operating system kernel for microcontrollers and IoT edge nodes.",
        "project": "Configure task scheduling, software timers, and semaphore-guarded peripherals on STM32 hardware."
    },
    "stm32": {
        "effort": "Medium",
        "weeks": 4,
        "impact": 15.0,
        "why": "Standard 32-bit ARM Cortex-M microcontroller architecture used across consumer, automotive, and industrial electronics.",
        "project": "Develop firmware utilizing STM32CubeIDE/HAL to stream ADC conversions over DMA and transmit via CAN bus."
    },
    "arm cortex": {
        "effort": "Medium",
        "weeks": 4,
        "impact": 15.0,
        "why": "Dominant processor core architecture in smartphones, embedded devices, and automotive ECUs worldwide.",
        "project": "Implement interrupt-driven GPIO handling and power-saving sleep modes on an ARM Cortex-M4 platform."
    },
    "fpga": {
        "effort": "High",
        "weeks": 6,
        "impact": 17.0,
        "why": "Enables ultra-low latency hardware acceleration, high-speed DSP, and custom hardware prototyping.",
        "project": "Implement a real-time digital video processing filter (edge detection) on a Xilinx/AMD Artix-7 FPGA."
    },
    "dsp": {
        "effort": "High",
        "weeks": 5,
        "impact": 15.0,
        "why": "Critical math and algorithm foundation for radar, audio, telecommunications, and biomedical instrumentation.",
        "project": "Implement a Fast Fourier Transform (FFT) spectral analyzer in C with fixed-point arithmetic."
    },
    "ros": {
        "effort": "High",
        "weeks": 5,
        "impact": 16.0,
        "why": "Standard middleware framework for mobile robotics, autonomous navigation, and manipulator controls.",
        "project": "Build an autonomous obstacle avoidance navigation node using ROS2, LiDAR SLAM, and Nav2."
    },
    "solidworks": {
        "effort": "Medium",
        "weeks": 4,
        "impact": 14.0,
        "why": "Parametric 3D CAD modeling software essential for mechanical enclosures, mechanism design, and GD&T.",
        "project": "Model an IP67-rated waterproof electronics enclosure with heat sink fins and snap-fit tooling drafts."
    }
}

def get_default_skills_for_role(target_role: str) -> List[str]:
    """Returns domain-appropriate baseline skills if none are provided."""
    role_lower = target_role.lower()
    if any(k in role_lower for k in ["nurse", "nursing", "clinical", "patient"]):
        return ["Electronic Health Records (EHR)", "Clinical Assessment & Triage", "Patient Case Management", "Critical Care Protocols"]
    elif any(k in role_lower for k in ["financial", "finance", "investment"]):
        return ["Financial Modeling (DCF)", "Advanced Excel & Power Query", "Variance Analysis", "GAAP Compliance"]
    elif any(k in role_lower for k in ["accountant", "accounting", "tax", "audit"]):
        return ["ERP Systems (SAP / NetSuite)", "Internal Financial Controls", "Corporate Tax Compliance", "Audit Preparation"]
    elif any(k in role_lower for k in ["marketing", "seo", "content", "growth"]):
        return ["Technical SEO & Content Strategy", "Google Analytics 4 & Attribution", "HubSpot Automation", "Conversion Rate Optimization"]
    elif any(k in role_lower for k in ["sales", "account executive", "bdr", "sdr"]):
        return ["B2B Enterprise Solution Selling", "Salesforce Pipeline Management", "Contract Negotiation", "Lead Qualification"]
    elif any(k in role_lower for k in ["hr", "human resources", "talent", "recruiting"]):
        return ["HRIS Administration (Workday)", "Executive Sourcing Strategy", "Compensation Benchmarking", "Employee Relations"]
    elif any(k in role_lower for k in ["operations", "supply chain", "logistics"]):
        return ["Lean Six Sigma Process Optimization", "Supply Chain Inventory Management", "Vendor Procurement", "SLA & KPI Tracking"]
    elif any(k in role_lower for k in ["designer", "graphic", "ui/ux", "visual"]):
        return ["Figma Design Systems", "User Research & Usability Testing", "Adobe Creative Cloud", "Visual Prototyping"]
    elif any(k in role_lower for k in ["teacher", "educator", "instructional"]):
        return ["Curriculum & Rubric Architecture", "Educational Technology & LMS", "Differentiated Instruction", "Student Assessment"]
    elif any(k in role_lower for k in ["legal", "counsel", "paralegal"]):
        return ["Commercial Contract Drafting", "Regulatory & Privacy Compliance", "Corporate Governance", "Dispute Resolution"]
    elif any(k in role_lower for k in ["vlsi", "asic", "fpga", "semiconductor"]):
        return ["Verilog", "SystemVerilog", "FPGA", "Timing Analysis"]
    elif any(k in role_lower for k in ["embed", "firmware", "microcontroller"]):
        return ["Embedded C", "FreeRTOS", "STM32", "Device Drivers"]
    elif any(k in role_lower for k in ["hardware", "pcb", "altium", "schematic"]):
        return ["Altium Designer", "PCB Design", "Signal Integrity", "Schematic Capture"]
    elif any(k in role_lower for k in ["electr", "ece", "eee", "circuit"]):
        return ["Embedded C", "Altium Designer", "MATLAB", "Microcontrollers"]
    elif any(k in role_lower for k in ["robot", "automation", "mechatronics"]):
        return ["ROS", "C++", "Control Systems", "Computer Vision"]
    elif any(k in role_lower for k in ["mech", "cad", "solidworks"]):
        return ["SolidWorks", "ANSYS", "GD&T", "DFM"]
    elif any(k in role_lower for k in ["data", "ai", "machine learning"]):
        return ["Python", "SQL", "Pandas", "Scikit-Learn"]
    elif any(k in role_lower for k in ["devops", "cloud", "sre"]):
        return ["Docker", "Kubernetes", "AWS", "Terraform"]
    return ["Strategic Planning & Leadership", "Process Optimization", "Data-Driven Analysis", "Stakeholder Communication"]

def fallback_learning_roadmap(missing_skills: List[str], target_role: str) -> List[RoadmapStep]:
    """Fallback roadmap generator when LLM is offline or unconfigured."""
    steps: List[RoadmapStep] = []
    default_skills = missing_skills if missing_skills else get_default_skills_for_role(target_role)

    for idx, skill in enumerate(default_skills[:5], start=1):
        clean_key = skill.lower().strip()
        matched_info = None

        for k, v in SKILL_CURRICULUM_DATA.items():
            if k in clean_key or clean_key in k:
                matched_info = v
                break

        if matched_info:
            effort = matched_info["effort"]
            weeks = matched_info["weeks"]
            impact = matched_info["impact"]
            why = matched_info["why"]
            project = matched_info["project"]
        else:
            effort = "Medium"
            weeks = 3
            impact = 10.0
            why = f"High-demand qualification for {target_role} roles to demonstrate applied mastery and operational readiness."
            project = f"Execute a practical case study, certification, or portfolio deliverable demonstrating {skill}."

        steps.append(
            RoadmapStep(
                step_number=idx,
                skill=skill,
                impact_score=impact,
                effort_level=effort,
                why_it_matters=why,
                suggested_project=project,
                estimated_weeks=weeks,
            )
        )

    # Sort by impact_score descending
    steps.sort(key=lambda x: x.impact_score, reverse=True)
    # Re-index step numbers
    for i, s in enumerate(steps, start=1):
        s.step_number = i

    return steps

def generate_learning_roadmap(
    missing_skills: List[str],
    target_role: str = "Software Engineer",
    company_type: str = "mid_size_product"
) -> List[RoadmapStep]:
    """Generates a structured, ordered learning roadmap."""
    if not missing_skills:
        missing_skills = get_default_skills_for_role(target_role)

    cache_key = f"roadmap_{get_hash(','.join(missing_skills))}_{target_role}"
    if cache_key in _LLM_CACHE:
        return [RoadmapStep(**item) for item in _LLM_CACHE[cache_key]]

    client = get_gemini_client()
    if not client:
        steps = fallback_learning_roadmap(missing_skills, target_role)
        _LLM_CACHE[cache_key] = [s.model_dump() for s in steps]
        return steps

    prompt = (
        f"Target Role: {target_role}\n"
        f"Company Culture Context: {company_type}\n"
        f"Candidate Missing Skills to Prioritize: {', '.join(missing_skills[:6])}\n\n"
        "Create an actionable, ordered learning roadmap for these skills."
    )

    for attempt in range(2):
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=ROADMAP_SYSTEM_PROMPT,
                    response_mime_type="application/json",
                    temperature=0.2,
                )
            )

            resp_text = response.text.strip()
            if resp_text.startswith("```"):
                resp_text = re.sub(r"^```(?:json)?|```$", "", resp_text, flags=re.MULTILINE).strip()

            parsed = json.loads(resp_text)
            if isinstance(parsed, list):
                steps = [RoadmapStep(**item) for item in parsed]
                _LLM_CACHE[cache_key] = [s.model_dump() for s in steps]
                return steps

        except Exception as e:
            print(f"[SkillBridge] Roadmap LLM call attempt {attempt+1} failed: {e}")
            time.sleep(1)

    steps = fallback_learning_roadmap(missing_skills, target_role)
    _LLM_CACHE[cache_key] = [s.model_dump() for s in steps]
    return steps

# -------------------------------------------------------------
# 2. Targeted Project & Experience Re-Framing
# -------------------------------------------------------------

REWRITE_SYSTEM_PROMPT = """
You are an executive resume coach and ATS optimization specialist.
Re-frame the candidate's existing project/experience bullet point into a high-impact Google XYZ-style resume bullet:
"Accomplished [X] as measured by [Y], by doing [Z]"

CRITICAL RULES (VERY IMPORTANT):
1. Use strong industry action verbs (e.g. Architected, Streamlined, Engineered, Spearheaded, Accelerated).
2. DO NOT INVENT FAKE NUMBERS OR FABRICATED PERCENTAGES.
3. If specific metrics are missing in the original text, YOU MUST INSERT CLEAR PLACEHOLDERS like [X%], [N ms], [Count], or [$Amount] so the candidate can fill in their verified numbers.
4. Return strictly valid JSON matching this schema:
{
  "rewritten_text": "Architected [Z] using [Tech], reducing latency by [X%] and supporting [Count] daily active users.",
  "action_verbs_used": ["Architected", "Reducing"],
  "metrics_to_fill": ["[X%]", "[Count]"],
  "explanation": "Brief explanation of why this phrasing performs better with recruiters and ATS scanners."
}
Do NOT output markdown backticks. Return only raw JSON.
"""

def fallback_rewrite_project(original_text: str, target_skills: List[str]) -> RewriteProjectResponse:
    """Fallback rewriter inserting explicit [X%] metric placeholders."""
    clean_orig = original_text.strip().rstrip(".")
    skill_mention = f" utilizing {target_skills[0]}" if target_skills else ""

    # Choose strong action verb
    action_verb = "Spearheaded"
    if any(w in clean_orig.lower() for w in ["build", "develop", "engineer", "create"]):
        action_verb = "Architected"
    elif any(w in clean_orig.lower() for w in ["improve", "optimiz", "streamline", "fast"]):
        action_verb = "Streamlined"
    elif any(w in clean_orig.lower() for w in ["coordinate", "manage", "deploy"]):
        action_verb = "Orchestrated"

    rewritten = (
        f"{action_verb} {clean_orig.lower()}{skill_mention}, "
        f"improving process efficiency by [X%] and reducing deliverable turnaround time by [N] hours across [Count] milestones."
    )

    return RewriteProjectResponse(
        rewritten_text=rewritten,
        action_verbs_used=[action_verb, "Streamlined"],
        metrics_to_fill=["[X%]", "[N] hours", "[Count]"],
        explanation="Re-framed with a strong industry action verb and structured impact placeholders (XYZ format) to maximize ATS parseability without inventing unverified numbers."
    )

def rewrite_project_bullet(
    original_text: str,
    target_role: str = "Software Engineer",
    company_type: str = "mid_size_product",
    target_skills: List[str] = None
) -> RewriteProjectResponse:
    """Re-frames experience bullet with strong action verbs and [X%] metric placeholders."""
    target_skills = target_skills or []
    cache_key = f"rewrite_{get_hash(original_text)}_{','.join(target_skills)}"

    if cache_key in _LLM_CACHE:
        return RewriteProjectResponse(**_LLM_CACHE[cache_key])

    client = get_gemini_client()
    if not client:
        result = fallback_rewrite_project(original_text, target_skills)
        _LLM_CACHE[cache_key] = result.model_dump()
        return result

    skills_context = f"Target Skills to Incorporate (if relevant): {', '.join(target_skills)}" if target_skills else ""
    prompt = (
        f"Original Resume Bullet/Project:\n\"{original_text}\"\n\n"
        f"Target Role: {target_role}\n"
        f"Company Type: {company_type}\n"
        f"{skills_context}\n\n"
        "Re-frame this bullet into an ATS-friendly, metric-driven statement with [X%] placeholders for unverified numbers."
    )

    for attempt in range(2):
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=REWRITE_SYSTEM_PROMPT,
                    response_mime_type="application/json",
                    temperature=0.2,
                )
            )

            resp_text = response.text.strip()
            if resp_text.startswith("```"):
                resp_text = re.sub(r"^```(?:json)?|```$", "", resp_text, flags=re.MULTILINE).strip()

            parsed = json.loads(resp_text)
            result = RewriteProjectResponse(**parsed)
            _LLM_CACHE[cache_key] = result.model_dump()
            return result

        except Exception as e:
            print(f"[SkillBridge] Bullet rewrite LLM call attempt {attempt+1} failed: {e}")
            time.sleep(1)

    result = fallback_rewrite_project(original_text, target_skills)
    _LLM_CACHE[cache_key] = result.model_dump()
    return result

# -------------------------------------------------------------
# 3. One-Click ATS Resume Bullet Generator
# -------------------------------------------------------------

BULLET_SYSTEM_PROMPT = """
You are an expert technical resume writer.
Generate 2 to 3 distinct, ATS-optimized, high-impact resume bullet options demonstrating hands-on experience with the given skill.
Each bullet MUST:
1. Begin with a powerful past-tense action verb (e.g., Architected, Spearheaded, Implemented, Automated).
2. Incorporate realistic technical context.
3. Use clear bracketed placeholders for metrics like [X%], [N], or [Count] — DO NOT invent fake numbers.

Return strictly valid JSON:
{
  "skill": "Docker",
  "bullet_options": [
    "Containerized [Service/Application] using Docker and Docker Compose, reducing local onboarding setup time by [X%] across a team of [N] developers.",
    "Architected multi-stage Docker production builds for microservices, reducing final container image footprints by [X%] and accelerating deployment cycle by [N] minutes."
  ]
}
Do NOT output markdown backticks. Return only raw JSON.
"""

def fallback_generate_bullets(skill: str, role_context: str) -> List[str]:
    """Generates ATS bullets using high-performing structural templates across domains."""
    clean_role = role_context.lower()
    is_hardware = any(k in clean_role for k in ["electr", "embed", "hardware", "vlsi", "pcb", "robot", "firmware", "circuit", "mechanical", "rf", "telecom"])
    is_software = any(k in clean_role for k in ["software", "backend", "frontend", "full stack", "cloud", "devops", "data"])

    if is_hardware:
        return [
            f"Designed and validated {skill}-driven architectures for {role_context.lower()} applications, reducing power dissipation by [X%] and achieving [99.9%] operational reliability.",
            f"Spearheaded implementation of {skill} across subsystem interfaces, cutting debugging cycle time by [X%] and verifying hardware-in-the-loop stability across [Count] test bench iterations.",
            f"Optimized signal integrity and execution throughput utilizing {skill}, meeting strict timing constraints within [N] ns and lowering bill of materials (BOM) cost by [X%]."
        ]
    elif is_software:
        return [
            f"Architected and deployed {skill}-based infrastructure for {role_context.lower()} workflows, improving process throughput by [X%] and achieving [99.9%] uptime.",
            f"Spearheaded implementation of {skill} across core modules, reducing pipeline execution latency by [X%] and decreasing automated regression errors by [Count]%.",
            f"Streamlined cross-functional service integration utilizing {skill}, enabling [N] simultaneous requests while optimizing server resource utilization by [X%]."
        ]
    else:
        # Universal professional template (Healthcare, Business, Finance, Marketing, HR, Operations, Education, Legal)
        return [
            f"Spearheaded implementation of {skill} initiatives for {role_context.lower()} deliverables, driving a [X%] improvement in outcome metrics across [Count] team projects.",
            f"Streamlined cross-functional workflows utilizing {skill}, reducing turnaround time by [X%] while maintaining [99.9%] accuracy and quality compliance.",
            f"Delivered key operational milestones leveraging {skill}, supporting [Count] stakeholders and generating [X%] operational efficiency improvements."
        ]

def generate_resume_bullets(skill: str, role_context: str = "Software Engineer") -> GenerateBulletResponse:
    """Generates 2-3 tailored ATS resume bullet variations for a skill."""
    cache_key = f"bullet_{skill.lower()}_{role_context.lower()}"
    if cache_key in _LLM_CACHE:
        return GenerateBulletResponse(**_LLM_CACHE[cache_key])

    client = get_gemini_client()
    if not client:
        bullets = fallback_generate_bullets(skill, role_context)
        resp = GenerateBulletResponse(skill=skill, bullet_options=bullets)
        _LLM_CACHE[cache_key] = resp.model_dump()
        return resp

    prompt = f"Skill: {skill}\nTarget Role Context: {role_context}\nGenerate 2-3 ATS resume bullet options."

    for attempt in range(2):
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=BULLET_SYSTEM_PROMPT,
                    response_mime_type="application/json",
                    temperature=0.3,
                )
            )

            resp_text = response.text.strip()
            if resp_text.startswith("```"):
                resp_text = re.sub(r"^```(?:json)?|```$", "", resp_text, flags=re.MULTILINE).strip()

            parsed = json.loads(resp_text)
            resp = GenerateBulletResponse(**parsed)
            _LLM_CACHE[cache_key] = resp.model_dump()
            return resp

        except Exception as e:
            print(f"[SkillBridge] Bullet generator LLM attempt {attempt+1} failed: {e}")
            time.sleep(1)

    bullets = fallback_generate_bullets(skill, role_context)
    resp = GenerateBulletResponse(skill=skill, bullet_options=bullets)
    _LLM_CACHE[cache_key] = resp.model_dump()
    return resp
