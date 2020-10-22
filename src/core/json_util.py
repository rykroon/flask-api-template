from bson import DBRef, Decimal128, ObjectId
from bson.errors import InvalidId
from datetime import datetime, date, time
from decimal import Decimal
import json
from uuid import UUID


class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, bytes):
            return o.decode()
        if isinstance(o, (datetime, date, time)):
            return o.isoformat()
        if isinstance(o, (Decimal, Decimal128)):
            return float(str(o))
        if isinstance(o, (UUID, ObjectId)):
            return str(o)
        if isinstance(o, DBRef):
            return o.id
        return super().default(o)


class JSONDecoder(json.JSONDecoder):
    pass