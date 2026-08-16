import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./app.db")
AGENT_URL = os.environ.get("AGENT_URL", "http://localhost:8001")
USE_MOCK_AGENT = os.environ.get("USE_MOCK_AGENT", "").lower() == "true"
CHAT_SUMMARY_TRIGGER = int(os.environ.get("CHAT_SUMMARY_TRIGGER", "6"))
CHAT_SUMMARY_KEEP = int(os.environ.get("CHAT_SUMMARY_KEEP", "3"))
CHAT_SUMMARY_RE_EVERY = int(os.environ.get("CHAT_SUMMARY_RE_EVERY", "2"))
DECISION_SEARCH_MIN_SCORE = float(os.environ.get("DECISION_SEARCH_MIN_SCORE", "0.5"))

# Comma-separated list of browser origins allowed to call this API. The default
# covers a local Vite dev server; a deployed frontend must be added here.
ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get(
        "ALLOWED_ORIGINS",
        "http://localhost:5173,http://localhost:5174,http://127.0.0.1:5173,http://127.0.0.1:5174",
    ).split(",")
    if origin.strip()
]

# Shared secret the agent service sends on /internal/* calls. Those routes expose
# project data with no user check, so they must not be reachable from the internet.
# Empty means "not configured" — the routes stay open and startup logs a warning,
# so local development keeps working without extra setup.
INTERNAL_API_TOKEN = os.environ.get("INTERNAL_API_TOKEN", "")
