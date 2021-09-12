"""Shim that runs Leprechaun GUI. Used during freezing in freeze-gui.spec."""
import sys
from pathlib import Path
import subprocess as sp

if sys.platform == "win32":
    flags = sp.CREATE_NO_WINDOW
else:
    flags = 0

dir = Path(sys.argv[0]).parent
sp.Popen([dir / "leprechaun.exe", "-gp"], creationflags=flags)