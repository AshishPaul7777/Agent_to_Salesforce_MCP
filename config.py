import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY: str = os.environ["GEMINI_API_KEY"]
OPENWEATHER_API_KEY: str = os.environ["OPENWEATHER_API_KEY"]
CHROMA_PERSIST_DIR: str = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")

PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "data"
MCP_SERVER_SCRIPT = str(PROJECT_ROOT / "mcp_server" / "server.py")

GEMINI_LLM_MODEL = os.environ["GEMINI_LLM_MODEL"]
GEMINI_FALLBACK_MODEL = os.getenv("GEMINI_FALLBACK_MODEL", "gemini-2.0-flash-lite")
GEMINI_EMBED_MODEL = os.environ["GEMINI_EMBED_MODEL"]
RAG_RELEVANCE_THRESHOLD = float(os.getenv("RAG_RELEVANCE_THRESHOLD", "0.75"))
