"""
RAGForge — Cloud Entrypoint for Hugging Face Spaces (Gradio SDK)

Serves the Next.js static UI and FastAPI backend with SSE streaming,
Sentence-Transformers embeddings, Cross-Encoder reranker, and Neon Postgres.
"""

import os
import sys
from pathlib import Path

# Initialize spaces module first if on ZeroGPU
try:
    import spaces
except Exception:
    pass

# Add backend directory to sys.path
backend_path = Path(__file__).resolve().parent / "backend"
sys.path.insert(0, str(backend_path))

# If app.py is loaded as a module named 'app', temporarily unregister it so 'import app.main' finds backend/app
current_app_module = sys.modules.pop("app", None)

try:
    from app.main import app
finally:
    if current_app_module is not None:
        sys.modules["__space_app__"] = current_app_module

import uvicorn

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    uvicorn.run(app, host="0.0.0.0", port=port)
