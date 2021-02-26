from .context import Context


def contextual(get_response):
    """
    Django middleware.
    """

    def middleware(request):
        try:
            Context.push(request=request)
            return get_response(request)
        finally:
            Context.pop()

    return middleware
