from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Bookmark, Token
from app.schemas import BookmarkCreate, BookmarkOut

router = APIRouter(prefix="/api/bookmarks", tags=["bookmarks"])


@router.get("", response_model=list[BookmarkOut])
def list_bookmarks(user_id: str = Query(...), db: Session = Depends(get_db)):
    stmt = select(Bookmark).where(Bookmark.user_id == user_id).order_by(Bookmark.created_at.desc())
    bookmarks = db.execute(stmt).scalars().all()
    results = []
    for b in bookmarks:
        token = db.get(Token, b.token_address)
        item = BookmarkOut.model_validate(b)
        item.token = token
        results.append(item)
    return results


@router.post("", response_model=BookmarkOut, status_code=201)
def add_bookmark(payload: BookmarkCreate, db: Session = Depends(get_db)):
    existing = db.execute(
        select(Bookmark).where(
            Bookmark.user_id == payload.user_id, Bookmark.token_address == payload.token_address
        )
    ).scalar_one_or_none()
    if existing:
        return existing

    bookmark = Bookmark(**payload.model_dump())
    db.add(bookmark)
    db.commit()
    db.refresh(bookmark)
    return bookmark


@router.delete("/{address}", status_code=204)
def remove_bookmark(address: str, user_id: str = Query(...), db: Session = Depends(get_db)):
    stmt = select(Bookmark).where(Bookmark.user_id == user_id, Bookmark.token_address == address)
    bookmark = db.execute(stmt).scalar_one_or_none()
    if not bookmark:
        raise HTTPException(status_code=404, detail="Bookmark not found")
    db.delete(bookmark)
    db.commit()
    return None
