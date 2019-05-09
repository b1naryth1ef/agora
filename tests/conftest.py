import os
import asyncio
import inspect

import pytest
import asyncpg

os.environ["TESTING"] = "1"
os.environ.setdefault("AGORA_PG_URL", "postgres://agora:agora@localhost/agora_test")
os.environ.setdefault("AGORA_REDIS_URL", "redis://localhost/9")

# Mark every test as async
pytestmark = pytest.mark.asyncio

# Create our event loop
loop = asyncio.get_event_loop_policy().new_event_loop()


@pytest.fixture(scope="session")
def app():
    from agora.http import app

    return app


@pytest.fixture(scope="session")
def client(app):
    return app.test_client()


@pytest.fixture(scope="session")
def event_loop():
    return loop


@pytest.fixture(scope="session")
def auth_header():
    def _gen_auth_headers(identity):
        return {"Authorization": f"Token {identity['access_token']}"}

    return _gen_auth_headers


@pytest.fixture(scope="session")
def create_identity():
    from nacl.signing import SigningKey
    from nacl.encoding import Base64Encoder
    from agora.db.identity import create_or_update_identity
    from agora.db.realm import create_realm, create_realm_membership

    async def _create_identity(num_realms_owner=0, num_realms_member=0):
        key = SigningKey.generate()

        identity = await create_or_update_identity(
            key.verify_key.encode(encoder=Base64Encoder).decode("utf-8")
        )

        realm_owner = []
        for idx in range(num_realms_owner):
            realm_owner.append(await create_realm(identity, "test-realm", True))

        realm_member = []
        if num_realms_member:
            other_identity, other_realms, _ = await create_identity(
                num_realms_owwner=num_realms_member
            )

            for realm in other_realms:
                realm_member.append(
                    await create_realm_membership(realm, identity["id"])
                )

        return identity, realm_owner, realm_member

    return _create_identity


async def clear_database():
    assert os.environ["AGORA_PG_URL"].endswith(
        "agora_test"
    ), "why you droppin my prod db bro?"
    conn = await asyncpg.connect(os.environ["AGORA_PG_URL"])

    rows = await conn.fetch(
        "SELECT tablename FROM pg_catalog.pg_tables WHERE tableowner = 'agora';"
    )

    for table in rows:
        await conn.execute(f"DROP TABLE {table['tablename']} CASCADE")

    await conn.close()


async def teardown_loop():
    from agora.db import close_db
    from agora.redis import close_redis

    await close_db()
    await close_redis()


def pytest_configure(config):
    loop.run_until_complete(clear_database())


def pytest_unconfigure(config):
    loop.run_until_complete(teardown_loop())
    loop.close()


# This function marks all our coroutine functions so they will be run correctly
def pytest_collection_modifyitems(items):
    for item in items:
        if inspect.iscoroutinefunction(item._obj):
            item.add_marker(pytest.mark.asyncio)
