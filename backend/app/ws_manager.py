import asyncio
import json
import logging
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger("bnbprint.ws")


class ConnectionManager:
    """Fan-out manager for the /ws/tokens stream. Every new token, security
    update, or bonding-progress tick gets broadcast to all connected
    clients as a small JSON envelope: {"type": ..., "data": ...}."""

    def __init__(self) -> None:
        self._connections: set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        async with self._lock:
            self._connections.add(ws)
        logger.info("client connected (%d total)", len(self._connections))

    async def disconnect(self, ws: WebSocket) -> None:
        async with self._lock:
            self._connections.discard(ws)
        logger.info("client disconnected (%d total)", len(self._connections))

    async def broadcast(self, event_type: str, data: Any) -> None:
        payload = json.dumps({"type": event_type, "data": data}, default=str)
        dead: list[WebSocket] = []
        async with self._lock:
            targets = list(self._connections)
        for ws in targets:
            try:
                await ws.send_text(payload)
            except Exception:
                dead.append(ws)
        if dead:
            async with self._lock:
                for ws in dead:
                    self._connections.discard(ws)


manager = ConnectionManager()
