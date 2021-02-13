import secrets
from mongoengine.fields import StringField, BooleanField
from models.base import BaseDocument


class Client(BaseDocument):
    meta = {
        'collection': 'clients',
        
    }

    name = StringField(required=True)
    description = StringField()
    secret_key = StringField(default=secrets.token_urlsafe)
