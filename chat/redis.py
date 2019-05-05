import aioredis
import json

pool = None


async def init_redis(url):
    global pool
    pool = await aioredis.create_pool(url)


def acquire():
    return pool.acquire()


def release(conn):
    return pool.release(conn)


def get_pool():
    return pool


async def dispatch_event(event, data, member=None, realm=None):
    channel = None
    if realm:
        channel = f'r:{realm["id"]}'

    if member:
        channel = f'u:{member["id"]}'

    if not channel:
        raise Exception("invalid dispatch target")

    await pool.execute("PUBLISH", channel, json.dumps({"e": event, "d": data}))
