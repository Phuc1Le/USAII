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
