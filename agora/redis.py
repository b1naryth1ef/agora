import aioredis
from agora.util.json import dumps

pool = None


async def init_redis(url):
    global pool
    pool = await aioredis.create_pool(url)


def close_redis():
    pool.close()
    return pool.wait_closed()


def acquire():
    return pool.acquire()


def release(conn):
    return pool.release(conn)


def get_pool():
    return pool


async def dispatch_event(event, data, member=None, realm=None, channel=None):
    target = None
    if realm:
        target = f'r:{realm["id"]}'

    if member:
        target = f'u:{member["identity_id"]}'

    if channel:
        target = f'c:{channel["id"]}'

    if not target:
        raise Exception("invalid dispatch target")

    await pool.execute("PUBLISH", target, dumps({"e": event, "d": data}))
