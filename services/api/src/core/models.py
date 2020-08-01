from datetime import datetime
import pickle

from mongoengine import Document, DateTimeField

from core.db import redis0


class BaseDocument(Document):
    date_created = DateTimeField(required=True)
    date_updated = DateTimeField(required=True)

    meta = {
        'allow_inheritance': True,
        'abstract': True
    }

    def clean(self):
        if self.pk is None:
            self.date_created = datetime.utcnow()
        self.date_updated = datetime.utcnow()

    def to_dict(self):
        return self.to_mongo().to_dict()


class Cache:

    def __contains__(self, key):
        return key in redis0

    def add(self, key, value, timeout=None):
        value = self._to_pickle(value)
        return redis0.set(key, value, ex=timeout, nx=True)

    def get(self, key, default=None):
        value = redis0.get(key)
        if value is None:
            return default
        value = self._from_pickle(value)
        return value

    def set(self, key, value, timeout=None):
        value = self._to_pickle(value)
        return redis0.set(key, value, ex=timeout)

    def delete(self, key):
        return redis0.delete(key) == 1

    def _to_pickle(self, value):
        if not isinstance(value, (bytes, str, int, float)):
            value = pickle.dumps(value)
        return value

    def _from_pickle(self, value):
        if not isinstance(value, bytes):
            return value

        try:
            return pickle.loads(value)
        except pickle.UnpicklingError:
            return value


class CacheMixin:

    @property
    def cache_key(self):
        raise NotImplementedError

    @property
    def cache(self):
        if not hasattr(self, '_cache'):
            self._cache = Cache()
        return self._cache

    def to_cache(self, timeout=None):
        key = '{}:{}'.format(self.__class__.__name__, self.cache_key)
        self.cache.set(key, self, timeout=timeout)

    @classmethod
    def from_cache(cls, key):
        cache = Cache()
        key = '{}:{}'.format(cls.__name__, key)
        return cache.get(key)
