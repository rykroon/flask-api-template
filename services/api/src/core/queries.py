from bson.objectid import ObjectId, InvalidId
from pymongo import ASCENDING, DESCENDING


class NoResultFound(Exception):
    pass


class MultipleResultsFound(Exception):
    pass


class BaseQuery:
    def __init__(self, model_class):
        self.model_class = model_class
        self._cache = []
        self._iterator = None
        self._as_model = True

    def __iter__(self):
        if self._cache:
            return iter(self._cache)
        self._iterator = self._get_iterator()
        return self

    def __len__(self):
        return len(self._cache)

    def __next__(self):
        result = self._iterator.__next__()
        if self._as_model:
            if type(result) == dict:
                result = self.model_class.from_dict(result)
            elif type(result) == bytes:
                result = self.model_class.from_bytes(result)
        self._cache.append(result)
        return result

    def _get_iterator(self):
        """
            Returns an iterator
        """
        raise NotImplementedError

    def all(self):
        """
            Return the results represented by this Query as a list.
        """
        return list(self)

    def filter(self, **kwargs):
        raise NotImplementedError

    def first(self):
        self.limit(1)
        return self.one_or_none()

    def get(self, id):
        """
            Return an instance based on the given primary key identifier, or None if not found.
        """
        raise NotImplementedError

    def limit(self, limit):
        raise NotImplementedError

    def offset(self, offset):
        raise NotImplementedError

    def one(self):
        """
            Return exactly one result or raise an exception.
        """
        results = self.all()
        if not results:
            raise NoResultFound

        elif len(results) > 1:
            raise MultipleResultsFound

        return results[0]

    def one_or_none(self):
        """
            Return at most one result or raise an exception
        """
        try:
            return self.one()
        except NoResultFound:
            return None

    def sort(self, *args):
        raise NotImplementedError

    def values(self, *args):
        raise NotImplementedError


class MongoQuery(BaseQuery):
    def __init__(self, model_class):
        super().__init__(model_class)
        self._fields = None
        self._filter = {}
        self._limit = None
        self._offset = None
        self._sort = []

    def _get_iterator(self):
        #the iterator is a pymongo cursor
        cursor = self.model_class.collection.find(self._filter, self._fields)
        if self._limit:
            cursor.limit(self._limit)

        if self._offset:
            cursor.skip(self._offset)

        if self._sort:
            cursor.sort(self._sort)

        return cursor

    def filter(self, **kwargs):
        self._filter = kwargs
        return self

    def get(self, id):
        try:
            object_id = ObjectId(id)
        except InvalidId:
            object_id = id

        q = self.filter(_id=object_id)
        result = q.one_or_none()
        return result

    def limit(self, limit):
        self._limit = limit
        return self

    def offset(self, offset):
        self._offset = offset
        return self

    def sort(self, *args):
        self._sort = [(arg[1:], DESCENDING) if arg.startswith('-') else (arg, ASCENDING) for arg in args]
        return self

    def values(self, *args):
        self._as_model = False
        self._fields = args or None
        return self.all()


class RedisQuery(BaseQuery):
    """
        Since Redis is a key/value store it is difficult to actually query data
        So the only option is to get one specific key or all the keys for a particular model
    """
    def _get_iterator(self):
        pattern = "{}*".format(self.model_class.__name__)
        keys = self.model_class.connection.keys(pattern)
        return iter(self.model_class.connection.mget(keys))

    def get(self, id):
        key = "{}:{}".format(self.model_class.__name__, id)
        b = self.model_class.connection.get(key)
        if b:
            return self.model_class.from_bytes(b)
        return None