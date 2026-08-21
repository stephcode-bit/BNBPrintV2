import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)

from app.database import Base


def utcnow():
    return datetime.now(timezone.utc)


class Token(Base):
    __tablename__ = "tokens"

    address = Column(String(42), primary_key=True, index=True)
    symbol = Column(String(32), default="")
    name = Column(String(128), default="")
    decimals = Column(Integer, default=18)

    pair_address = Column(String(42), nullable=True, index=True)
    factory = Column(String(64), nullable=True)  # e.g. "pancakeswap_v2" | "four.meme" | "grafun"
    dex = Column(String(64), nullable=True)

    creation_block = Column(Integer, nullable=True)
    creation_timestamp = Column(DateTime(timezone=True), default=utcnow, index=True)

    bonding_platform = Column(String(64), nullable=True)  # null once it's a plain DEX pair
    bonding_progress = Column(Float, default=0.0)  # 0-100, 100 = migrated to DEX
    is_bonding = Column(Boolean, default=True, index=True)
    migrated_at = Column(DateTime(timezone=True), nullable=True)

    liquidity_usd = Column(Float, default=0.0)
    liquidity_locked = Column(Boolean, default=False)
    market_cap_usd = Column(Float, default=0.0)
    price_usd = Column(Float, default=0.0)
    volume_24h_usd = Column(Float, default=0.0)
    holder_count = Column(Integer, default=0)
    top10_holder_pct = Column(Float, default=0.0)

    owner_address = Column(String(42), nullable=True)
    owner_renounced = Column(Boolean, default=False)
    mint_disabled = Column(Boolean, default=False)
    contract_verified = Column(Boolean, default=False)

    honeypot_risk = Column(Boolean, nullable=True)  # null = not checked yet
    buy_tax_pct = Column(Float, default=0.0)
    sell_tax_pct = Column(Float, default=0.0)

    ave_security_score = Column(Float, nullable=True)
    ave_raw = Column(Text, nullable=True)  # cached JSON blob from Ave AI

    security_score = Column(Float, default=0.0, index=True)  # our combined 0-100 score
    runner_score = Column(Float, default=0.0, index=True)  # 0-100 "likely runner" score
    is_runner = Column(Boolean, default=False, index=True)

    last_checked_at = Column(DateTime(timezone=True), default=utcnow)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class Bookmark(Base):
    __tablename__ = "bookmarks"
    __table_args__ = (UniqueConstraint("user_id", "token_address", name="uq_bookmark_user_token"),)

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(128), index=True)  # anonymous device/session id from the frontend
    token_address = Column(String(42), ForeignKey("tokens.address"), index=True)
    note = Column(String(280), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    token_address = Column(String(42), ForeignKey("tokens.address"), index=True)
    alert_type = Column(String(32))  # "new_token" | "runner" | "bonding_complete" | "risk_flag"
    message = Column(String(500))
    created_at = Column(DateTime(timezone=True), default=utcnow, index=True)


class PushSubscription(Base):
    """Web Push subscriptions (standard PWA push, VAPID-based — no Firebase)."""

    __tablename__ = "push_subscriptions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(128), index=True)
    endpoint = Column(Text, unique=True)
    p256dh = Column(String(255))
    auth = Column(String(255))
    created_at = Column(DateTime(timezone=True), default=utcnow)
