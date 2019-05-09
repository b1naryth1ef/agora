from functools import wraps

from agora.permissions import get_scope_rules_for_request, scopes_contains
from agora.http.util import APIError


def require_scopes(*scopes, allow_any=False, include_scopes=False):
    def deco(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            rules = get_scope_rules_for_request()
            contains = {scope: scopes_contains(rules, scope) for scope in scopes}

            if (allow_any and True not in contains.values()) or not all(
                contains.values()
            ):
                raise APIError(0, "invalid scopes", 401)

            if include_scopes:
                kwargs["scopes"] = contains

            return fn(*args, **kwargs)

        return wrapper

    return deco
