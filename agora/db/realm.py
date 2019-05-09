import json

from quart import g
import ulid.api

from agora.permissions import INITIAL_DEFAULT_REALM_ROLE_SCOPE_RULES
from agora.util.json import dumps


async def count_realms_by_user(identity):
    result = await g.conn.fetchrow(
        """
        SELECT count(*) AS count
        FROM realms
        WHERE id=$1
    """,
        identity["id"],
    )

    return result["count"]


async def get_realm(realm_id):
    return await g.conn.fetchrow(
        """
        SELECT * FROM realms
        WHERE id=$1
    """,
        realm_id,
    )


# TODO: figure out how to reduce the net hops w/ asyncpg
async def create_realm(identity, name, public):
    async with g.conn.transaction():
        realm_id = ulid.api.new().uuid
        role_id = ulid.api.new().uuid

        realm = await g.conn.fetchrow(
            """
            INSERT INTO realms (id, name, owner_id, is_public)
            VALUES ($1, $2, $3, $4)
            RETURNING *
        """,
            realm_id,
            name,
            identity["id"],
            public,
        )

        await g.conn.fetchrow(
            """
            INSERT INTO realm_roles
                (id, realm_id, name, granted_scopes, weight)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING *
        """,
            role_id,
            realm_id,
            "default",
            dumps(INITIAL_DEFAULT_REALM_ROLE_SCOPE_RULES),
            0,
        )

        await g.conn.execute(
            """
            UPDATE realms SET default_role_id=$1
            WHERE id=$2
        """,
            role_id,
            realm_id,
        )

        member = await g.conn.fetchrow(
            """
            INSERT INTO realm_members
                (realm_id, identity_id, joined_at, is_admin)
            VALUES ($1, $2, current_timestamp, true)
            RETURNING *
        """,
            realm_id,
            identity["id"],
        )

        await g.conn.execute(
            """
            INSERT INTO realm_member_roles (role_id, identity_id, realm_id)
            VALUES ($1, $2, $3)
        """,
            role_id,
            identity["id"],
            realm_id,
        )

    return realm, member


async def delete_realm(realm_id):
    await g.conn.execute(
        """
        DELETE FROM realms
        WHERE id=$1
        """,
        realm_id,
    )


async def get_realm_session_info(identity, realm_id):
    return await g.conn.fetchrow(
        """
        WITH member AS (
          SELECT DISTINCT ON (rm.realm_id) rm.*
          FROM realm_members rm
          WHERE rm.realm_id = $2 AND rm.identity_id = $1
        ),
        roles AS (
          SELECT DISTINCT ON (rr.realm_id) array_agg(rr.*) AS member_roles
          FROM realm_roles rr
          JOIN realm_member_roles rmr ON rmr.role_id = rr.id
          WHERE rmr.realm_id = $2 AND rmr.identity_id = $1
          GROUP BY rr.realm_id
        )
        SELECT
          r as realm,
          m::realm_members as member,
          rs.member_roles as member_roles
        FROM
          realms r,
          member m,
          roles rs
        WHERE r.id = $2;
    """,
        identity["id"],
        realm_id,
    )


async def get_realms_for_hello(identity):
    return await g.conn.fetch(
        """
        SELECT
            r.*,
            array_remove(array_agg(c.*), NULL) as channels,
            array_remove(array_agg(rs.*), NULL) as roles
        FROM realms r
        JOIN realm_members rm ON (rm.realm_id = r.id)
        LEFT JOIN realm_channels c ON (c.realm_id = r.id)
        LEFT JOIN realm_roles rs ON (rs.realm_id = r.id)
        WHERE rm.identity_id=$1
        GROUP BY r.id
    """,
        identity["id"],
    )


async def create_realm_membership(realm, identity_id):
    async with g.conn.transaction():
        member = await g.conn.fetchrow(
            """
            INSERT INTO realm_members
                (realm_id, identity_id, joined_at)
            VALUES ($1, $2, current_timestamp)
            RETURNING *
        """,
            realm["id"],
            identity_id,
        )

        await g.conn.execute(
            """
            INSERT INTO realm_member_roles (role_id, identity_id, realm_id)
            VALUES ($1, $2, $3)
        """,
            realm["default_role_id"],
            identity_id,
            realm["id"],
        )

    return member


def serialize_realm(realm):
    from agora.db.channel import serialize_realm_channel

    data = {"id": realm["id"], "name": realm["name"], "public": realm["is_public"]}

    if "channels" in realm:
        data["channels"] = [serialize_realm_channel(c) for c in realm["channels"]]

    if "roles" in realm:
        data["roles"] = [serialize_realm_role(r) for r in realm["roles"]]

    return data


def serialize_realm_member(member):
    return {"joined_at": member["joined_at"], "admin": member["is_admin"]}


def serialize_realm_role(role):
    return {
        "id": role["id"],
        "name": role["name"],
        "weight": role["weight"],
        "granted_scopes": json.loads(role["granted_scopes"]),
    }
