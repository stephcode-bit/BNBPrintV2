import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import init_db
from app.routers import bookmarks, push, stats, tokens, ws
from app.tasks import cleanup_stale_tokens_loop, refresh_bonding_tokens_loop, start_chain_listener

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("bnbprint.main")

settings = get_settings()

_background_tasks: list[asyncio.Task] = []


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting %s (env=%s, demo_mode=%s)", settings.app_name, settings.env, settings.demo_mode)
    init_db()

    _background_tasks.append(asyncio.create_task(start_chain_listener()))
    _background_tasks.append(asyncio.create_task(refresh_bonding_tokens_loop()))
    _background_tasks.append(asyncio.create_task(cleanup_stale_tokens_loop()))

    yield

    for task in _background_tasks:
        task.cancel()
    await asyncio.gather(*_background_tasks, return_exceptions=True)
    logger.info("Shutdown complete")


app = FastAPI(
    title="BNBPRINT API",
    description="Real-time BNB Chain token discovery, security checks, and runner alerts.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tokens.router)
app.include_router(bookmarks.router)
app.include_router(stats.router)
app.include_router(ws.router)
app.include_router(push.router)


@app.get("/")
def root():
    return {
        "app": settings.app_name,
        "status": "ok",
        "demo_mode": settings.demo_mode,
        "docs": "/docs",
    }


@app.get("/health")
def health():
    return {"status": "healthy"}
