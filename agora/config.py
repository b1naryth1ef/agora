import os
import json
import collections


class Configuration(collections.UserDict):
    def __init__(self, name, default=None):
        self._name = name
        self._default = default or {}
        super().__init__(self._default)

        if os.path.exists(f"{name}.json"):
            with open(f"{name}.json", "r") as f:
                self._load(json.load(f))

    def _load(self, obj, namespace=None):
        namespace = namespace or []

        for k, v in obj.items():
            if isinstance(v, dict):
                self._load(v, namespace=namespace + [k])
            else:
                self.set_path(".".join(namespace + [k]), v)

    def set_path(self, path, value):
        parts = path.split(".")
        obj = self.data
        for part in parts[:-1]:
            obj = obj[part]
        obj[parts[-1]] = value

    def get_path(self, path):
        parts = path.split(".")
        obj = self.data
        for part in parts:
            obj = obj[part]
        return obj


config = Configuration(
    "agora",
    default={
        "instance": {
            "name": "Default Agora Instance",
            "owners": [],
            "max_realms_created_per_user": 0,
            "allow_realm_registration": False,
        }
    },
)
