"""
Convenience launcher for the SkillBridge backend.
Allows the beginner developer to simply run:
    python run.py
from the backend directory.
"""

import uvicorn
from app.config import settings

if __name__ == "__main__":
    print(f"Starting SkillBridge Backend on http://{settings.backend_host}:{settings.backend_port}")
    uvicorn.run(
        "app.main:app",
        host=settings.backend_host,
        port=settings.backend_port,
        reload=True
    )
