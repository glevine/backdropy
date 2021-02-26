import logging
from .context import Context


class ContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        for key, value in Context.data:
            setattr(record, key, value)

        return super().filter(record)


class ContextFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        msg = super().format(record)
        context = ''.join([f'[{key}={value}]' for key, value in Context.data])

        return f'{context} {msg}'
