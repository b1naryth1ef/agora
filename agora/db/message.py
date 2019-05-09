from quart import g
import ulid.api


class MessageType(object):
    PROSE = "prose"
    UPLOAD = "upload"
    SYSTEM_EVENT = "system_event"

    ALL = {PROSE, UPLOAD, SYSTEM_EVENT}


async def create_realm_message(message_type, realm_channel_id, author_id, content):
    return await g.conn.fetchrow(
        """
        INSERT INTO realm_messages (id, type, realm_channel_id, author_id, content)
        VALUES ($1, $2, $3, $4, $5)
        RETURNING *
    """,
        ulid.api.new().uuid,
        message_type,
        realm_channel_id,
        author_id,
        content,
    )


async def get_realm_messages_by_channel(realm_channel_id, after, limit=None):
    return await g.conn.fetch(
        """
        SELECT * FROM realm_messages
        WHERE
            realm_channel_id=$1 AND id > $2
        ORDER BY id ASC
        LIMIT $3
    """,
        realm_channel_id,
        after,
        limit,
    )


async def delete_realm_message_by_id(message_id, ensure_author_id=None):
    query = """
        DELETE FROM realm_messages
        WHERE id=$1 {}
        RETURNING *
    """.format(
        "AND author_id=$2" if ensure_author_id else ""
    )
    return await g.conn.fetchrow(query, message_id, ensure_author_id)


def serialize_message(message):
    return dict(message.items())
