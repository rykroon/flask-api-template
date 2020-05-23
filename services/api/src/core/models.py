from datetime import datetime
import json
import pickle

from core.db import mongo, redis0
from core.descriptors import CollectionDescriptor, QueryDescriptor
from core.queries import MongoQuery, RedisQuery


class SerializableObject:
    """
        An object that can be converted to or created from the following types.
        - Python Dictionary
        - JSON string
        - Bytes
    """

    def to_bytes(self):
        return pickle.dumps(self)

    def to_dict(self, include=None, exclude=None):
        """
            :param include: a list of attributes to include
            :type include: list or None
            :param exclude: a list of attributes to exclude
            :type exclude: list or None
            :return: a dictionary
            :rtype: dict
            :raises ValueError: if both include and exclude are truthy

        """
        if include and exclude:
            raise ValueError("Cannot pass both an include and an exclude")

        d = dict(vars(self))

        if include:
            return {k: v for k, v in d.items() if k in include}

        elif exclude:
            return {k: v for k, v in d.items() if k not in exclude}

        return d


    def to_json(self, encoder=None, include=None, exclude=None):
        """
            :param encoder: A class to use as the encoder
            :type encoder: a subclass of json.JSONEncoder
            :param include: a list of attributes to include
            :type include: list or None
            :param exclude: a list of attributes to exclude
            :type exclude: list or None
            :return: a json string
            :rtype: str
        """
        return json.dumps(self.to_dict(include=include, exclude=exclude), cls=encoder)

    @classmethod
    def from_bytes(cls, b):
        instance = pickle.loads(b)
        if type(instance) != cls:
            raise TypeError
        return instance

    @classmethod
    def from_dict(cls, d, setattrs=False):
        """
            :param d: a dictionary
            :type d: dict
            :param setattrs: If set to True it will call the `setattr` function for each key/value in the dictionary,
                otherwise it will set the instance's __dict__ attribute to `d`
            :type seattrs: bool
        """
        instance = cls.__new__(cls)
        
        if setattrs:
            for k, v in d.items(): setattr(instance, k, v)
        else:
            instance.__dict__ = d

        return instance

    @classmethod
    def from_json(cls, j, decoder=None, setattrs=False):
        """
            :param j: a json string
            :type j: str
            :param setattrs: is passed to from_dict()
            :type seattrs: bool
        """
        d = json.loads(j, cls=decoder)
        return cls.from_dict(d, setattrs=setattrs)


class BaseModel(SerializableObject):
    """
        An Implementation of a Model
        Inspired by other popular python ORMs such as
        Django and SQLAlchemy
    """

    primary_key_field = None

    def __eq__(self, other):
        if not isinstance(other, BaseModel):
            return NotImplemented

        if type(self) != type(other):
            return False

        if self.pk is None:
            return self is other

        return self.pk == other.pk

    def __hash__(self):
        if self.pk is None:
            raise TypeError("Model instances without a primary key value are unhashable")
        return hash(self.pk)

    def __repr__(self):
        return "{}(id={})".format(self._cls.__name__, self.pk)

    def __str__(self):
        return "{} object ({})".format(self._cls.__name__, self.pk)

    @property
    def pk(self):
        try:
            return getattr(self, self.__class__.primary_key_field)
        except AttributeError:
            return None

    @property
    def _cls(self):
        return self.__class__

    def delete(self):
        raise NotImplementedError

    def save(self):
        raise NotImplementedError


class MongoModel(BaseModel):
    """
        A model backed by a Mongodb Database
    """

    client = mongo
    collection_name = None 
    database_name = None
    collection = CollectionDescriptor()
    query = QueryDescriptor(MongoQuery)
    primary_key_field = '_id'

    def delete(self):
        self.__class__.collection.delete_one({'_id': self.pk})

    def save(self):
        if self.pk is None:
            self.date_created = datetime.utcnow()
            self.date_updated = datetime.utcnow()
            result = self.__class__.collection.insert_one(self.to_dict())
            self._id = result.inserted_id
        else:
            self.date_updated = datetime.utcnow()
            self.__class__.collection.update_one(
                {'_id': self.pk}, 
                {'$set': self.to_dict()}
            )


class RedisModel(BaseModel):
    """
        A model backed by a redis key-value store
    """

    connection = redis0
    ttl = None
    keepttl = True 
    query = QueryDescriptor(RedisQuery)

    @property
    def _key(self):
        if self.pk:
            return "{}:{}".format(self._cls.__name__, self.pk)
        return None

    def delete(self):
        self._cls.connection.delete(self._key)

    def save(self):
        if self._cls.keepttl and self._key in self._cls.connection:
            self._cls.connection.set(self._key, self.to_bytes(), keepttl=True)
        else:
            self._cls.connection.set(self._key, self.to_bytes(), ex=self._cls.ttl)


class RefField:
    """
        A descriptor used to reference other Models
    """
    def __init__(self, model_class):
        self.model_class = model_class

    def __get__(self, instance, owner):
        if instance is None:
            return self

        try:
            id = getattr(instance, self.attr_name)
        except AttributeError:
            return None
            
        return self.model_class.query.get(id)

    def __set__(self, instance, value):
        if value is None:
            setattr(instance, self.attr_name, value)

        elif isinstance(value, self.model_class):
            setattr(instance, self.attr_name, value.pk)
            
        else:
            raise TypeError

    def __delete__(self, instance):
        delattr(instance, self.attr_name)

    def __set_name__(self, owner, name):
        self.name = name
        self.attr_name = "{}_id".format(self.name)
