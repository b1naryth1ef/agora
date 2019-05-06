from quart import Blueprint, jsonify

from agora.config import config

blueprint = Blueprint("instance", __name__)


@blueprint.route("/instance/info")
async def instance_info():
    return jsonify({"name": config["instance"]["name"]})
