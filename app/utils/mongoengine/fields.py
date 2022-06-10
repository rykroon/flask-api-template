from dataclasses import is_dataclass, asdict
from inspect import isclass
from tokenize import String

from mongoengine.errors import ValidationError
from mongoengine.fields import DictField, StringField


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


class IdentifierField(StringField):

    def validate(self, value):
        super().validate(value)

        if not value.isidentifier():
            raise ValidationError

        if any(char.isupper() for char in value):
            raise ValidationError

        if not value[0].islower():
            raise ValidationError
