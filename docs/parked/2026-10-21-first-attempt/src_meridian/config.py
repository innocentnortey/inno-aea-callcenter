"""Runtime settings. Every value comes from the environment (.env locally, Railway variables in production)."""
from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")

ISSUED = ROOT / "docs" / "data" / "issued" / "meridian_dataset"
KB_DIR = ISSUED / "knowledge_base"
ISSUED_DB = ISSUED / "scheduling_db" / "meridian_scheduling.sqlite"
TRANSCRIPTIONS = ROOT / "data" / "kb_transcriptions"


@dataclass(frozen=True)
class Settings:
    var_dir: Path = Path(os.getenv("MERIDIAN_VAR_DIR", str(ROOT / "var")))
    llm_model: str = os.getenv("MERIDIAN_LLM_MODEL", "claude-sonnet-5-5")
    fast_model: str = os.getenv("MERIDIAN_FAST_MODEL", "claude-haiku-5-5")
    # The dataset's fixed "today" (dataset README). Never the server clock (audit C-9).
    today: date = date.fromisoformat(os.getenv("MERIDIAN_TODAY", "2026-10-16"))
    clock_time: time = time.fromisoformat(os.getenv("MERIDIAN_CLOCK_TIME", "10:00"))
    daily_spend_cap_usd: float = float(os.getenv("MERIDIAN_DAILY_SPEND_CAP_USD", "10"))
    staff_password: str = os.getenv("MERIDIAN_STAFF_PASSWORD", "demo-staff")
    admin_token: str = os.getenv("MERIDIAN_ADMIN_TOKEN", "")
    emergency_number: str = os.getenv("MERIDIAN_EMERGENCY_NUMBER", "(512) 555-0199")  # placeholder (OD-4 g)
    max_tool_iterations: int = int(os.getenv("MERIDIAN_MAX_TOOL_ITERATIONS", "8"))
    max_sessions_bookings: int = int(os.getenv("MERIDIAN_MAX_BOOKINGS_PER_SESSION", "3"))

    @property
    def db_path(self) -> Path:
        return self.var_dir / "meridian.sqlite"

    @property
    def checkpoint_path(self) -> Path:
        return self.var_dir / "checkpoints.sqlite"

    @property
    def index_dir(self) -> Path:
        return self.var_dir / "kb_index"


SETTINGS = Settings()


def now() -> datetime:
    """The configured 'now': the dataset's today at the configured clock time, plus any simulated offset."""
    from meridian import db

    offset_min = db.get_setting_int("sim_minutes_offset", 0)
    return datetime.combine(SETTINGS.today, SETTINGS.clock_time) + timedelta(minutes=offset_min)
