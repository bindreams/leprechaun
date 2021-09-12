"""Shim that runs Leprechaun GUI. Used during freezing in freeze-gui.spec."""
import sys
from pathlib import Path
from subprocess import Popen

dir = Path(sys.argv[0]).parent
Popen([dir / "leprechaun.exe", "-gp"])