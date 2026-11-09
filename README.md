# 🌉 SkillBridge: AI-Powered Career Guidance Platform

> **Bridging the gap between your resume and your target job description with actionable, transparent intelligence.**

SkillBridge is a modern web application designed to eliminate arbitrary, unexplained resume scores. Instead of a black-box percentage, it uses semantic NLP (`sentence-transformers` + cosine similarity) and LLM-assisted analysis (Google Gemini API) to compare a candidate's resume against a specific target Job Description (JD). It provides:

- 🎯 **Prioritized Skill Gaps** (Strong Match, Underrepresented, Missing).
- 👔 **Recruiter-Style Rejection Explanations** linked directly to resume evidence.
- 🏢 **Company Culture & Tech Stack Context Engine** (Startup, Mid-Size Product, Big Tech, Enterprise Bank, Consulting).
- 📈 **Predictive Match Uplift Simulator** with real-time before/after score recalculation.
- 🗺️ **Impact-Ranked Learning Roadmap** (Curriculum ordered by score impact vs. learning effort).
- ✍️ **Targeted Experience & Project Re-Framer** (Google XYZ format with `[X%]` metric placeholders; no fake numbers).
- ⚡ **One-Click ATS Resume Bullet Generator** (2-3 tailored bullet options with bracketed placeholders).
- 💰 **Salary Insights & 5-Year Career Growth Projections** (Supporting USD and INR with skill premiums).
- 🔒 **Privacy-First Data Retention** (One-click session purging and complete local SQLite wipe).

---

## 🏗️ System Architecture & Module Guide

```text
SkillBridge/
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI entry point, CORS, and route endpoints (/analyze, /simulate, etc.)
│   │   ├── config.py                # Environment configuration loaded from .env via Pydantic Settings
│   │   ├── models/
│   │   │   └── schemas.py           # Pydantic schemas validating all API request and response contracts
│   │   ├── services/
│   │   │   ├── parser_service.py    # Extracts & validates text from PDF (pdfplumber) and Word (python-docx)
│   │   │   ├── embedding_service.py # sentence-transformers (all-MiniLM-L6-v2) dense embeddings & cosine similarity
│   │   │   ├── scoring_service.py   # Deterministic alignment score & predictive uplift simulation engine
│   │   │   ├── gap_service.py       # Gap prioritization & recruiter rejection explanation generator
│   │   │   ├── rewriter_service.py  # Quantified XYZ project re-framer & one-click ATS bullet writer
│   │   │   ├── salary_service.py    # Benchmark salary ranges (USD/INR) & 1/3/5-year growth trajectory
│   │   │   └── llm_service.py       # Gemini API client with caching, retry logic & smart heuristic fallbacks
│   │   ├── data/
│   │   │   ├── company_profiles.json# Configurable weight profiles per company type (editable JSON)
│   │   │   └── salary_data.json     # Role benchmarks, skill premiums, and 5-year growth progressions
│   │   └── db/
│   │       └── database.py          # SQLite database storing analysis records with data purge support
│   ├── tests/
│   │   ├── test_scaffold.py         # Smoke tests for configuration and database schema
│   │   ├── test_parser.py           # Unit tests for text extraction, empty files & invalid formats
│   │   ├── test_scoring.py          # Unit tests for embeddings, thresholds, and company weights
│   │   ├── test_gaps.py             # Unit tests for gap ranking and recruiter rejection reasons
│   │   ├── test_simulator.py        # Unit tests for uplift calculation and API endpoint
│   │   ├── test_rewriter.py         # Unit tests for XYZ structure, [X%] placeholders, and bullet generator
│   │   ├── test_salary.py           # Unit tests for USD/INR currency calculations and role mapping
│   │   └── test_integration_analyze.py # End-to-end integration test of /api/analyze with mock DOCX
│   ├── requirements.txt             # Python dependencies
│   ├── .env.example                 # Environment variables template
│   └── run.py                       # One-line server launcher (`python run.py`)
├── frontend/
│   ├── src/
│   │   ├── api.js                   # Clean async client for all backend endpoints with friendly error handling
│   │   ├── App.jsx                  # Main application container, tab navigation & privacy controls
│   │   ├── components/              # Modular UI components:
│   │   │   ├── ScoreCard.jsx        # Circular progress score gauge with qualitative status badge
│   │   │   ├── CategoryBreakdown.jsx# Per-category progress bars with weights and raw scores
│   │   │   ├── SkillTag.jsx         # Status badge (Strong, Partial, Missing) with cosine match term
│   │   │   └── LoadingSpinner.jsx   # Animated loading indicator for AI operations
│   │   └── pages/                   # The 7 core pages/views:
│   │       ├── UploadPage.jsx       # Resume upload, JD input, company profile picker & Demo loader
│   │       ├── DashboardPage.jsx    # Overall score, category bars, requirements summary, filterable skills
│   │       ├── GapAnalysisPage.jsx  # Ranked skill gaps (#1, #2...) & recruiter rejection explanations
│   │       ├── SimulatorPage.jsx    # "I will learn skill X" interactive checkboxes with real-time uplift
│   │       ├── RoadmapPage.jsx      # Impact-vs-effort curriculum with one-click bullet generator
│   │       ├── RewriterPage.jsx     # Project re-framer with interactive [X%] placeholder customizer
│   │       └── SalaryGrowthPage.jsx # Benchmark compensation range (USD/INR), 5-yr growth, skill premiums
│   ├── package.json                 # Frontend dependencies (React 18, Vite, Tailwind CSS, Lucide)
│   ├── vite.config.js               # Vite config with backend proxy to localhost:8000
│   └── tailwind.config.js           # Tailwind CSS configuration with custom brand palette
└── README.md
```

---

## 🚀 Getting Started

### 1. Prerequisites
- **Python 3.10+** (Python 3.13 fully supported)
- **Node.js 18+** & **npm**

---

### 2. Backend Setup

1. **Navigate to the `backend/` folder:**
   ```bash
   cd backend
   ```

2. **Create and activate a virtual environment:**
   - **Windows:**
     ```powershell
     python -m venv .venv
     .\.venv\Scripts\activate
     ```
   - **macOS / Linux:**
     ```bash
     python3 -m venv .venv
     source .venv/bin/activate
     ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure your `.env` file:**
   Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
   *(Optional)*: Open `.env` and add your `GEMINI_API_KEY` from [Google AI Studio](https://aistudio.google.com/).
   > **Note:** SkillBridge includes built-in heuristic fallbacks, so **all features run seamlessly even without an external API key!**

5. **Start the backend server:**
   ```bash
   python run.py
   ```
   The backend will be running at `http://127.0.0.1:8000`. You can inspect interactive Swagger documentation at `http://127.0.0.1:8000/docs`.

---

### 3. Frontend Setup

1. **Open a separate terminal in the `frontend/` folder:**
   ```bash
   cd frontend
   ```

2. **Install frontend dependencies:**
   ```bash
   npm install
   ```

3. **Start the Vite development server:**
   ```bash
   npm run dev
   ```
   Open `http://localhost:5173` in your browser.

---

## 🧮 How the Scoring Engine Works

SkillBridge does **not** rely on simple keyword matching. It uses a **two-tier semantic evaluation engine**:

### Step 1: Semantic Embedding Match (Cosine Similarity)
Each requirement $i$ extracted from the Job Description is embedded using `sentence-transformers` (`all-MiniLM-L6-v2`) and compared against candidate skills in the resume:
$$S(i) = \max_j \frac{\mathbf{v}_i \cdot \mathbf{u}_j}{\|\mathbf{v}_i\| \|\mathbf{u}_j\|}$$

Requirements are classified into three configurable tiers:
- **Strong Match ($S(i) \ge 0.75$):** Score contribution $m_i = 1.0$ (e.g. *React.js* matches *JavaScript/React*).
- **Underrepresented ($0.50 \le S(i) < 0.75$):** Score contribution $m_i = S(i)$ (e.g. *FastAPI* partially matches *Flask*).
- **Missing ($S(i) < 0.50$):** Score contribution $m_i = 0.0$.

### Step 2: Unweighted Category Raw Score
For each category $C$ (Hard Skills, Tools & Tech, Domain Knowledge, Soft Skills, Experience):
$$R_C = \left( \frac{\sum_{i \in C} m_i}{|C|} \right) \times 100$$

### Step 3: Company Context Weight Engine
Weights ($W_C$, where $\sum W_C = 1.0$) are defined in `backend/app/data/company_profiles.json`:

| Category | Early-Stage Startup | Mid-Size Product | Big Tech | Enterprise / Bank | Consulting / Service |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Hard Skills** | 35% | 35% | 40% | 30% | 30% |
| **Tools & Tech** | 25% | 25% | 20% | 20% | 20% |
| **Domain Knowledge**| 20% | 15% | 15% | 30% | 15% |
| **Soft Skills** | 15% | 20% | 15% | 10% | 30% |
| **Experience / Edu** | 5% | 5% | 10% | 10% | 5% |

### Step 4: Overall Alignment Score
$$\text{Overall Score} = \sum_{C} \left( W_C \times R_C \right) \quad \in [0, 100]$$

### Step 5: Predictive Uplift Simulator
When the candidate toggles *"I will learn skill X"*, the skill transitions to Strong Match ($m_X = 1.0$) and the score is recalculated using the identical mathematical scoring function:
$$\Delta \text{Score} = \text{Simulated Score} - \text{Baseline Score}$$

---

## 🧪 Running Automated Tests

SkillBridge includes **28 comprehensive unit and integration tests** verifying parser edge cases, semantic embeddings, company weights, gap prioritization, uplift simulation, metric placeholder integrity, and salary calculations:

```bash
# From the project root with the virtual environment activated:
$env:PYTHONPATH="backend"; pytest backend/tests -v
```

All 28 tests pass with **0 failures and 0 warnings**.

---

## 🔒 Privacy & Data Retention

- **In-Memory Processing**: Resumes are parsed in memory and never written to permanent disk storage.
- **On-Demand Purging**: Users can purge their current session or permanently wipe all database records at any time using the **"Purge My Data"** button in the header or via `DELETE /api/data`.
