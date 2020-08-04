# standard library imports
from base64 import urlsafe_b64encode
import crypt
from hashlib import sha256
import ipaddress
import os
import secrets
import string

# third party imports
from mongoengine import ValidationError, CASCADE
from mongoengine.fields import BooleanField, EmailField, IntField, ListField, \
    ReferenceField, StringField
from nltk.corpus import words
import requests

# local imports
from core.models import BaseModel


class InvalidPassword(Exception):
    pass


class PasswordPolicy(BaseModel):
    """
        Default values based off of NIST Publication 800-63B
        https://pages.nist.gov/800-63-3/sp800-63b.html
        Section 5.1.1.2 Memorized Secret Verifiers
    """

    min_length = IntField(default=8)
    max_length = IntField(default=64)
    require_lower = BooleanField(default=False)
    require_upper = BooleanField(default=False)
    require_digit = BooleanField(default=False)
    require_special = BooleanField(default=False)
    only_ascii = BooleanField(default=False)
    allow_whitespace = BooleanField(default=True)
    allow_dictionary_words = BooleanField(default=False)
    blacklist = ListField(StringField(), default=list)
    is_active = BooleanField(default=False)

    def get_words(self, min_length=4):
        w = [word.lower() for word in words.words() if len(word) >= min_length]
        return list(set(w))

    def set_blacklist(self):
        url =  "https://raw.githubusercontent.com/danielmiessler/SecLists/master/Passwords/Common-Credentials/10-million-password-list-top-1000000.txt"
        response = requests.get(url)
        if response.ok:
            self.blacklist = response.content.decode().split('\n')

    def validate_password(self, password):
        if self.min_length:
            if len(password) < self.min_length:
                raise InvalidPassword("min_length")

        if self.max_length:
            if len(password) > self.max_length:
                raise InvalidPassword('max_length')

        if self.require_upper:
            if not any([char.isupper() for char in password]):
                raise InvalidPassword('require_upper')

        if self.require_digit:
            if not any(char.isdigit() for char in password):
                raise InvalidPassword('require_digit')

        if self.require_special:
            if not any(char in string.punctuation for char in password):
                raise InvalidPassword('require_special')

        if not self.allow_whitespace:
            if any(char in string.whitespace for char in password):
                raise InvalidPassword('white space not allowed')

        if self.only_ascii:
            if not all([char.is_ascii() for char in password]):
                raise InvalidPassword('only ascii characters are allowed')

        if not self.allow_dictionary_words:
            for word in self.get_words():
                if word in password.lower():
                    raise InvalidPassword('password contains dictionary words')

        if self.blacklist:
            if password in self.blacklist:
                raise InvalidPassword('password is common')

        return True

    def clean(self):
        super().clean()
        if self.is_active == True:
            current_active_policy = self.__class__.objects.filter(is_active=True, pk__ne=self.pk).first()
            if current_active_policy:
                current_active_policy.is_active = False
                current_active_policy.save()


def mksalt():
    return crypt.mksalt(crypt.METHOD_SHA256)


class User(BaseModel):

    email = EmailField(required=True)
    email_verified = BooleanField(default=False)
    phone_number = StringField(null=True)
    phone_number_verified = BooleanField(default=False)
    salt = StringField(default=mksalt)
    password = StringField(required=True)

    def __init__(self, email, password, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.email = email
        self.set_password(password)
        #self.password = password
        #self.failed_login_attempts = 0
        #self.lockout_date = None 
    
    def set_email(self, email):
        self.email = email
        self.email_verified = False

    def set_phone_number(self, phone_number):
        self.phone_number = phone_number
        self.phone_number_verified = False

    def set_password(self, password):
        policy = PasswordPolicy.objects.filter(is_active=True).first()
        if policy:
            policy.validate_password(password)

        salted_password = "{}{}".format(password, self.salt)
        self.password = sha256(salted_password.encode()).hexdigest()

    def check_password(self, password):
        salted_password = "{}{}".format(password, self.salt)
        hashed_password = sha256(salted_password.encode()).hexdigest()
        return self.password == hashed_password


class Resource(BaseModel):
    user = ReferenceField('User', reverse_delete_rule=CASCADE)

    meta = {
        'abstract': True
    }


class Client(BaseModel):
    #from the oauth2.1 draft
    CONFIDENTIAL = 'confidential'
    PUBLIC = 'public'
    TYPES = (CONFIDENTIAL, PUBLIC)

    WEB_APPLICATION = 'web application'
    BROWSER_BASED_APPLICATION = 'browser-based application'
    NATIVE_APPLICATION = 'native application'
    PROFILES = {
        WEB_APPLICATION: CONFIDENTIAL, 
        BROWSER_BASED_APPLICATION: PUBLIC, 
        NATIVE_APPLICATION: PUBLIC
    }

    app_name = StringField(required=True)
    description = StringField(required=True)
    type = StringField(required=True, choices=TYPES)
    profile = StringField(required=True, choices=PROFILES)
    secret = StringField(null=True)

    def __init__(self, app_name, description, profile):
        self.app_name = app_name
        self.description = description
        self.profile = profile
        self.secret = None
        if self.is_confidential():
            self.secret = secrets.token_urlsafe(32)
    
    def clean(self):
        super().clean()
        self.type = self.__class__.PROFILES.get(self.profile)

    def is_confidential(self):
        return self.type == self.__class__.CONFIDENTIAL

    def is_public(self):
        return self.type == self.__class__.PUBLIC


class SecretMixin():
    ttl = None
    nbytes = None #

    def __init__(self, client, user, scope=None):
        self.secret = secrets.token_urlsafe(self.__class__.nbytes)
        self.client_id = client.pk
        self.user_id = user.pk
        self.scope = scope

    @property
    def cache_key(self):
        return self.secret

    def get_client(self):
        return Client.objects.get(pk=self.client_id)

    def get_user(self):
        return User.objects.get(pk=self.user_id)

    def __str__(self):
        return self.pk

    def to_cache(self):
        return super().set(ex=self.__class__.ttl)


class RefreshToken(SecretMixin):
    ttl = 86400 # 1 day
    nbytes = 128


class AccessToken(SecretMixin):
    ttl = 3600 #1 hour
    nbytes = 64


class AuthorizationCode(SecretMixin):
    ttl = 60 #1 minute
    nbytes = 32

    S256 = 'S256'
    PLAIN = 'plain'
    CODE_CHALLENGE_METHODS = (S256, PLAIN)

    def __init__(self, client, user, scope=None):
        super().__init__(client, user, scope)
        self.code_challenge = None
        self.code_challenge_method = None

    def verify_code_challenge(self, code_verifier):
        if self.code_challenge:
            if self.code_challenge_method == self.S256:
                hashed = sha256(code_verifier.encode('ascii')).digest()
                encoded = urlsafe_b64encode(hashed).decode('ascii')
                return self.code_challenge == encoded

            elif self.code_challenge_method == self.PLAIN:
                return self.code_challenge == code_verifier

        return False



