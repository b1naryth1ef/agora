import json
from fnmatch import fnmatch

from quart import g
from agora.config import config


class Scopes(object):
    """
    Scopes define all the possible permisable actions an identity could take.
    """

    REALM_CHANNEL_CREATE = "realm.channel.create"
    REALM_CHANNEL_UPDATE = "realm.channel.update"
    REALM_CHANNEL_DELETE = "realm.channel.delete"
    REALM_CHANNEL_VIEW = "realm.channel.view"

    REALM_CHANNEL_MESSAGE_CREATE = "realm.channel.message.create"
    REALM_CHANNEL_MESSAGE_UPDATE = "realm.channel.message.update"
    REALM_CHANNEL_MESSAGE_DELETE = "realm.channel.message.delete"
    REALM_CHANNEL_MESSAGE_SELF_UPDATE = "realm.channel.message.self.update"
    REALM_CHANNEL_MESSAGE_SELF_DELETE = "realm.channel.message.self.delete"
    REALM_CHANNEL_MESSAGE_VIEW = "realm.channel.message.view"


def get_scope_rules_for_request():
    if g.identity["key"] in config["instance"]["owners"]:
        return ["*"]

    if not g.session:
        return []

    if g.session["member"]["is_admin"]:
        return ["realm.*"]

    scopes = set()
    for role in g.session["member_roles"]:
        # TODO: lol
        granted_scopes = json.loads(role["granted_scopes"])
        scopes |= set(granted_scopes.keys())

    return scopes


def scopes_contains(scope_rules, wanted_scope):
    for scope_rule in scope_rules:
        if fnmatch(wanted_scope, scope_rule):
            return True
    return False


INITIAL_DEFAULT_REALM_ROLE_SCOPE_RULES = {
    "realm.channel.view": {},
    "realm.channel.message.create": {},
    "realm.channel.message.self.*": {},
    "realm.channel.message.view": {},
}
