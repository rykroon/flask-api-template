from mongoengine.fields import UUIDField
from models.base import BaseDocument
from models import Client, User

class Resource(BaseDocument):
    meta = {
        'abstract': True
    }

    owner_id = UUIDField(required=True)

    


