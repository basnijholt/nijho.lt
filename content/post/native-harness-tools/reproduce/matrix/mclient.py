"""Small Matrix client for the minimal-mode eval: one user, one room per trial, wait for the agent's reply."""
from __future__ import annotations

import asyncio
import time

import nio

HS = "http://127.0.0.1:28700"


TOKEN_FILE = "/work/rrsi-minimal/.evaltoken.json"


async def client_for(user: str, password: str) -> nio.AsyncClient:
    """Return a new client for *user*, reusing one cached access token so the homeserver's login limit never applies."""
    import json, os
    if os.path.exists(TOKEN_FILE):
        saved = json.load(open(TOKEN_FILE))
        client = nio.AsyncClient(HS, saved["user_id"])
        client.restore_login(saved["user_id"], saved["device_id"], saved["access_token"])
        resp = await client.whoami()
        if isinstance(resp, nio.WhoamiResponse):
            return client
        await client.close()
    client = await login(user, password)
    fd = os.open(TOKEN_FILE, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f:
        json.dump({"user_id": client.user_id, "device_id": client.device_id, "access_token": client.access_token}, f)
    return client


async def login(user: str, password: str) -> nio.AsyncClient:
    client = nio.AsyncClient(HS, f"@{user}:matrix.localhost")
    resp = await client.login(password)
    if not isinstance(resp, nio.LoginResponse):
        resp = await client.register(user, password)
        assert isinstance(resp, nio.RegisterResponse), resp
    await client.sync(timeout=1000, full_state=True)
    return client


async def new_room(client: nio.AsyncClient, invite: list[str], name: str) -> str:
    resp = await client.room_create(name=name, invite=invite, is_direct=False)
    assert isinstance(resp, nio.RoomCreateResponse), resp
    room_id = resp.room_id
    deadline = time.time() + 120
    while time.time() < deadline:
        members = await client.joined_members(room_id)
        joined = {m.user_id for m in getattr(members, "members", [])}
        if set(invite) <= joined:
            return room_id
        await asyncio.sleep(1)
    raise TimeoutError(f"agents never joined {room_id}")


async def send(client: nio.AsyncClient, room_id: str, body: str) -> str:
    resp = await client.room_send(room_id, "m.room.message", {"msgtype": "m.text", "body": body})
    assert isinstance(resp, nio.RoomSendResponse), resp
    return resp.event_id


async def messages_from(client: nio.AsyncClient, room_id: str, sender: str, after_ts: int) -> list[dict]:
    resp = await client.room_messages(room_id, start="", limit=100, direction=nio.MessageDirection.back)
    out = []
    for ev in reversed(resp.chunk):
        src = ev.source
        if src.get("sender") == sender and src.get("origin_server_ts", 0) >= after_ts and src.get("type") == "m.room.message":
            out.append(src)
    return out
