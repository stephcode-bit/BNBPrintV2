"""
Runner scoring + combined security scoring.

Two separate 0-100 scores are produced per token:

  security_score  — "is this likely safe to interact with at all"
                     (honeypot risk, LP lock, renounced owner, holder
                     concentration, Ave AI's own score if available).

  runner_score     — "is this likely to pump before/around bonding
                      completion" (buy volume, holder growth rate, bonding
                      speed, market cap sanity, security as a gate).

Both are intentionally simple, transparent, weighted-sum models rather
than a black box — tune the WEIGHTS dicts as you gather real outcome data.
A token is only ever flagged `is_runner=True` if it also clears the
security bar, so a hyped-but-unsafe token is never surfaced as a "runner".
"""
from dataclasses import dataclass
from typing import Optional

from app.config import get_settings

settings = get_settings()


@dataclass
class ScoringInputs:
    # Security signals
    ave_security_score: Optional[float]
    honeypot_risk: Optional[bool]
    liquidity_locked: bool
    owner_renounced: bool
    mint_disabled: bool
    contract_verified: Optional[bool]
    top10_holder_pct: Optional[float]
    buy_tax_pct: float
    sell_tax_pct: float

    # Runner signals
    volume_24h_usd: float
    liquidity_usd: float
    market_cap_usd: float
    holder_count: int
    holder_growth_per_hour: float  # new holders/hour, caller computes from history
    bonding_progress_pct: float
    bonding_speed_pct_per_hour: float  # how fast progress is climbing
    age_minutes: float


def compute_security_score(i: ScoringInputs) -> float:
    if i.honeypot_risk is True:
        return 0.0  # hard fail — never let a confirmed honeypot score above 0

    score = 50.0  # neutral baseline when signals are missing

    if i.ave_security_score is not None:
        score = i.ave_security_score
    else:
        score = 50.0

    if i.liquidity_locked:
        score += 15
    else:
        score -= 15

    if i.owner_renounced:
        score += 10
    else:
        score -= 5

    if i.mint_disabled:
        score += 5

    if i.contract_verified:
        score += 5

    if i.top10_holder_pct is not None:
        if i.top10_holder_pct > 70:
            score -= 25
        elif i.top10_holder_pct > 50:
            score -= 12
        elif i.top10_holder_pct < 20:
            score += 5

    total_tax = (i.buy_tax_pct or 0) + (i.sell_tax_pct or 0)
    if total_tax > 20:
        score -= 20
    elif total_tax > 10:
        score -= 8

    return max(0.0, min(100.0, round(score, 1)))


def compute_runner_score(i: ScoringInputs, security_score: float) -> float:
    """Weighted-sum heuristic. Security acts as a gate: below
    MIN_SECURITY_SCORE, the runner score is capped hard regardless of hype,
    since a "runner" that's also a honeypot isn't a runner worth surfacing.
    """
    if security_score < settings.min_security_score:
        return min(security_score, 20.0)

    score = 0.0

    # Volume relative to liquidity — high turnover vs. pool size suggests
    # real demand rather than a thin, easily-manipulated pool.
    if i.liquidity_usd > 0:
        turnover = i.volume_24h_usd / i.liquidity_usd
        score += min(25.0, turnover * 10)

    # Holder growth rate — organic interest accelerating.
    score += min(20.0, i.holder_growth_per_hour * 2)

    # Bonding speed — climbing toward completion quickly, without having
    # just launched in the last couple of minutes (avoids sniping noise).
    if i.age_minutes > 2:
        score += min(20.0, i.bonding_speed_pct_per_hour / 2)

    # Sane market cap band — very low mcap can be too illiquid/manipulable,
    # extremely high mcap this early is often already-diluted.
    if 5_000 <= i.market_cap_usd <= 500_000:
        score += 15
    elif i.market_cap_usd < 5_000:
        score += 5

    # Absolute holder count as a floor signal.
    score += min(10.0, i.holder_count / 10)

    # Bonding progress sweet spot: still bonding, but with real traction
    # (not 1%, not already migrated).
    if 15 <= i.bonding_progress_pct < 95:
        score += 10

    return max(0.0, min(100.0, round(score, 1)))


def is_runner(runner_score: float) -> bool:
    return runner_score >= settings.runner_score_threshold
