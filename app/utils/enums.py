import enum


class EnumMeta(enum.EnumMeta):

    def __contains__(cls, member):
        if not isinstance(member, enum.Enum):
            # Allow non-enums to match against member values.
            return any(x.value == member for x in cls)
        return super().__contains__(member)


class Enum(enum.Enum, metaclass=EnumMeta):
    ...


class StrEnum(str, Enum):
    ...

