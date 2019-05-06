import os

from quart import Quart, jsonify, g, request, websocket

from agora.redis import init_redis
from agora.db import init_db, acquire, release
from agora.util.json import JSONEncoder
from .util import APIError, authenticate_request
from .util.converter import ULIDConverter
from .views.auth import blueprint as auth_blueprint
from .views.channel import blueprint as channel_blueprint
from .views.identity import blueprint as identity_blueprint
from .views.instance import blueprint as instance_blueprint
from .views.message import blueprint as message_blueprint
from .views.realm import blueprint as realm_blueprint
from .views.stream import blueprint as stream_blueprint

app = Quart(__name__)
app.json_encoder = JSONEncoder
app.url_map.converters["ulid"] = ULIDConverter

# Register all our blueprints
app.register_blueprint(auth_blueprint)
app.register_blueprint(channel_blueprint)
app.register_blueprint(identity_blueprint)
app.register_blueprint(instance_blueprint)
app.register_blueprint(message_blueprint)
app.register_blueprint(realm_blueprint)
app.register_blueprint(stream_blueprint)


@app.before_first_request
async def before_first_request():
    pg_url = os.getenv("AGORA_PG_URL", "postgres://agora:agora@localhost/agora")
    redis_url = os.getenv("AGORA_REDIS_URL", "redis://localhost/8")
    await init_db(pg_url)
    await init_redis(redis_url)


@app.before_request
async def before_request():
    g.conn = await acquire()
    g.identity = None
    g.owner = False
    g.session = None
    await authenticate_request(request)


@app.before_websocket
async def before_websocket():
    g.conn = await acquire()
    g.identity = None
    g.owner = False
    g.session = None
    await authenticate_request(websocket)


@app.after_request
async def after_request(res):
    await release(g.conn)
    return res


@app.errorhandler(APIError)
def handle_api_error(e):
    res = jsonify({"code": e.code, "message": e.message})
    res.status_code = e.status_code
    return res
