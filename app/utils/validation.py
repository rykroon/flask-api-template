

_Undefined = object()


class ValidationDict(dict):

    def get(self, key: str, type_: type, /, default=_Undefined):
        allow_null = default is None
        required = default is _Undefined
        value = self[key] if required else super().get(key, default)
        
        ...

