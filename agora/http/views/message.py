import json

from quart import Blueprint, jsonify, request, g

from agora.redis import dispatch_event
from agora.permissions import Scopes
from agora.http.util import authed, validate_json, APIError
from agora.http.util.decos import require_scopes
from agora.http.views.channel import require_channel
from agora.db.message import (
    create_realm_message,
    get_realm_messages_by_channel,
    serialize_message,
    delete_realm_message_by_id,
    MessageType,
)

blueprint = Blueprint("messages", __name__)


@blueprint.route(
    "/realms/<ulid:realm_id>/channels/<ulid:channel_id>/messages", methods=["POST"]
)
@authed()
@require_channel(pass_channel=True)
@require_scopes(Scopes.REALM_CHANNEL_MESSAGE_CREATE)
async def realm_channel_message_create(channel):
    payload = await validate_json({"type": str, "content": dict})

    if payload["type"] not in MessageType.ALL:
        raise APIError(0, "invalid message type")

    # TODO: validate content based on type

    message = serialize_message(
        await create_realm_message(
            payload["type"],
            channel["id"],
            g.identity["id"],
            json.dumps(payload["content"]),
        )
    )

    await dispatch_event("MESSAGE_ADD", message, channel=channel)
    return jsonify(message)


@blueprint.route(
    "/realms/<ulid:realm_id>/channels/<ulid:channel_id>/messages", methods=["GET"]
)
@authed()
@require_channel(pass_channel=True)
@require_scopes(Scopes.REALM_CHANNEL_MESSAGE_VIEW)
async def realm_channel_message_list(channel):
    values = await request.values

    messages = await get_realm_messages_by_channel(
        channel["id"], after=int(values.get("after", 0)), limit=100
    )

    return jsonify([serialize_message(m) for m in messages])


@blueprint.route(
    "/realms/<ulid:realm_id>/channels/<ulid:channel_id>/messages/<ulid:message_id>",
    methods=["DELETE"],
)
@authed()
@require_channel(pass_channel=True)
@require_scopes(
    Scopes.REALM_CHANNEL_MESSAGE_DELETE,
    Scopes.REALM_CHANNEL_MESSAGE_SELF_DELETE,
    allow_any=True,
    include_scopes=True,
)
async def realm_channel_message_delete(channel, scopes, message_id):
    if scopes[Scopes.REALM_CHANNEL_MESSAGE_DELETE]:
        message = await delete_realm_message_by_id(message_id)
    else:
        message = await delete_realm_message_by_id(message_id, g.identity["id"])

    if not message:
        raise APIError(0, "unknown message", status_code=404)

    return "", 204
