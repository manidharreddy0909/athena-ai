"""
Pytest configuration: ensures the backend .env is loaded before any test,
and adds backend/ to sys.path so imports like `from core.llm import ...` work.
"""
import os
import sys
from pathlib import Path

# Add backend to Python path
BACKEND_DIR = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))

# Load .env from backend directory before any test module imports config
from dotenv import load_dotenv
load_dotenv(BACKEND_DIR / ".env", override=True)
