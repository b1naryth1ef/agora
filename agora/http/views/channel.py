from functools import wraps

from quart import Blueprint, jsonify, g

from agora.redis import dispatch_event
from agora.permissions import Scopes
from agora.db.channel import (
    get_realm_channel,
    create_realm_channel,
    delete_realm_channel,
    serialize_realm_channel,
    RealmChannelType,
)
from agora.http.util import authed, validate_json, APIError
from agora.http.util.decos import require_scopes
from agora.http.views.realm import require_realm

blueprint = Blueprint("channel", __name__)


def require_channel(pass_channel=False):
    def deco(f):
        @wraps(f)
        async def wrap(*args, **kwargs):
            if not g.session:
                raise APIError(0, "unknown realm", status_code=404)

            channel = await get_realm_channel(g.session["realm"]["id"], kwargs.pop("channel_id"))
            if not channel:
                raise APIError(0, "unknown channel", status_code=404)

            if pass_channel:
                kwargs["channel"] = channel
            return await f(*args, **kwargs)
        return wrap
    return deco


@blueprint.route("/realms/<ulid:realm_id>/channels", methods=["POST"])
@authed()
@require_realm(pass_realm=True)
@require_scopes(Scopes.REALM_CHANNEL_CREATE)
async def realm_channel_create(realm):
    payload = await validate_json(
        {"type": str, "name": (str, 60), "topic": (str, 2000)}
    )

    if payload["type"] not in RealmChannelType.ALL:
        raise APIError(0, "invalid channel type")

    channel = serialize_realm_channel(
        await create_realm_channel(
            realm, payload["type"], payload["name"], payload["topic"]
        )
    )
    await dispatch_event("CHANNEL_ADD", channel, realm=realm)
    return jsonify(channel)


@blueprint.route(
    "/realms/<ulid:realm_id>/channels/<ulid:channel_id>", methods=["DELETE"]
)
@authed()
@require_realm(pass_realm=True)
@require_scopes(Scopes.REALM_CHANNEL_DELETE)
async def realm_channel_delete(realm, channel_id):
    channel = await delete_realm_channel(channel_id)
    if not channel:
        raise APIError(0, "channel not found", status_code=404)

    await dispatch_event(
        "CHANNEL_DELETE", serialize_realm_channel(channel), realm=realm
    )
    return "", 204
