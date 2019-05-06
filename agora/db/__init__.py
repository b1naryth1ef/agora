import os
import asyncpg

pool = None


def acquire():
    return pool.acquire()


def release(conn):
    return pool.release(conn)


async def init_db(url):
    global pool
    pool = await asyncpg.create_pool(dsn=url)

    curpath = os.path.dirname(os.path.abspath(__file__))

    for schema in ["identity", "realm", "channel", "message"]:
        print(f"running schema file {schema}")
        path = os.path.join(curpath, "..", "..", "schema", f"{schema}.sql")
        with open(path, "r") as f:
            async with pool.acquire() as conn:
                await conn.execute(f.read())
