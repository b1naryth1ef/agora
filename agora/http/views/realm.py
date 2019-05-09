from quart import Blueprint, jsonify, g
from functools import wraps

from agora.config import config
from agora.redis import dispatch_event
from agora.db.realm import (
    get_realm,
    create_realm,
    serialize_realm,
    count_realms_by_user,
    serialize_realm_member,
    create_realm_membership,
)
from agora.http.util import authed, validate_json, APIError

blueprint = Blueprint("realm", __name__)


def require_realm(pass_realm=False, pass_member=False):
    def deco(f):
        @wraps(f)
        async def wrap(*args, **kwargs):
            if not g.session:
                raise APIError(0, "unknown realm", status_code=404)

            if pass_realm:
                kwargs["realm"] = g.session["realm"]

            if pass_member:
                kwargs["member"] = g.session["member"]

            return await f(*args, **kwargs)

        return wrap

    return deco


@blueprint.route("/realms", methods=["POST"])
@authed()
async def realm_create():
    if not g.owner and not config["instance"]["allow_realm_registration"]:
        raise APIError(0, "realm registration is disabled", 401)

    payload = await validate_json({"name": str, "public": bool})

    if len(payload["name"]) > 64:
        raise APIError(0, "name can be up to 64 characters long")

    async with g.conn.transaction():
        if not g.owner:
            count = await count_realms_by_user(g.identity)
            if count >= config.get_path("instance.max_realms_created_per_user"):
                raise APIError(
                    0, "you already have the maximum number of realms per user"
                )

        realm, member = await create_realm(g.identity, **payload)

    realm = serialize_realm(realm)
    realm["member"] = serialize_realm_member(member)
    await dispatch_event("REALM_ADD", realm, member=member)
    return jsonify(realm)


@blueprint.route("/realms/<ulid:realm_id>/join", methods=["POST"])
@authed()
async def realm_join(realm_id):
    realm = await get_realm(realm_id)
    if not realm or (not g.owner and not realm["is_public"]):
        raise APIError(0, "realm not found", status_code=404)

    member = await create_realm_membership(realm, g.identity["id"])

    realm = serialize_realm(realm)
    realm["member"] = serialize_realm_member(member)
    await dispatch_event("REALM_ADD", realm, member=member)
    return jsonify(realm)


@blueprint.route("/realms/<ulid:realm_id>", methods=["DELETE"])
@require_realm(pass_realm=True)
@authed()
async def realm_delete(realm):
    if not g.owner and not g.identity["id"] == realm["owner_id"]:
        raise APIError(0, "forbidden", 401)

    payload = await validate_json({"name": str, "public": bool})

    if len(payload["name"]) > 64:
        raise APIError(0, "name can be up to 64 characters long")

    async with g.conn.transaction():
        if not g.owner:
            count = await count_realms_by_user(g.identity)
            if count >= config.get_path("instance.max_realms_created_per_user"):
                raise APIError(
                    0, "you already have the maximum number of realms per user"
                )

        realm, member = await create_realm(g.identity, **payload)

    realm = serialize_realm(realm)
    realm["member"] = serialize_realm_member(member)
    await dispatch_event("REALM_ADD", realm, member=member)
    return jsonify(realm)
