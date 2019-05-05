import asyncio
import json

from aioredis.pubsub import Receiver
from quart import Blueprint, websocket, g
from chat.redis import get_pool
from chat.db import release
from chat.db.identity import serialize_identity
from chat.db.realm import get_realms_for_hello, serialize_realm
from ..util import authed


blueprint = Blueprint("stream", __name__)


@blueprint.websocket("/stream/ws")
@authed()
async def stream_ws():
    await websocket.accept()

    pool = get_pool()
    recv = Receiver()

    realms = await get_realms_for_hello(g.identity)

    # Once we're done using the db connection get rid of it
    await release(g.conn)

    await websocket.send(
        json.dumps(
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
    await pool.execute_pubsub("subscribe", recv.channel(f'u:{g.identity["key"]}'))

    # Subscribe to realm channels
    for realm in realms:
        await pool.execute_pubsub("subscribe", recv.channel(f'r:{realm["id"]}'))

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
