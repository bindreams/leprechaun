from better_exceptions import ExceptionFormatter


class InvalidConfigError(ValueError):
    pass


_exception_formatter = ExceptionFormatter(colored=False, max_length=None)
def format_exception(exc, value, tb):
    return list(_exception_formatter.format_exception(exc, value, tb))
