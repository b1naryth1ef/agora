from quart import g
import ulid.api


class RealmChannelType(object):
    INFO = "info"
    FOLDER = "folder"
    TEXT = "text"
    VOICE = "voice"

    ALL = {VOICE, TEXT, FOLDER, INFO}


async def create_realm_channel(realm, channel_type, name, topic):
    return await g.conn.fetchrow(
        """
        INSERT INTO realm_channels
            (id, realm_id, type, name, topic)
        VALUES ($1, $2, $3, $4, $5)
        RETURNING *
    """,
        ulid.api.new().uuid,
        realm["id"],
        channel_type,
        name,
        topic,
    )


async def delete_realm_channel(channel_id):
    return await g.conn.fetchrow(
        """
        DELETE FROM realm_channels WHERE id=$1
        RETURNING *
    """,
        int(channel_id),
    )


async def get_realm_channel(realm_id, channel_id):
    return await g.conn.fetchrow(
        """
        SELECT * FROM realm_channels
        WHERE realm_id=$1 AND id=$2
    """,
        realm_id,
        channel_id,
    )


def serialize_realm_channel(channel):
    data = {
        "id": channel["id"],
        "type": channel["type"],
        "name": channel["name"],
        "topic": channel["topic"],
    }

    return data
