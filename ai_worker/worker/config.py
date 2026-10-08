from __future__ import annotations
import os
from dataclasses import dataclass
from dotenv import load_dotenv
load_dotenv()

def csv_set(name: str, default: str = "") -> set[str]:
    return {x.strip().lower() for x in os.getenv(name, default).split(",") if x.strip()}

@dataclass(frozen=True)
class Settings:
    market_base_url: str = os.getenv("MARKET_BASE_URL", "https://market.near.ai").rstrip("/")
    market_api_key: str = os.getenv("MARKET_API_KEY", "")
    enable_autonomy: bool = os.getenv("ENABLE_AUTONOMY", "false").lower() == "true"
    dry_run: bool = os.getenv("DRY_RUN", "true").lower() == "true"
    max_bids_per_run: int = int(os.getenv("MAX_BIDS_PER_RUN", "1"))
    min_score: float = float(os.getenv("MIN_SCORE", "55"))
    min_reward_near: float = float(os.getenv("MIN_REWARD_NEAR", "2"))
    min_hourly_target_usd: float = float(os.getenv("MIN_HOURLY_TARGET_USD", "2"))
    usd_per_near_estimate: float = float(os.getenv("USD_PER_NEAR_ESTIMATE", "3"))
    poll_seconds: int = int(os.getenv("POLL_SECONDS", "900"))
    allowed_tags: set[str] = None  # type: ignore
    required_keywords: set[str] = None  # type: ignore

    def __post_init__(self):
        object.__setattr__(self, "allowed_tags", csv_set("ALLOWED_TAGS", "python,api,github,documentation,research,data,automation"))
        object.__setattr__(self, "required_keywords", csv_set("REQUIRED_KEYWORDS", "python,api,docs,research,data,automation"))

SETTINGS = Settings()
