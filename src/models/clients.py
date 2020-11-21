import secrets
from mongoengine.fields import StringField, BooleanField
from models.base import BaseDocument


class Client(BaseDocument):
    meta = {
        'collection': 'clients'
    }

    name = StringField(required=True)
    description = StringField()
    is_public = BooleanField()
    is_external = BooleanField()
    secret_key = StringField(null=True)

    def clean(self):
        super().clean()
        if self.pk is None and not self.is_public:
            self.secret_key = secrets.token_urlsafe()