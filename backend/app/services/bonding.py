"""
Bonding-curve progress reader.

Bonding-curve launchpads (four.meme, GraFun, pump.fun-style clones, etc.)
each expose progress slightly differently — some via a `getCurveProgress`
view, some by comparing raised-BNB to a target, some by reading the curve
contract's virtual reserves. Since exact ABIs differ per platform and
BNBPRINT needs to support "four.meme, GraFun, or similar" generically,
this module defines a small `BondingReader` interface and a couple of
best-effort implementations you can complete once you have the exact
verified ABI for each platform (grab it from the factory's BscScan page).

DEMO_MODE bypasses all of this and generates a synthetic progress curve so
the rest of the app has something real to render.
"""
import logging
import random
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

from web3 import Web3

from app.config import get_settings

logger = logging.getLogger("bnbprint.bonding")
settings = get_settings()


@dataclass
class BondingStatus:
    platform: str
    progress_pct: float  # 0-100
    is_bonding: bool  # False once migrated to the DEX
    raised_bnb: Optional[float] = None
    target_bnb: Optional[float] = None


class BondingReader(ABC):
    platform_name: str

    @abstractmethod
    def read(self, w3: Web3, token_address: str) -> Optional[BondingStatus]:
        ...


class FourMemeReader(BondingReader):
    """
    Real implementation — calls TokenManagerHelper3.getTokenInfo(token) on
    BSC, which four.meme provides specifically for reading bonding-curve
    state regardless of which TokenManager version the token uses. See
    app/services/four_meme.py's docstring for how this contract address
    and ABI were verified (two independent, cross-confirming sources).

    Progress is `funds / maxFunds` — `funds` is the BNB raised so far
    toward the curve's target (`maxFunds`); `liquidityAdded` flips to
    True the instant the curve completes and migrates to the DEX, which
    maps directly onto `is_bonding`.
    """

    platform_name = "four.meme"

    def read(self, w3: Web3, token_address: str) -> Optional[BondingStatus]:
        from app.services import four_meme

        try:
            contract = w3.eth.contract(address=four_meme.HELPER3, abi=four_meme.HELPER_ABI)
            info = contract.functions.getTokenInfo(Web3.to_checksum_address(token_address)).call()
            # version, tokenManager, quote, lastPrice, tradingFeeRate,
            # minTradingFee, launchTime, offers, maxOffers, funds, maxFunds, liquidityAdded
            funds, max_funds, liquidity_added = info[9], info[10], info[11]
            progress = min(100.0, (funds / max_funds) * 100) if max_funds else 0.0
            return BondingStatus(
                platform=self.platform_name,
                progress_pct=progress,
                is_bonding=not liquidity_added,
                raised_bnb=funds / 1e18,
                target_bnb=max_funds / 1e18,
            )
        except Exception as exc:
            logger.warning("FourMemeReader.read failed for %s: %s", token_address, exc)
            return None


class GraFunReader(BondingReader):
    """
    GraFun's "Token Sale Factory" contract address IS verified now —
    `0x8341b19a2A602eAE0f22633b6da12E1B016E6451` on BSC, confirmed via
    DefiLlama's own dimension-adapters source (dexs/grafun.ts), which
    hardcodes it for their own fee/volume tracking — a source with no
    reason to get it wrong. What's still unconfirmed is a bonding-progress
    read function on that contract: DefiLlama's adapter only needed the
    `Swap(address indexed token, address indexed referrer, address
    indexed account, bool isBuy, uint256 bnbAmount, uint256 tokenAmount,
    uint256 fee, uint256 reserved)` event (for volume), which doesn't by
    itself expose a maxFunds-style target to compute progress against —
    same open item as before, just narrowed: find GraFun's equivalent of
    four.meme's `getTokenInfo` (a getter that returns funds raised vs.
    target), most likely on this same contract. Check its BscScan page for
    verified source once BscScan is reachable from wherever you're
    running this, or search for other open-source GraFun integrations the
    way app/services/four_meme.py's docstring found four.meme's.
    """

    platform_name = "grafun"
    CURVE_ABI: list = []

    def read(self, w3: Web3, token_address: str) -> Optional[BondingStatus]:
        if not self.CURVE_ABI:
            logger.debug("GraFunReader: progress-read ABI not confirmed yet, skipping on-chain read")
            return None
        return None


READERS: dict[str, BondingReader] = {
    "four.meme": FourMemeReader(),
    "grafun": GraFunReader(),
}


def read_bonding_status(w3: Optional[Web3], platform: str, token_address: str) -> Optional[BondingStatus]:
    if settings.demo_mode or w3 is None:
        return _demo_bonding_status(platform)

    reader = READERS.get(platform)
    if reader is None:
        return None
    try:
        return reader.read(w3, token_address)
    except Exception as exc:
        logger.warning("bonding read failed for %s (%s): %s", token_address, platform, exc)
        return None


def _demo_bonding_status(platform: str) -> BondingStatus:
    progress = round(random.uniform(1, 100), 1)
    return BondingStatus(
        platform=platform,
        progress_pct=progress,
        is_bonding=progress < 100,
        raised_bnb=round(progress / 100 * 24, 3),
        target_bnb=24.0,
    )
