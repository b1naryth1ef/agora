from quart import g


class ChannelType(object):
    REALM_INFO = "realm_info"
    REALM_FOLDER = "realm_folder"
    REALM_TEXT = "realm_text"
    REALM_VOICE = "realm_voice"
    GROUP = "group"
    DIRECT = "direct"

    REALM = {REALM_INFO, REALM_FOLDER, REALM_TEXT, REALM_VOICE}

    ALL = {DIRECT, GROUP, REALM_VOICE, REALM_TEXT, REALM_FOLDER, REALM_INFO}


async def create_realm_channel(realm, channel_type, name, topic):
    return await g.conn.fetchrow(
        """
        INSERT INTO channels
            (realm_id, type, name, topic)
        VALUES ($1, $2, $3, $4)
        RETURNING *
    """,
        realm["id"],
        channel_type,
        name,
        topic,
    )


async def delete_channel(channel_id):
    return await g.conn.fetchrow(
        """
        DELETE FROM channels WHERE id=$1
        RETURNING *
    """,
        int(channel_id),
    )


def serialize_channel(channel):
    data = {
        "id": channel["id"],
        "type": channel["type"],
        "name": channel["name"],
        "topic": channel["topic"],
    }

    if channel["type"] in (ChannelType.DIRECT, ChannelType.GROUP):
        data["member_ids"] = channel["member_identity_ids"]

    return data
