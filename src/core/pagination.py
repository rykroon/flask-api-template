from flask import request


class BasePagination:
    def paginate_queryset(self):
        raise NotImplementedError

    def get_paginated_response(self, data):
        raise NotImplementedError


class PageNumberPagination(BasePagination):
    pass


class LimitOffsetPagination(BasePagination):
    limit_query_param = 'limit'
    offset_query_param = 'offset'
    default_limit = None
    max_limit = None

    def paginate_queryset(self, queryset):
        self.limit = self.get_limit()
        self.offset = self.get_offset()
        queryset = queryset[self.offset: self.offset + self.limit]
        return queryset

    def get_paginated_response(self, data):
        pass

    def get_limit(self):
        limit = request.args.get(self.limit_query_param, self.default_limit)
        limit = int(limit)
        if self.max_limit:
            limit = min(limit, self.max_limit)
        return limit

    def get_offset(self):
        offset = request.args.get(self.offset_query_param, 0)
        offset = int(offset)
        return offset


