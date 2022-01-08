from secrets import token_urlsafe

from mongoengine.fields import StringField, URLField

from models.base import BaseDocument


class Client(BaseDocument):
    meta = {
        'collection': 'clients'
    }

    name = StringField()
    description = StringField()
    secret_key = StringField()
    webhook_url = URLField()
