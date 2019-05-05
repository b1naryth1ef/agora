from quart import Quart, jsonify, g, request, websocket

from chat.redis import init_redis
from chat.db import init_db, acquire, release
from .util import APIError, authenticate_request
from .views.auth import blueprint as auth_blueprint
from .views.identity import blueprint as identity_blueprint
from .views.stream import blueprint as stream_blueprint
from .views.realm import blueprint as realm_blueprint
from .views.channel import blueprint as channel_blueprint

app = Quart(__name__)
app.register_blueprint(auth_blueprint)
app.register_blueprint(identity_blueprint)
app.register_blueprint(stream_blueprint)
app.register_blueprint(realm_blueprint)
app.register_blueprint(channel_blueprint)


@app.before_first_request
async def before_first_request():
    await init_db("postgres://chat@localhost/chat")
    await init_redis("redis://localhost/8")


@app.before_request
async def before_request():
    g.conn = await acquire()
    g.identity = None
    await authenticate_request(request)


@app.before_websocket
async def before_websocket():
    g.conn = await acquire()
    g.identity = None
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
