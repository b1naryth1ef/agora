from quart import Blueprint, jsonify, g
from functools import wraps

from chat.redis import dispatch_event
from chat.db.realm import (
    create_realm,
    serialize_realm,
    count_realms_by_user,
    serialize_realm_member,
    get_realm_with_membership_by_id,
)
from chat.http.util import authed, validate_json, APIError

blueprint = Blueprint("realm", __name__)

MAX_REALMS_PER_USER = 1


def with_realm(admin=False):
    def deco(f):
        @wraps(f)
        async def wrap(*args, **kwargs):
            realm = await get_realm_with_membership_by_id(
                g.identity, kwargs.pop("realm_id")
            )
            if not realm:
                raise APIError(0, "not found", status_code=404)

            kwargs["member"] = realm["member"]
            kwargs["realm"] = realm
            return await f(*args, **kwargs)

        return wrap

    return deco


@blueprint.route("/realm", methods=["POST"])
@authed()
async def realm_create():
    payload = await validate_json({"name": str, "public": bool})

    if len(payload["name"]) > 64:
        raise APIError(0, "name can be up to 64 characters long")

    count = await count_realms_by_user(g.identity)
    if count >= MAX_REALMS_PER_USER:
        raise APIError(0, "you already have the maximum number of realms per user")

    realm, member = serialize_realm(await create_realm(g.identity, **payload))
    realm["member"] = serialize_realm_member(member)
    dispatch_event("REALM_ADD", realm, member=member)
    return jsonify(serialize_realm(realm))
