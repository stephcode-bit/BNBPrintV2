"""
Central application settings, loaded from environment variables / .env.

Everything defaults to safe, demo-friendly values so the service boots and
is fully explorable with zero external credentials. Flip DEMO_MODE=false
once real RPC + Ave AI keys and verified factory addresses are in place.
"""
from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # App
    app_name: str = "BNBPRINT"
    env: str = "development"
    demo_mode: bool = True
    cors_origins: str = "http://localhost:3000"

    # Database
    database_url: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/bnbprint"

    # Chain
    rpc_wss_url: str = ""
    rpc_https_url: str = ""
    chain_id: int = 56

    # Ave AI
    ave_ai_api_key: str = ""
    ave_ai_base_url: str = "https://prod.ave-api.com/v2"

    # GoPlus Security (real honeypot/tax/LP-lock simulator — works keyless
    # at a lower rate limit; app key/secret optional for higher volume)
    goplus_app_key: str = ""
    goplus_app_secret: str = ""

    # Factories
    pancakeswap_v2_factory: str = "0xcA143Ce32Fe78f1f7019d7d551a6402fC5350c73"
    pancakeswap_v3_factory: str = "0x0BFbCF9fa4f9C56B0F40a671Ad40E0805A091865"
    four_meme_factory: str = ""
    grafun_factory: str = ""
    extra_bonding_factories: str = ""

    # Scoring
    runner_score_threshold: int = 70
    min_security_score: int = 50

    # Push
    vapid_public_key: str = ""
    vapid_private_key: str = ""
    vapid_subject: str = "mailto:you@example.com"

    # Infra (legacy always-on path — unused by the default $0/month
    # GitHub Actions + Upstash setup, kept for anyone who does want to
    # self-host the old always-on FastAPI+Postgres version later)
    redis_url: str = ""

    # Upstash Redis (REST API) — the default state store for scan_runner.py
    # and the frontend's Next.js API routes. Free tier: 500K commands/month,
    # 256MB, no sleep, no card. Get these from your Upstash database's
    # "REST API" tab after creating a free database at upstash.com.
    upstash_redis_rest_url: str = ""
    upstash_redis_rest_token: str = ""

    bonding_refresh_interval: int = 45
    stale_token_cleanup_hours: int = 72

    # scan_runner.py loop tuning — see .github/workflows/scanner.yml
    scan_poll_interval_seconds: int = 15
    scan_loop_budget_seconds: int = 20_700  # 5h45m; leaves a safety margin
    # under the ~5h cron restart cadence and GitHub's 6h hard job cap.

    @property
    def cors_origin_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def bonding_factories(self) -> dict:
        """Map of platform_name -> factory address, built from settings."""
        factories = {}
        if self.four_meme_factory:
            factories["four.meme"] = self.four_meme_factory
        if self.grafun_factory:
            factories["grafun"] = self.grafun_factory
        for pair in self.extra_bonding_factories.split(","):
            if ":" in pair:
                name, addr = pair.split(":", 1)
                factories[name.strip()] = addr.strip()
        return factories


@lru_cache
def get_settings() -> Settings:
    return Settings()
