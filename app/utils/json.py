from dataclasses import is_dataclass, asdict
from datetime import datetime, date, time
from decimal import Decimal
import json
from uuid import UUID

from bson import ObjectId
from mongoengine import Document


JSON_SEPARATORS = (',', ':')


class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, bytes):
            return obj.decode()

        if isinstance(obj, (datetime, date, time)):
            return obj.isoformat()

        if is_dataclass(obj):
            return asdict(obj)

        if isinstance(obj, Decimal):
            return float(obj)

        if isinstance(obj, (ObjectId, UUID)):
            return str(obj)

        if isinstance(obj, Document):
            return obj._data

        return super().default(obj)


class JSONDecoder(json.JSONDecoder):
    pass