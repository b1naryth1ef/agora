import json
import functools
import datetime
import uuid
import ulid.api


class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        elif isinstance(obj, datetime.date):
            return obj.isoformat()
        elif isinstance(obj, datetime.timedelta):
            return (datetime.datetime.min + obj).time().isoformat()
        elif isinstance(obj, uuid.UUID):
            return ulid.api.parse(obj).str
        else:
            return super().default(obj)


dumps = functools.partial(json.dumps, cls=JSONEncoder)
