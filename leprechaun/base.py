from urllib.request import urlretrieve
from urllib.parse import urlparse
from pathlib import Path
from tempfile import TemporaryDirectory
import shutil
from calc import calc as calc_impl, default_identifiers

class InvalidConfigError(ValueError):
    pass

def calc(expr, identifiers=None):
    if not isinstance(expr, str):
        return expr

    identifiers = default_identifiers | (identifiers or {})
    return calc_impl(expr, identifiers)

def download_and_unpack(url, dest, if_exists=False, nested=False):
    """Download a zip or tar archive and unpack it into a specified folder.
    If `if_exists` is True, download and extract even if the path already exists.
    If `nested` is True, assume the archive contains a single folder with files inside (not files directly).
    """
    dest = Path(dest)
    urlfilename = urlparse(url).path.rsplit("/", 1)[-1]

    if dest.exists() and not if_exists:
        return

    with TemporaryDirectory() as tempdir:
        tempdir = Path(tempdir)
        archivepath = tempdir / urlfilename
        unpackdir = tempdir / "unpacked"
        urlretrieve(url, archivepath)
        shutil.unpack_archive(archivepath, unpackdir)
        
        if nested:
            files = list(unpackdir.glob("*"))

            if len(files) != 1:
                raise ValueError("nested set to True, but more than one file found")
            
            file = files[0]
            shutil.copytree(file, dest)
        else:
            shutil.copytree(unpackdir, dest)
