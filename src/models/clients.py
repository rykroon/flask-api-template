import secrets
from mongoengine.fields import StringField, BooleanField
from models.base import BaseDocument


class Client(BaseDocument):
    meta = {
        'abstract': True,
        'allow_inheritance': True,
        'collection': 'clients',
        
    }

    name = StringField(required=True)
    description = StringField()


class PublicClient(Client):
    pass


class ConfidentialClient(Client):
    secret_key = StringField(default=secrets.token_urlsafe)