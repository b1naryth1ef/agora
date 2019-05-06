from functools import wraps
from quart import request, g
from nacl.encoding import Base64Encoder
from agora.db.identity import get_identity_by_access_token
from agora.db.realm import get_realm_session_info
from agora.config import config


class APIError(Exception):
    VALIDATION_ERROR = 9000

    def __init__(self, code, message=None, status_code=400):
        super().__init__()
        self.code = code
        self.message = message
        self.status_code = status_code


async def validate_json(schema):
    data = await request.json

    result = {}
    for k, v in schema.items():
        if k not in data:
            raise APIError(APIError.VALIDATION_ERROR, f"missing required key `{k}`")

        if isinstance(v, tuple):
            if v[0] == str:
                if len(data[k]) > v[1]:
                    raise APIError(
                        APIError.VALIDATION_ERROR,
                        f"string value `{data[k]}` for {v} can be a maximum of {v[1]} characters",
                    )

        if not isinstance(data[k], v):
            raise APIError(
                APIError.VALIDATION_ERROR,
                f"incorrect type `{type(data[k])}` for key `{k}` (want: `{v}`)",
            )

        result[k] = data[k]
    return result


def authed(acl=None, require_owner=False):
    def deco(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if not g.identity:
                raise APIError(0, "Authentication Required", status_code=403)

            if require_owner and not g.owner:
                raise APIError(0, "Forbidden", status_code=401)

            return f(*args, **kwargs)

        return wrapper

    return deco


async def authenticate_request(entity):
    if "Authentication" in entity.headers:
        if " " not in entity.headers["Authentication"]:
            raise APIError(0, "Invalid Authentication Header Format")

        method, data = entity.headers["Authentication"].split(" ", 1)
        if method == "Token":
            access_token = Base64Encoder.decode(data)
            g.identity = await get_identity_by_access_token(access_token)

        if not g.identity:
            raise APIError(0, "Invalid Authentication")

        if "realm_id" in request.view_args:
            g.session = await get_realm_session_info(
                g.identity, request.view_args.pop("realm_id")
            )

        g.owner = g.identity["key"] in config["instance"]["owners"]
