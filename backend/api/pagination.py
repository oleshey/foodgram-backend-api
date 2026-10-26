from rest_framework.pagination import PageNumberPagination


class LimitOffsetPagination(PageNumberPagination):
    """
    Пагинация для Foodgram с параметрами page и limit.

    Кастомная пагинация с параметрами page/limit,
    соответствующая схеме OpenAPI Foodgram:
    формат ответа {count, next, previous, results},
    ссылки формируются через параметр page (?page=N).
    """

    page_size = 6
    page_query_param = 'page'
    page_size_query_param = 'limit'
    max_page_size = 1000
