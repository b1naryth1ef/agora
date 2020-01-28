from functools import wraps
from quart import request, g
from agora.db.realm import get_realm_session_info
from agora.config import config
from agora.http.util.auth import authenticate_from_token, AuthenticationFailure


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
        try:
            g.identity = await authenticate_from_token(entity.headers["Authentication"])
        except AuthenticationFailure:
            raise APIError(0, "Invalid Authentication")

        if "realm_id" in entity.view_args:
            g.session = await get_realm_session_info(
                g.identity, entity.view_args["realm_id"]
            )

        g.owner = g.identity["key"] in config["instance"]["owners"]
