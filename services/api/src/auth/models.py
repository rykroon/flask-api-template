# standard library imports
from base64 import urlsafe_b64encode
import crypt
from datetime import datetime, timedelta
from hashlib import sha256
import os
import secrets
import string

# third party imports
from email_validator import EmailNotValidError, validate_email
from nltk.corpus import words
import requests

# local imports
from core.models import MongoModel, RedisModel, RefField
from core.descriptors import DictAttrDescriptor


class InvalidPassword(Exception):
    pass


class OpenIdConnectMixin:
    """
        A Mixin Class for users
    """

    SCOPES = {
        'profile': (
            'name', 
            'family_name', 
            'given_name', 
            'middle_name', 
            'nickname', 
            'preferred_username', 
            'profile', 
            'picture', 
            'website', 
            'gender', 
            'birthdate', 
            'zoneinfo', 
            'locale', 
            'updated_at'
        ),
        'email': (
            'email', 
            'email_verified'
        ),
        'address': (
            'address', 
        ),
        'phone': (
            'phone_number', 
            'phone_number_verified'
        )
    }

    formatted = DictAttrDescriptor('address')
    street_address = DictAttrDescriptor('address')
    locality = DictAttrDescriptor('address')
    region = DictAttrDescriptor('address')
    postal_code = DictAttrDescriptor('address')
    country = DictAttrDescriptor('address')

    def info(self, scopes=['profile', 'email', 'address', 'phone']):
        claims = []
        for scope in scopes:
            claims.extend(self.__class__.SCOPES.get(scope))

        d = dict(vars(self))
        info = {k: v for k, v in d.items() if k in claims}
        info['sub'] = self.pk
        return info


class PasswordPolicy(MongoModel):
    database_name = 'auth_db'
    collection_name = 'password_policies'

    def __init__(self, min_length=8, max_length=64, 
        require_alpha=False, require_lower=False, require_upper=False, require_digit=False, require_special=False, 
        allow_whitespace=True, allow_unicode=True, allow_dictionary_words=False, blacklist=[]):
        self.min_length = min_length
        self.max_length = max_length
        self.require_alpha = require_alpha
        self.require_lower = require_lower
        self.require_upper = require_upper
        self.require_digit = require_digit
        self.require_special = require_special
        self.allow_whitespace = allow_whitespace
        self.allow_unicode = allow_unicode
        self.allow_dictionary_words = allow_dictionary_words
        self.blacklist = blacklist
        self.is_active = False

    def get_words(self, min_length=4):
        w = [word.lower() for word in words.words() if len(word) >= min_length]
        return list(set(w))

    def is_unicode(self, s):
        try:
            s.encode('ascii')
            return False
        except UnicodeEncodeError:
            return True

    def set_blacklist(self):
        url =  "https://raw.githubusercontent.com/danielmiessler/SecLists/master/Passwords/Common-Credentials/10-million-password-list-top-1000000.txt"
        response = requests.get(url)
        if response.ok:
            self.blacklist = response.content.decode().split('\n')

    def validate_password(self, password, raise_exc=True):
        if self.min_length:
            if len(password) < self.min_length:
                if raise_exc:
                    raise InvalidPassword("min_length")
                return False

        if self.max_length:
            if len(password) > self.max_length:
                if raise_exc:
                    raise InvalidPassword('max_length')
                return False

        if self.require_alpha:
            if not any([char.isalpha() for char in password]):
                if raise_exc:
                    raise InvalidPassword('require_alpha')
                return False

        if self.require_lower:
            if not any([char.islower() for char in password]):
                if raise_exc:
                    raise InvalidPassword('require_lower')
                return False

        if self.require_upper:
            if not any([char.isupper() for char in password]):
                if raise_exc:
                    raise InvalidPassword('require_upper')
                return False

        if self.require_digit:
            if not any(char.isdigit() for char in password):
                if raise_exc:
                    raise InvalidPassword('require_digit')
                return False

        if self.require_special:
            if not any(char in string.punctuation for char in password):
                if raise_exc:
                    raise InvalidPassword('require_special')
                return False

        if not self.allow_whitespace:
            if any(char in string.whitespace for char in password):
                if raise_exc:
                    raise InvalidPassword('white space not allowed')
                return False

        if not self.allow_unicode:
            if self.is_unicode(password):
                if raise_exc:
                    raise InvalidPassword('unicode not allowed')
                return False

        if not self.allow_dictionary_words:
            for word in self.get_words():
                if word in password.lower():
                    if raise_exc:
                        raise InvalidPassword('password contains dictionary words')
                    return False

        if self.blacklist:
            if password in self.blacklist:
                if raise_exc:
                    raise InvalidPassword('password is common')
                return False

        return True

    def save(self):
        if self.is_active == True:
            current_active_policy = self.__class__.query.filter(is_active=True, _id={'$ne': self.pk}).one_or_none()
            if current_active_policy:
                current_active_policy.is_active = False
                current_active_policy.save()
        
        super().save()


class User(MongoModel, OpenIdConnectMixin):
    database_name = 'auth_db'
    collection_name = 'users'

    def __init__(self, email, password):
        self.email = email
        self.salt = crypt.mksalt(crypt.METHOD_SHA256)
        self.password = password
        self.failed_login_attempts = 0
        self.lockout_date = None      

    def __setattr__(self, attr, value):
        if attr == 'email':
            self._set_email(value)

        elif attr == 'password':
            self._set_password(value)

        elif attr == 'phone_number':
            self._set_phone_number(value)

        else:
            return super().__setattr__(attr, value)

    def _set_email(self, email):
        try:
            validate_email(email)
        except EmailNotValidError as e:
            raise ValueError("Invalid email")

        self.__dict__['email'] = email
        self.email_verified = False

    def _set_password(self, password):
        policy = PasswordPolicy.query.filter(is_active=True).one_or_none()
        if policy:
            policy.validate_password(password)

        salted_password = "{}{}".format(password, self.salt)
        self.__dict__['password'] = sha256(salted_password.encode()).hexdigest()

    def _set_phone_number(self, phone_number):
        self.__dict__['phone_number'] = phone_number
        self.phone_number_verified = False

    def check_password(self, password):
        salted_password = "{}{}".format(password, self.salt)
        hashed_password = sha256(salted_password.encode()).hexdigest()
        return self.password == hashed_password

    def save(self):
        self.updated_at = datetime.utcnow().timestamp()
        super().save()


class Resource(MongoModel):
    database_name = 'resource_db'
    user = RefField(User)


class Client(MongoModel):
    database_name = 'auth_db'
    collection_name = 'clients'

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

    def __init__(self, app_name, description, profile):
        self.app_name = app_name
        self.description = description
        self.profile = profile

        self.secret = None
        if self.is_confidential():
            self.secret = secrets.token_urlsafe(32)

    def __setattr__(self, attr, value):
        if attr == 'profile':
            self._set_profile(value)
        if attr == 'type':
            raise AttributeError("can't set attribute")
        else:
            super().__setattr__(attr, value)

    def _set_profile(self, profile):
        if profile not in self.__class__.PROFILES:
            raise ValueError("Invalid client profile")
        self.__dict__['profile'] = profile
        self.__dict__['type'] = self.__class__.PROFILES[self.profile]

    def is_confidential(self):
        return self.type == self.__class__.CONFIDENTIAL

    def is_public(self):
        return self.type == self.__class__.PUBLIC


class SecretMixin(RedisModel):
    nbytes = None #
    client = RefField(Client)
    user = RefField(User)

    def __init__(self, client, user, scope=None):
        self.__dict__[self._cls.primary_key_field] = secrets.token_urlsafe(self._cls.nbytes)
        self.client = client
        self.user = user
        self.scope = scope

    def __str__(self):
        return self.pk


class RefreshToken(SecretMixin, RedisModel):
    primary_key_field = 'token'
    ttl = 86400 # 1 day
    nbytes = 128


class AccessToken(SecretMixin, RedisModel):
    primary_key_field = 'token'
    ttl = 3600 #1 hour
    nbytes = 64


class AuthorizationCode(SecretMixin, RedisModel):
    primary_key_field = 'code'
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


