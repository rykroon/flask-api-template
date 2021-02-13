from mongoengine.fields import ObjectIdField
from models.base import BaseDocument

class Resource(BaseDocument):
    meta = {
        'abstract': True
    }

    client_id = ObjectIdField(required=True)

