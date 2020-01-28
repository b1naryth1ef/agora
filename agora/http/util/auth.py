from nacl.encoding import Base64Encoder
from agora.db.identity import get_identity_by_access_token


class AuthenticationFailure(Exception):
    pass


async def authenticate_from_token(token):
    if " " not in token:
        raise AuthenticationFailure("Invalid Format")

    token_type, token_value = token.split(" ", 1)
    if token_type == "Token":
        access_token = Base64Encoder.decode(token_value)
        identity = await get_identity_by_access_token(access_token)
        if not identity:
            raise AuthenticationFailure("Invalid Authentication")
        return identity
    else:
        raise AuthenticationFailure("Invalid Token Type")
