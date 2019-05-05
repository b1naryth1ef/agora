from quart import Blueprint, jsonify

from chat.redis import dispatch_event
from chat.db.channel import (
    create_realm_channel,
    delete_channel,
    serialize_channel,
    ChannelType,
)
from chat.http.util import authed, validate_json, APIError
from chat.http.views.realm import with_realm

blueprint = Blueprint("channel", __name__)


@blueprint.route("/realm/<realm_id>/channel", methods=["POST"])
@authed()
@with_realm(admin=True)
async def realm_channel_create(realm, member):
    payload = await validate_json(
        {"type": str, "name": (str, 60), "topic": (str, 2000)}
    )

    if payload["type"] not in ChannelType.REALM:
        raise APIError(0, "invalid channel type")

    channel = serialize_channel(
        await create_realm_channel(
            realm, payload["type"], payload["name"], payload["topic"]
        )
    )
    await dispatch_event("CHANNEL_ADD", channel, realm=realm)
    return jsonify(channel)


@blueprint.route("/realm/<realm_id>/channel/<channel_id>", methods=["DELETE"])
@authed()
@with_realm(admin=True)
async def realm_channel_delete(realm, member, channel_id):
    channel = await delete_channel(channel_id)
    if not channel:
        raise APIError(0, "channel not found", status_code=404)

    await dispatch_event("CHANNEL_DELETE", serialize_channel(channel), realm=realm)
    return "", 204
