import ulid.api

from quart.routing import BaseConverter


class ULIDConverter(BaseConverter):
    def to_python(self, value):
        return ulid.api.parse(value)
