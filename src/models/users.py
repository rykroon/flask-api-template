import crypt
from hashlib import sha256
from mongoengine.fields import BooleanField, EmailField, StringField
from models.base import BaseDocument


def mksalt():
    return crypt.mksalt(crypt.METHOD_SHA256)


class User(BaseDocument):
    username = StringField(required=True, unique=True)
    salt = StringField(required=True, default=mksalt)
    password = StringField(required=True)

    email_address = EmailField(required=True)
    email_address_verified = BooleanField()

    def set_password(self, password):
        salted_password = '{}{}'.format(password, self.salt)
        self.password = sha256(salted_password.encode()).hexdigest()

    def check_passsword(self, password):
        salted_password = '{}{}'.format(password, self.salt)
        hashed_password = sha256(salted_password.encode()).hexdigest()
        return self.password == hashed_password

