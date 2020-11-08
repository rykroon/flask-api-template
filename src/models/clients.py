import secrets
from mongoengine.fields import StringField
from models.base import BaseDocument


PUBLIC = 'public'
CONFIDENTIAL = 'confidential'
CLIENT_TYPES = (PUBLIC, CONFIDENTIAL)


class Client(BaseDocument):
    name = StringField(required=True)
    description = StringField()
    type = StringField(required=True, choices=CLIENT_TYPES)
    secret = StringField(null=True)

    def clean(self):
        super().clean()
        if self.pk is None and self.type == CONFIDENTIAL:
            self.secret = secrets.token_urlsafe()

    def is_public(self):
        return self.type == PUBLIC