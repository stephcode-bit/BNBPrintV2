from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.ws_manager import manager

router = APIRouter()


@router.websocket("/ws/tokens")
async def tokens_ws(ws: WebSocket):
    """
    Streams real-time events as JSON: {"type": "...", "data": {...}}

    Event types:
      new_token        - a freshly discovered token
      token_updated     - periodic refresh of a bonding token's data
      runner_flagged    - a token just crossed the runner-score threshold
      bonding_complete  - a token finished bonding and migrated to the DEX
    """
    await manager.connect(ws)
    try:
        while True:
            # We don't expect client -> server messages, but read (and
            # discard) to detect disconnects promptly and allow future
            # client-side filters/subscriptions to be added here.
            await ws.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        await manager.disconnect(ws)
