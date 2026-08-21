"""
On-chain security checks that don't depend on any third-party API — these
run directly against BNB Chain via web3.py so BNBPRINT still has a security
opinion even if Ave AI is unreachable or unconfigured.

Each check is defensive: RPC failures return a neutral/unknown result
rather than raising, so one bad call doesn't take down the whole pipeline.
"""
import logging
from dataclasses import dataclass
from typing import Optional

from web3 import Web3

from app.config import get_settings

logger = logging.getLogger("bnbprint.security_checks")
settings = get_settings()

BURN_ADDRESSES = {
    "0x0000000000000000000000000000000000dead",
    "0x0000000000000000000000000000000000000000"[:42],
    "0x0000000000000000000000000000000000000000",
}

# Minimal ERC20 ABI fragment — enough for owner/mint/holder-style probes.
ERC20_ABI = [
    {"constant": True, "inputs": [], "name": "owner", "outputs": [{"name": "", "type": "address"}], "type": "function"},
    {"constant": True, "inputs": [], "name": "totalSupply", "outputs": [{"name": "", "type": "uint256"}], "type": "function"},
    {"constant": True, "inputs": [{"name": "account", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "", "type": "uint256"}], "type": "function"},
    {"constant": False, "inputs": [{"name": "to", "type": "address"}, {"name": "amount", "type": "uint256"}], "name": "transfer", "outputs": [{"name": "", "type": "bool"}], "type": "function"},
]

# Well-known BSC LP-locker contracts worth checking for a lock record.
KNOWN_LOCKERS = {
    "unicrypt": "0xC765bddB93b0D1c1A88282BA0fa6B2d00E3e0c83",
    "pinklock": "0x71B5759d73262FBb223956913ecF4ecC51057641",
    "team_finance": "0xE2fE530C047f2d85298b07D9333C05737f1435fB",
}


@dataclass
class OnChainSecurity:
    owner_address: Optional[str]
    owner_renounced: bool
    mint_disabled: bool
    contract_verified: Optional[bool]  # BscScan verification isn't queryable via RPC; left for API integration
    honeypot_risk: Optional[bool]
    buy_tax_pct: float
    sell_tax_pct: float
    liquidity_locked: bool
    top10_holder_pct: Optional[float]
    notes: list[str]


def get_web3() -> Optional[Web3]:
    if not settings.rpc_https_url:
        return None
    try:
        w3 = Web3(Web3.HTTPProvider(settings.rpc_https_url, request_kwargs={"timeout": 8}))
        return w3 if w3.is_connected() else None
    except Exception as exc:
        logger.warning("RPC connection failed: %s", exc)
        return None


def check_owner_renounced(w3: Web3, token_address: str) -> tuple[Optional[str], bool]:
    """Reads owner() if present; renounced == owner is a burn/zero address."""
    try:
        contract = w3.eth.contract(address=Web3.to_checksum_address(token_address), abi=ERC20_ABI)
        owner = contract.functions.owner().call()
        renounced = owner.lower() in BURN_ADDRESSES
        return owner, renounced
    except Exception:
        # No owner() function is itself a decent signal (can't be common
        # rug patterns that rely on owner-gated mint/blacklist functions),
        # but we can't assert renounced==True without more info.
        return None, False


def simulate_buy_sell(w3: Web3, token_address: str, pair_address: Optional[str]) -> tuple[Optional[bool], float, float]:
    """
    Honeypot simulation stub.

    A real implementation forks state at the latest block (via `eth_call`
    with a state override, or a local anvil/ganache fork) and:
      1. Buys the token with a small amount of BNB/WBNB through the router.
      2. Immediately attempts to sell it back.
      3. Compares expected vs. actual output to infer buy/sell tax, and
         flags `honeypot_risk=True` if the sell reverts or returns ~0.

    That requires a router ABI, a temporary funded account (or a state
    override to fund one), and slippage-safe call construction, which is
    beyond a single eth_call — wire in a service like honeypot.is's API,
    or your own forked-state simulator, and replace this function's body.
    Until then this returns "unknown" rather than a false negative.
    """
    return None, 0.0, 0.0


def check_liquidity_lock(w3: Web3, pair_address: Optional[str]) -> bool:
    """
    Checks whether a meaningful share of LP tokens sits in a known locker
    contract. This is a heuristic (balanceOf on each known locker) rather
    than a guarantee — some platforms use bespoke lockers not listed here.
    """
    if not pair_address:
        return False
    try:
        pair = w3.eth.contract(address=Web3.to_checksum_address(pair_address), abi=ERC20_ABI)
        total_supply = pair.functions.totalSupply().call()
        if total_supply == 0:
            return False
        for _, locker_addr in KNOWN_LOCKERS.items():
            try:
                locked_balance = pair.functions.balanceOf(Web3.to_checksum_address(locker_addr)).call()
                if locked_balance / total_supply > 0.5:
                    return True
            except Exception:
                continue
    except Exception:
        pass
    return False


def run_full_check(token_address: str, pair_address: Optional[str] = None) -> OnChainSecurity:
    notes: list[str] = []
    w3 = get_web3()
    if w3 is None:
        notes.append("RPC unavailable — on-chain checks skipped, relying on Ave AI only")
        return OnChainSecurity(
            owner_address=None,
            owner_renounced=False,
            mint_disabled=False,
            contract_verified=None,
            honeypot_risk=None,
            buy_tax_pct=0.0,
            sell_tax_pct=0.0,
            liquidity_locked=False,
            top10_holder_pct=None,
            notes=notes,
        )

    owner, renounced = check_owner_renounced(w3, token_address)
    honeypot, buy_tax, sell_tax = simulate_buy_sell(w3, token_address, pair_address)
    locked = check_liquidity_lock(w3, pair_address)

    return OnChainSecurity(
        owner_address=owner,
        owner_renounced=renounced,
        mint_disabled=renounced,  # best-effort proxy until mint-selector introspection is added
        contract_verified=None,
        honeypot_risk=honeypot,
        buy_tax_pct=buy_tax,
        sell_tax_pct=sell_tax,
        liquidity_locked=locked,
        top10_holder_pct=None,
        notes=notes,
    )
