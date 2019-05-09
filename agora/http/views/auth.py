import time

from quart import Blueprint, request, jsonify
from agora.db.identity import create_or_update_identity
from agora.http.util import APIError, validate_json

from nacl.exceptions import BadSignatureError
from nacl.encoding import Base64Encoder
from nacl.signing import VerifyKey, SigningKey

SIGNING_WINDOW = 30

blueprint = Blueprint("auth", __name__)
challenge_key = SigningKey.generate()


@blueprint.route("/auth/challenge")
async def auth_challenge():
    values = await request.values
    if "key" not in values:
        raise APIError(0, "key required")

    timestamp = int(time.time())
    challenge_data = "{}:{}".format(timestamp, values["key"])
    challenge = challenge_key.sign(challenge_data.encode("utf-8"))

    return jsonify(
        {
            "challenge": {
                "value": Base64Encoder.encode(challenge.signature).decode("utf-8"),
                "timestamp": timestamp,
            }
        }
    )


@blueprint.route("/auth/join", methods=["POST"])
async def auth_join():
    signature = request.headers.get("X-Challenge-Signature")
    if not signature:
        raise APIError(0, "Signature Required")

    signature = Base64Encoder.decode(signature)

    raw_data = await request.data
    data = await validate_json({"key": str, "challenge": dict, "identity": dict})

    # First validate the users signature
    try:
        key = VerifyKey(data["key"], encoder=Base64Encoder)
        key.verify(raw_data, signature)
    except BadSignatureError:
        raise APIError(0, "Invalid Signature")

    # Next validate our challenge signature
    try:
        challenge_key.verify_key.verify(
            "{}:{}".format(data["challenge"]["timestamp"], data["key"]).encode("utf-8"),
            Base64Encoder.decode(data["challenge"]["value"]),
        )
    except BadSignatureError:
        raise APIError(0, "Bad Challenge Signature")

    delta = time.time() - data["challenge"]["timestamp"]
    if delta < 0 or delta > SIGNING_WINDOW:
        raise APIError(0, "Bad Challenge Timestamp")

    # Ensure we create/update this identity in the DB
    identity = await create_or_update_identity(data["key"], **data["identity"])

    return jsonify(
        {"access_token": Base64Encoder.encode(identity["access_token"]).decode("utf-8")}
    )
