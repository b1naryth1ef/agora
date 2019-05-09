import time

from nacl.signing import SigningKey
from nacl.encoding import Base64Encoder


async def test_auth_challenge_no_key(client):
    response = await client.get("/auth/challenge")
    assert response.status_code == 400
    assert (await response.json) == {"code": 0, "message": "key required"}


async def test_auth_challenge_key(client):
    from agora.http.views.auth import challenge_key

    key = SigningKey.generate()
    pubkey = key.verify_key.encode(encoder=Base64Encoder).decode("utf-8")
    response = await client.get("/auth/challenge", query_string={"key": pubkey})

    assert response.status_code == 200
    json = await response.json
    assert json["challenge"]["timestamp"] < time.time()

    challenge_key.verify_key.verify(
        "{}:{}".format(json["challenge"]["timestamp"], pubkey).encode("utf-8"),
        Base64Encoder.decode(json["challenge"]["value"]),
    )
