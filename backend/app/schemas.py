from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class TokenOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    address: str
    symbol: str
    name: str
    decimals: int

    pair_address: Optional[str] = None
    factory: Optional[str] = None
    dex: Optional[str] = None

    creation_block: Optional[int] = None
    creation_timestamp: datetime

    bonding_platform: Optional[str] = None
    bonding_progress: float
    is_bonding: bool
    migrated_at: Optional[datetime] = None

    liquidity_usd: float
    liquidity_locked: bool
    market_cap_usd: float
    price_usd: float
    volume_24h_usd: float
    holder_count: int
    top10_holder_pct: float

    owner_renounced: bool
    mint_disabled: bool
    contract_verified: bool

    honeypot_risk: Optional[bool] = None
    buy_tax_pct: float
    sell_tax_pct: float

    ave_security_score: Optional[float] = None
    security_score: float
    runner_score: float
    is_runner: bool

    last_checked_at: datetime
    created_at: datetime


class TokenListResponse(BaseModel):
    items: list[TokenOut]
    total: int
    limit: int
    offset: int


class BookmarkCreate(BaseModel):
    token_address: str = Field(..., min_length=42, max_length=42)
    user_id: str = Field(..., min_length=1, max_length=128)
    note: Optional[str] = Field(default=None, max_length=280)


class BookmarkOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    token_address: str
    note: Optional[str] = None
    created_at: datetime
    token: Optional[TokenOut] = None


class AlertOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    token_address: str
    alert_type: str
    message: str
    created_at: datetime


class StatsOut(BaseModel):
    total_tokens: int
    bonding_tokens: int
    migrated_tokens: int
    runners_24h: int
    avg_security_score: float
    last_token_at: Optional[datetime] = None


class PushSubscriptionIn(BaseModel):
    user_id: str
    endpoint: str
    p256dh: str
    auth: str
