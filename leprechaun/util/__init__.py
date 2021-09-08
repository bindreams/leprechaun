import ctypes
import os
import shutil
from contextlib import contextmanager
from functools import wraps

from calc import calc as calc_impl
from calc import default_identifiers

__all__ = [
    # Exceptions
    "InvalidConfigError",
    "format_exception",

    # File handling
    "ClosedNamedTemporaryFile",
    "download",
    "extract",
    "download_and_extract",

    # Suprocess management
    "popen",

    # Misc utilities
    "isroot",
    "atleave",
    "calc"
]

from .exceptions import InvalidConfigError, format_exception
from .files import (ClosedNamedTemporaryFile, download, download_and_extract,
                    extract)
from .subprocess import popen

# Misc utilities =======================================================================================================
if os.name == "nt":
    isroot = ctypes.windll.shell32.IsUserAnAdmin() != 0
else:
    isroot = (os.getuid() == 0)


@contextmanager
def atleave(fn):
    """Use during `with` statement to call something at the end regardless of exceptions.

    Example:
    ```
    resource = Resource()
    with atleave(lambda: release(resource)):
        # Work on resource
    ```
    """
    try:
        yield None
    finally:
        fn()

@wraps(calc_impl)
def calc(expr, identifiers=None, unary_operators=None, binary_operators=None):
    if not isinstance(expr, str):
        return expr

    identifiers = default_identifiers | (identifiers or {})
    return calc_impl(expr, identifiers, unary_operators, binary_operators)
