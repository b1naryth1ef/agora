from quart import Blueprint, jsonify, g

from chat.db.identity import serialize_identity
from chat.http.util import authed

blueprint = Blueprint("identity", __name__)


@blueprint.route("/identity/@me")
@authed()
async def identity_me():
    return jsonify(serialize_identity(g.identity))
