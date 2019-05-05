from quart import g


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


async def create_realm(identity, name, public):
    async with g.conn.transaction():
        realm = await g.conn.fetchrow(
            """
            INSERT INTO realms (name, owner_id, is_public)
            VALUES ($1, $2, $3)
            RETURNING *
        """,
            name,
            identity["id"],
            public,
        )

        member = await g.conn.fetchrow(
            """
            INSERT INTO realm_members
                (realm_id, identity_id, joined_at, is_admin)
            VALUES ($1, $2, current_timestamp, true)
            RETURNING *
        """,
            realm["id"],
            identity["id"],
        )

    return realm, member


async def get_realm_with_membership_by_id(identity, realm_id):
    return await g.conn.fetchrow(
        """
        SELECT r.*, array_agg(rm.*) as member FROM realms r
        JOIN realm_members rm ON rm.realm_id = r.id AND rm.identity_id = $1
        WHERE r.id=$2
        GROUP BY r.id
    """,
        identity["id"],
        int(realm_id),
    )


async def get_realms_for_hello(identity):
    return await g.conn.fetch(
        """
        SELECT r.*, array_agg(c.*) as channels FROM realms r
        JOIN channels c ON (c.realm_id = r.id)
        JOIN realm_members rm ON (rm.realm_id = r.id)
        WHERE rm.identity_id=$1
        GROUP BY r.id
    """,
        identity["id"],
    )


def serialize_realm(realm):
    from chat.db.channel import serialize_channel

    data = {"id": realm["id"], "name": realm["name"], "public": realm["is_public"]}

    if "channels" in realm:
        data["channels"] = [serialize_channel(c) for c in realm["channels"]]

    return data


def serialize_realm_member(member):
    return {"joined_at": member["joined_at"], "admin": member["is_admin"]}
