"""
Embedding and semantic similarity service for SkillBridge.
Uses sentence-transformers ('all-MiniLM-L6-v2') to compute dense vector embeddings
and cosine similarity between JD requirements and candidate resume skills.
"""

import os
from typing import List, Tuple, Optional, Dict
import numpy as np

# Suppress HuggingFace symlink warning and prevent online blocking on Windows
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from app.config import settings

# Global singleton instance for the sentence transformer model
_MODEL_INSTANCE: Optional[SentenceTransformer] = None

# Cache for computed skill embeddings (skill string -> 1D numpy vector)
_EMBEDDING_CACHE: Dict[str, np.ndarray] = {}

# Common tech alias / ecosystem mappings for immediate high-confidence resolution across engineering disciplines
COMMON_ALIASES = {
    # Electronics, ECE, Embedded & Hardware
    "verilog": ["systemverilog", "vhdl", "hdl", "fpga", "vlsi", "digital design"],
    "systemverilog": ["verilog", "uvm", "vhdl", "fpga", "vlsi"],
    "vhdl": ["verilog", "systemverilog", "hdl", "fpga", "digital design"],
    "embedded c": ["c", "c++", "microcontrollers", "firmware", "embedded systems"],
    "embedded c++": ["c++", "embedded c", "microcontrollers", "firmware"],
    "altium": ["altium designer", "pcb design", "schematic design", "eda", "kicad"],
    "altium designer": ["altium", "pcb design", "schematic design", "kicad"],
    "kicad": ["altium", "pcb design", "eda", "schematic"],
    "arm": ["arm cortex", "arm cortex-m", "stm32", "microcontrollers", "embedded systems"],
    "arm cortex": ["arm", "stm32", "microcontrollers", "embedded c"],
    "stm32": ["arm", "arm cortex", "microcontrollers", "embedded c"],
    "matlab": ["simulink", "dsp", "signal processing"],
    "simulink": ["matlab", "control systems", "modeling"],
    "i2c": ["spi", "uart", "serial communication", "protocols"],
    "spi": ["i2c", "uart", "serial communication"],
    "uart": ["i2c", "spi", "serial communication"],
    "can": ["can bus", "automotive protocols", "serial communication"],
    "can bus": ["can", "automotive protocols", "embedded systems"],
    "pcb": ["pcb design", "hardware design", "schematics"],
    "pcb design": ["altium", "kicad", "circuit design", "hardware"],
    "rtos": ["freertos", "real-time operating system", "embedded systems"],
    "freertos": ["rtos", "embedded systems", "firmware"],
    "vlsi": ["asic", "fpga", "digital design", "verilog", "semiconductor"],
    "fpga": ["verilog", "vhdl", "xilinx", "vivado", "quartus", "digital design"],

    # Mechanical & Core Engineering
    "cad": ["solidworks", "autocad", "catia", "3d modeling"],
    "solidworks": ["cad", "3d modeling", "catia", "ansys"],
    "autocad": ["cad", "drafting", "solidworks"],

    # Software & Web
    "react.js": ["react", "reactjs", "javascript"],
    "react": ["react.js", "reactjs", "javascript"],
    "node.js": ["node", "nodejs", "javascript"],
    "node": ["node.js", "nodejs", "javascript"],
    "fastapi": ["python", "python backend"],
    "django": ["python", "python backend"],
    "flask": ["python", "python backend"],
    "postgres": ["postgresql", "sql", "relational database"],
    "postgresql": ["postgres", "sql", "relational database"],
    "mysql": ["sql", "relational database"],
    "ts": ["typescript", "javascript"],
    "typescript": ["ts", "javascript"],
    "js": ["javascript"],
    "k8s": ["kubernetes", "devops", "container orchestration"],
    "kubernetes": ["k8s", "devops", "container orchestration"],
    "docker": ["containers", "devops"],
}

def get_embedding_model() -> SentenceTransformer:
    """
    Lazy-loads the SentenceTransformer model on first invocation.
    Loading once into RAM avoids repeated latency on subsequent requests.
    """
    global _MODEL_INSTANCE
    if _MODEL_INSTANCE is None:
        print(f"[SkillBridge] Loading semantic embedding model: {settings.embedding_model_name}...")
        _MODEL_INSTANCE = SentenceTransformer(settings.embedding_model_name)
        print("[SkillBridge] Semantic embedding model loaded successfully.")
    return _MODEL_INSTANCE

def embed_text(text: str) -> np.ndarray:
    """
    Computes and caches the normalized dense vector embedding for a skill text.
    """
    clean_text = text.strip().lower()
    if clean_text in _EMBEDDING_CACHE:
        return _EMBEDDING_CACHE[clean_text]

    model = get_embedding_model()
    # Normalize embedding vector so cosine similarity equals the dot product
    vector = model.encode(clean_text, normalize_embeddings=True)
    _EMBEDDING_CACHE[clean_text] = vector
    return vector

def find_best_semantic_match(jd_skill: str, resume_skills: List[str]) -> Tuple[float, Optional[str]]:
    """
    Finds the candidate skill in the resume that has the highest semantic similarity to the JD requirement.

    WHAT:
    1. Checks for exact or near-exact string match (e.g. 'Python' vs 'Python 3' -> 0.95+).
    2. Checks tech ecosystem aliases (e.g. 'React.js' ~ 'JavaScript' -> 0.85).
    3. Calculates cosine similarity across dense vector embeddings for all candidate skills.
    4. Returns the highest score and best matching candidate skill name.

    WHY:
    Enables true semantic understanding beyond raw keyword matching (e.g., matching 'React.js' to 'JavaScript',
    'PostgreSQL' to 'Relational Databases', or 'FastAPI' to 'Python Backend').
    """
    if not resume_skills:
        return (0.0, None)

    clean_jd = jd_skill.strip().lower()

    # 1. Exact or near-exact string match
    for res_skill in resume_skills:
        clean_res = res_skill.strip().lower()
        if clean_jd == clean_res:
            return (1.0, res_skill)
        # Check simple variations like 'Python' vs 'Python 3' or 'Docker' vs 'Docker CE'
        if (clean_jd in clean_res or clean_res in clean_jd) and abs(len(clean_jd) - len(clean_res)) <= 3:
            return (0.95, res_skill)

    # 2. Check curated technology alias map for instant high-confidence matching
    if clean_jd in COMMON_ALIASES:
        for res_skill in resume_skills:
            if res_skill.strip().lower() in COMMON_ALIASES[clean_jd]:
                return (0.85, res_skill)

    # 3. Dense vector embedding cosine similarity
    jd_vector = embed_text(jd_skill)
    res_vectors = [embed_text(s) for s in resume_skills]

    similarities = cosine_similarity([jd_vector], res_vectors)[0]

    best_idx = int(np.argmax(similarities))
    best_score = float(similarities[best_idx])
    best_match_skill = resume_skills[best_idx]

    # Bound score between 0.0 and 1.0
    best_score = max(0.0, min(1.0, round(best_score, 3)))
    return (best_score, best_match_skill)
