from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Token
from app.schemas import TokenListResponse, TokenOut

router = APIRouter(prefix="/api/tokens", tags=["tokens"])


@router.get("", response_model=TokenListResponse)
def list_tokens(
    db: Session = Depends(get_db),
    bonding: Optional[bool] = Query(None, description="Filter: still bonding vs migrated"),
    platform: Optional[str] = Query(None, description="four.meme | grafun | pancakeswap_v2 ..."),
    min_security_score: Optional[float] = Query(None, ge=0, le=100),
    runners_only: bool = Query(False),
    search: Optional[str] = Query(None, description="Match symbol/name/address"),
    sort_by: str = Query("created_at", pattern="^(created_at|security_score|runner_score|bonding_progress|volume_24h_usd|liquidity_usd|market_cap_usd)$"),
    order: str = Query("desc", pattern="^(asc|desc)$"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    stmt = select(Token)

    if bonding is not None:
        stmt = stmt.where(Token.is_bonding == bonding)
    if platform:
        stmt = stmt.where(Token.bonding_platform == platform)
    if min_security_score is not None:
        stmt = stmt.where(Token.security_score >= min_security_score)
    if runners_only:
        stmt = stmt.where(Token.is_runner.is_(True))
    if search:
        like = f"%{search.lower()}%"
        stmt = stmt.where(
            (Token.symbol.ilike(like)) | (Token.name.ilike(like)) | (Token.address.ilike(like))
        )

    total = len(db.execute(stmt).scalars().all())

    sort_col = getattr(Token, sort_by)
    stmt = stmt.order_by(sort_col.desc() if order == "desc" else sort_col.asc())
    stmt = stmt.offset(offset).limit(limit)

    items = db.execute(stmt).scalars().all()
    return TokenListResponse(items=items, total=total, limit=limit, offset=offset)


@router.get("/{address}", response_model=TokenOut)
def get_token(address: str, db: Session = Depends(get_db)):
    token = db.get(Token, address)
    if not token:
        raise HTTPException(status_code=404, detail="Token not found")
    return token
