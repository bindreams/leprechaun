from functools import lru_cache
from PySide6.QtGui import QFontDatabase
from PySide6.QtWidgets import QApplication, QWidget

@lru_cache(maxsize=None)
def logicalDpi():
    """Return this application's logical dpi"""
    # Check if the application has been created. If the application has not been created, dpi cannot be measured.
    if QApplication.instance() is None:
        raise RuntimeError("dpi(): Must construct a QApplication before measuring dpi")

    w = QWidget()
    return w.logicalDpiX()


def rempt():
    """Return default application font size in points."""
    return defaultfont().pointSizeF()

def rem():
    """Return default application font size in pixels."""
    return rempt() / 72 * logicalDpi()

def font(family: str, style: str = "Regular", size: float = None):
    size = size or rempt()
    fd = QFontDatabase()

    font = fd.font(family, style, round(size))
    font.setPointSizeF(size)
    return font

def defaultfont():
    return QApplication.instance().font()