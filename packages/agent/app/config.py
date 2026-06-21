from pathlib import Path

from dotenv import load_dotenv


ROOT_DIR = Path(__file__).resolve().parents[1]

load_dotenv(ROOT_DIR / ".env")
load_dotenv()

GEMINI_API_KEY = ""
GEMINI_MODEL = "gemini-2.5-flash"
CHAT_HISTORY_LIMIT = 20
CLARITY_THRESHOLD = 0.7
CHAT_SUMMARY_TRIGGER = 6
CHAT_SUMMARY_KEEP = 3
CHAT_SUMMARY_RE_EVERY = 2


def _int_from_env(name: str, default: int) -> int:
    import os

    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError as exc:
        raise RuntimeError(f"{name} must be an integer") from exc


def _float_from_env(name: str, default: float) -> float:
    import os

    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        return float(raw)
    except ValueError as exc:
        raise RuntimeError(f"{name} must be a number") from exc


def _load_settings() -> None:
    import os
    import sys

    global GEMINI_API_KEY, GEMINI_MODEL, CHAT_HISTORY_LIMIT, CLARITY_THRESHOLD
    global CHAT_SUMMARY_TRIGGER, CHAT_SUMMARY_KEEP, CHAT_SUMMARY_RE_EVERY

    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
    if not GEMINI_API_KEY and "pytest" not in sys.modules:
        raise RuntimeError("GEMINI_API_KEY is required to start the agent service")

    GEMINI_MODEL = os.environ.get("GEMINI_MODEL", GEMINI_MODEL)
    CHAT_HISTORY_LIMIT = _int_from_env("CHAT_HISTORY_LIMIT", CHAT_HISTORY_LIMIT)
    CLARITY_THRESHOLD = _float_from_env("CLARITY_THRESHOLD", CLARITY_THRESHOLD)
    CHAT_SUMMARY_TRIGGER = _int_from_env("CHAT_SUMMARY_TRIGGER", CHAT_SUMMARY_TRIGGER)
    CHAT_SUMMARY_KEEP = _int_from_env("CHAT_SUMMARY_KEEP", CHAT_SUMMARY_KEEP)
    CHAT_SUMMARY_RE_EVERY = _int_from_env("CHAT_SUMMARY_RE_EVERY", CHAT_SUMMARY_RE_EVERY)


_load_settings()
