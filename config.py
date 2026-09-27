from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
import os

load_dotenv()


def _require(key: str) -> str:
    value = os.getenv(key)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {key}")
    return value


@dataclass
class Config:
    hammerhead_client_id: str
    hammerhead_client_secret: str
    hammerhead_username: str
    hammerhead_password: str
    garmin_username: str
    garmin_password: str
    garmin_tokenstore: Path = field(default_factory=lambda: Path("garmin_tokens"))
    state_file: Path = field(default_factory=lambda: Path("sync_state.json"))
    data_dir: Path = field(default_factory=lambda: Path("data"))
    sync_from_date: datetime | None = None


def _parse_date(value: str) -> datetime:
    return datetime.strptime(value, "%Y-%m-%d").replace(tzinfo=timezone.utc)


def load_config() -> Config:
    raw_date = os.getenv("SYNC_FROM_DATE")
    return Config(
        hammerhead_client_id=_require("HAMMERHEAD_CLIENT_ID"),
        hammerhead_client_secret=_require("HAMMERHEAD_CLIENT_SECRET"),
        hammerhead_username=_require("HAMMERHEAD_USERNAME"),
        hammerhead_password=_require("HAMMERHEAD_PASSWORD"),
        garmin_username=_require("GARMIN_USERNAME"),
        garmin_password=_require("GARMIN_PASSWORD"),
        garmin_tokenstore=Path(os.getenv("GARMIN_TOKENSTORE", "garmin_tokens")),
        state_file=Path(os.getenv("SYNC_STATE_FILE", "sync_state.json")),
        data_dir=Path(os.getenv("DATA_DIR", "data")),
        sync_from_date=_parse_date(raw_date) if raw_date else None,
    )
