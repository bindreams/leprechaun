import os
from urllib.parse import urlparse
from pathlib import Path
from tempfile import TemporaryDirectory, NamedTemporaryFile
import shutil
from zipfile import ZipFile
from tarfile import TarFile
from contextlib import contextmanager
import ctypes
from calc import calc as calc_impl, default_identifiers
import requests
from better_exceptions import ExceptionFormatter

# OS utilities =========================================================================================================
try:
    elevated = (os.getuid() == 0)
except AttributeError:
    elevated = ctypes.windll.shell32.IsUserAnAdmin() != 0

# Exceptions ===========================================================================================================
class InvalidConfigError(ValueError):
    pass

_exception_formatter = ExceptionFormatter(colored=False, max_length=None)
def format_exception(exc, value, tb):
    return list(_exception_formatter.format_exception(exc, value, tb))

# Misc utilities =======================================================================================================
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

def calc(expr, identifiers=None):
    if not isinstance(expr, str):
        return expr

    identifiers = default_identifiers | (identifiers or {})
    return calc_impl(expr, identifiers)

# File handling utilities ==============================================================================================
@contextmanager
def ClosedNamedTemporaryFile(*, suffix=None, prefix=None, dir=None, errors=None):
    tf = NamedTemporaryFile(suffix=suffix, prefix=prefix, dir=dir, errors=errors, delete=False)
    tf.close()
    try:
        yield tf.name
    finally:
        os.unlink(tf.name)

def download_and_extract(url, dest, callback=None, *, format=None, if_exists=False, remove_nested=False):
    """Download a zip or tar archive and unpack it into a specified folder.
    If `if_exists` is True, download and extract even if the path already exists.
    If `nested` is True, assume the archive contains a single folder with files inside (not files directly).
    """
    dest = Path(dest)
    
    if not if_exists and dest.exists():
        return

    supposed_filename = urlparse(url).path.rsplit("/", 1)[-1]  # Last component of path
    supposed_suffix = "".join(Path(supposed_filename).suffixes)

    with ClosedNamedTemporaryFile(suffix=supposed_suffix) as tempfile:
        if callback is not None:
            cb1 = lambda progress: callback(progress / 2)
            cb2 = lambda progress: callback(0.5 + progress / 2)
        else:
            cb1 = None
            cb2 = None

        download(url, tempfile, cb1)
        extract(tempfile, dest, cb2, format=format, remove_nested=remove_nested)

def download(url, filename, callback=None):
    response = requests.get(url, stream=True)

    with open(filename, "wb") as f:
        length = response.headers.get('content-length')

        if length is None: # no content length header
            f.write(response.content)
        else:
            completed = 0
            length = int(length)
            for data in response.iter_content(chunk_size=4096):
                completed += len(data)
                f.write(data)

                if callback is not None:
                    callback(completed / length)

_formats = {name: extensions for name, extensions, _ in shutil.get_unpack_formats()}

def extract(src, dest, callback=None, *, format=None, if_exists=False, remove_nested=False):
    """Download a zip or tar archive and extract it into a specified folder.
    If `if_exists` is True, download and extract even if the path already exists.
    If `nested` is True, assume the archive contains a single folder with files inside (not files directly).
    """
    src = Path(src)
    
    if not if_exists and dest.exists():
        return

    # Determine format -------------------------------------------------------------------------------------------------
    suffix = "".join(src.suffixes)
    format = None

    for format_check, extensions in _formats.items():
        for extension in extensions:
            if suffix.endswith(extension):
                format = format_check
                break
        
        if format is not None:
            break

    if format is None:
        raise ValueError(f"Could not determine archive format from filename '{src.name}'")
    
    # Extract functions ------------------------------------------------------------------------------------------------
    def extract_tar(dest):
        with TarFile(src) as tf:
            members = tf.getmembers()
            length = len(members)
            completed = 0

            for member in members:
                tf.extract(member, dest)
                completed += 1

                if callback is not None:
                    callback(completed / length)

    def extract_zip(dest):
        with ZipFile(src) as zf:
            members = zf.infolist()
            length = len(members)
            completed = 0

            for member in members:
                zf.extract(member, dest)
                completed += 1

                if callback is not None:
                    callback(completed / length)

    if format in ("tar", "gztar", "bztar", "xztar"):
        extract = extract_tar
    elif format == "zip":
        extract = extract_zip
    else:
        raise ValueError(f"Unknown archive format '{format}'")

    # Extract file -----------------------------------------------------------------------------------------------------
    if remove_nested:
        # Handle nested directory
        with TemporaryDirectory() as tempdir:
            tempdir = Path(tempdir)
            extract(tempdir)
            files = list(tempdir.glob("*"))

            if len(files) != 1:
                raise ValueError("remove_nested set to True, but more than one file found")
            
            file = files[0]
            shutil.copytree(file, dest)
    else:
        extract(dest)
