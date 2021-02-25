from .context import push, pop


def contextual(get_response):
    """
    Django middleware.
    """

    def middleware(request):
        try:
            push(request=request)
            return get_response(request)
        finally:
            pop()

    return middleware
