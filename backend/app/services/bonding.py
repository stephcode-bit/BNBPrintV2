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
    four.meme bonding curves track BNB raised vs. a fixed target (public
    docs have historically cited ~24 BNB to complete a curve, subject to
    change — confirm current parameters before relying on this).

    TODO: replace `CURVE_ABI` with the verified ABI from the deployed
    four.meme curve/factory contract and implement the real call below.
    """

    platform_name = "four.meme"
    CURVE_ABI: list = []  # fill in once verified

    def read(self, w3: Web3, token_address: str) -> Optional[BondingStatus]:
        if not self.CURVE_ABI:
            logger.debug("FourMemeReader: ABI not configured, skipping on-chain read")
            return None
        # Example shape once ABI is wired in:
        # contract = w3.eth.contract(address=curve_address, abi=self.CURVE_ABI)
        # raised = contract.functions.raisedBNB(token_address).call() / 1e18
        # target = contract.functions.targetBNB().call() / 1e18
        # progress = min(100.0, (raised / target) * 100) if target else 0.0
        # return BondingStatus(self.platform_name, progress, progress < 100, raised, target)
        return None


class GraFunReader(BondingReader):
    """Same pattern as FourMemeReader — fill in GraFun's verified curve ABI."""

    platform_name = "grafun"
    CURVE_ABI: list = []

    def read(self, w3: Web3, token_address: str) -> Optional[BondingStatus]:
        if not self.CURVE_ABI:
            logger.debug("GraFunReader: ABI not configured, skipping on-chain read")
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
