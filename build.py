from pathlib import Path
import subprocess as sp
dir = Path(__file__).parent

sp.run(["pyinstaller", dir / "freeze.spec"], check=True)
sp.run(["pyinstaller", dir / "freeze-cli.spec"], check=True)
