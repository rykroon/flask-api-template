
class DictAttrDescriptor:
    """
        Access the keys in a dictionary using dot notation
    """
    def __init__(self, dict_name):
        self.dict_name = dict_name

    def __get__(self, instance, owner):
        if instance is None:
            return self

        dict_attr = self._get_dict(instance)
        try:
            return dict_attr[self.name]
        except KeyError:
            raise AttributeError("'{}' object has no attribute '{}'".format(owner.__name__, self.name))

    def __set__(self, instance, value):  
        dict_attr = self._get_dict(instance)
        dict_attr[self.name] = value 

    def __set_name__(self, owner, name):
        self.name = name

    def __delete__(self, instance):
        dict_attr = self._get_dict(instance)
        try:
            del dict_attr[self.name]
        except KeyError as e:
            raise AttributeError(e)

    def _get_dict(self, instance):
        try:
            return getattr(instance, self.dict_name)
        except AttributeError:
            dict_attr = {}
            setattr(instance, self.dict_name, dict_attr)
            return dict_attr



class CollectionDescriptor:
    def __get__(self, instance, owner):
        if instance is not None:
            raise AttributeError("Collection isn't accessible via {} instances".format(owner.__name__))
        return owner.client[owner.database_name][owner.collection_name]


class QueryDescriptor:
    def __init__(self, query_class):
        self.query_class = query_class

    def __get__(self, instance, owner):
        if instance is not None:
            raise AttributeError("Query isn't accessible via {} instances".format(owner.__name__))
        return self.query_class(owner)