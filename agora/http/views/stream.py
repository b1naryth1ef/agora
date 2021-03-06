import asyncio
import json

from aioredis.pubsub import Receiver
from quart import Blueprint, websocket, g
from agora.redis import get_pool
from agora.db import release
from agora.db.identity import serialize_identity
from agora.db.realm import get_realms_for_hello, serialize_realm
from agora.http.util.auth import authenticate_from_token, AuthenticationFailure
from agora.util.json import dumps


blueprint = Blueprint("stream", __name__)


@blueprint.websocket("/stream/ws")
async def stream_ws():
    await websocket.accept()

    try:
        login = await websocket.receive()
        payload = json.loads(login)
        method = payload['a']
        data = payload['d']
    except Exception:
        websocket.send(dumps({
            "e": "ERROR",
            "d": {
                "code": 0,
                "message": "Invalid Payload",
            },
        }))
        return

    if method != 'LOGIN':
        websocket.send(dumps({
            "e": "ERROR",
            "d": {
                "code": 0,
                "message": "Login Required",
            },
        }))
        return

    try:
        g.identity = await authenticate_from_token(data)
    except AuthenticationFailure:
        websocket.send(dumps({
            "e": "ERROR",
            "d": {
                "code": 0,
                "message": "Invalid Authentication",
            }
        }))
        return

    pool = get_pool()
    recv = Receiver()

    realms = await get_realms_for_hello(g.identity)

    # Once we're done using the db connection get rid of it
    await release(g.conn)

    await websocket.send(
        dumps(
            {
                "e": "HELLO",
                "d": {
                    "identity": serialize_identity(g.identity),
                    "realms": [serialize_realm(r) for r in realms],
                },
            }
        )
    )

    # Subscribe to the user channel
    await pool.execute_pubsub("subscribe", recv.channel(f'u:{g.identity["id"]}'))

    # Subscribe to realm channels
    for realm in realms:
        await pool.execute_pubsub("subscribe", recv.channel(f'r:{realm["id"]}'))

        for channel in realm["channels"]:
            await pool.execute_pubsub("subscribe", recv.channel(f'c:{channel["id"]}'))

    ws_message_coro = asyncio.create_task(websocket.receive())
    redis_message_coro = asyncio.create_task(recv.get())

    while True:
        (done, pending) = await asyncio.wait(
            [ws_message_coro, redis_message_coro], return_when=asyncio.FIRST_COMPLETED
        )

        if ws_message_coro in done:
            message = ws_message_coro.result()
            ws_message_coro = asyncio.create_task(websocket.receive())

        if redis_message_coro in done:
            (channel, message) = redis_message_coro.result()
            await websocket.send(message.decode("utf-8"))
            redis_message_coro = asyncio.create_task(recv.get())
