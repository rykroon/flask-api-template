from dataclasses import is_dataclass, asdict
from inspect import isclass
from typing import Dict

from mongoengine.errors import ValidationError
from mongoengine.fields import DictField


class DataclassField(DictField):

    def __init__(self, dataclass, *args, **kwargs):
        if not isclass(dataclass) and not is_dataclass(dataclass):
            raise TypeError

        self.dataclass = dataclass
        super().__init__(*args, **kwargs)

    def to_python(self, value):
        return self.dataclass(**value)

    def to_mongo(self, value):
        return asdict(value)

    def validate(self, value):
        if not isinstance(value, self.dataclass):
            raise ValidationError
