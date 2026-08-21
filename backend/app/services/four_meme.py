"""
Verified four.meme contract details (BSC only).

Unlike the placeholder addresses this repo started with, these were
independently cross-confirmed from two sources rather than guessed:

1. Bitquery's public four.meme API docs (docs.bitquery.io/docs/blockchain/
   BSC/four-meme-api/), which document the TokenManager2 address as "the
   four.meme exchange proxy on BNB Chain" for TokenCreate/LiquidityAdded/
   migration events.
2. four-meme-community/four-meme-ai (MIT-licensed, github.com/four-meme-
   community/four-meme-ai) — an open-source integration project whose
   skills/four-meme-integration/references/contract-addresses.md and
   event-listening.md documents the same TokenManager2 address plus the
   exact event and getTokenInfo() signatures used below.

Both sources agree on 0x5c952063c7fc8610FFDB798152D69F0B9550762b for
TokenManager2 — that's what gives this enough confidence to wire in as a
real (not placeholder) address. See README.md §6.2 for the full trail.

TokenManagerHelper3 is a separate, fixed helper contract four.meme
provides specifically for reading token/bonding-curve state (getTokenInfo)
without needing to know which TokenManager version a given token uses —
it's not something that varies per-deployment, so it's hardcoded here
rather than pulled from Settings/env like the factory address is.
"""
from web3 import Web3

TOKEN_MANAGER2 = Web3.to_checksum_address("0x5c952063c7fc8610FFDB798152D69F0B9550762b")
HELPER3 = Web3.to_checksum_address("0xF251F83e40a78868FcfA3FA4599Dad6494E46034")

# Only the events/functions BNBPRINT actually uses — TokenManager2 exposes
# more (TokenPurchase, TokenSale) that would matter for a trading bot, not
# a discovery/security-screening tool like this one.
EVENT_ABI = [
    {
        "anonymous": False,
        "inputs": [
            {"indexed": False, "name": "creator", "type": "address"},
            {"indexed": False, "name": "token", "type": "address"},
            {"indexed": False, "name": "requestId", "type": "uint256"},
            {"indexed": False, "name": "name", "type": "string"},
            {"indexed": False, "name": "symbol", "type": "string"},
            {"indexed": False, "name": "totalSupply", "type": "uint256"},
            {"indexed": False, "name": "launchTime", "type": "uint256"},
            {"indexed": False, "name": "launchFee", "type": "uint256"},
        ],
        "name": "TokenCreate",
        "type": "event",
    },
]

HELPER_ABI = [
    {
        "name": "getTokenInfo",
        "type": "function",
        "stateMutability": "view",
        "inputs": [{"name": "token", "type": "address"}],
        "outputs": [
            {"name": "version", "type": "uint256"},
            {"name": "tokenManager", "type": "address"},
            {"name": "quote", "type": "address"},
            {"name": "lastPrice", "type": "uint256"},
            {"name": "tradingFeeRate", "type": "uint256"},
            {"name": "minTradingFee", "type": "uint256"},
            {"name": "launchTime", "type": "uint256"},
            {"name": "offers", "type": "uint256"},
            {"name": "maxOffers", "type": "uint256"},
            {"name": "funds", "type": "uint256"},
            {"name": "maxFunds", "type": "uint256"},
            {"name": "liquidityAdded", "type": "bool"},
        ],
    },
]
