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
from mongoengine.fields import BooleanField, DateTimeField, EmailField, \
    IntField, ListField, ReferenceField, StringField
from nltk.corpus import words
import requests

# local imports
from core.models import BaseModel
from core.caches import Cache


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
    username = StringField(default='', unique=True, max_length=150)
    first_name = StringField(default='', max_length=150)
    last_name = StringField(default='', max_length=150)

    email = EmailField(null=True)
    email_verified = BooleanField(default=False)
    phone_number = StringField(null=True)
    phone_number_verified = BooleanField(default=False)

    #groups
    #permissions

    salt = StringField(default=mksalt)
    password = StringField(required=True)

    is_staff = BooleanField(deafult=False)
    is_active = BooleanField(default=True)
    is_super_user = BooleanField(default=False)

    last_login = DateTimeField(null=True)

    @property
    def is_anonymous(self):
        return False

    @property
    def is_authenticated(self):
        return True

    def get_username(self):
        return self.username

    def get_full_name(self):
        return '{} {}'.format(self.first_name, self.last_name)

    def set_password(self, password):
        salted_password = "{}{}".format(password, self.salt)
        self.password = sha256(salted_password.encode()).hexdigest()

    def check_password(self, password):
        salted_password = "{}{}".format(password, self.salt)
        hashed_password = sha256(salted_password.encode()).hexdigest()
        return self.password == hashed_password


class AnonymousUser:
    id = None
    pk = None
    username = ''
    is_staff = False
    is_active = False
    is_superuser = False

    def __str__(self):
        return 'AnonymousUser'

    def __eq__(self, other):
        return isinstance(other, self.__class__)

    def __hash__(self):
        return 1  # instances always return the same hash value

    @property
    def is_anonymous(self):
        return True

    @property
    def is_authenticated(self):
        return False
    
    def delete(self):
        raise NotImplementedError
    
    def save(self):
        raise NotImplementedError

    def set_password(self, password):
        raise NotImplementedError

    def check_password(self, password):
        raise NotImplementedError


class Permission(BaseModel):
    pass


class Group(BaseModel):
    pass


class Resource(BaseModel):
    owner = ReferenceField('User', reverse_delete_rule=CASCADE)
    group = ReferenceField('Group', reverse_delete_rule=CASCADE)

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


class Token:

    key_func = secrets.token_urlsafe
    timeout = None

    def __init__(self, user):
        if not isinstance(user, User):
            raise TypeError

        self.user_id = user.pk
        self.key = self.key_func()

    def get_user(self):
        return User.objects.get(pk=self.user_id)

    def save(self):
        cache = Cache(
            key_prefix=self.__class__.__name__, 
            timeout=self.timeout
        )
        cache.set(self.key, self)

    @classmethod
    def get_token(cls, token):
        cache = Cache(key_prefix=cls.__name__)
        return cache.get(token)

    def __str__(self):
        return self.key


class RefreshToken(Token):
    timeout = 86400 # 1 day


class AccessToken(Token):
    timeout = 3600 #1 hour
