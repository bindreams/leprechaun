from pathlib import Path

dir = Path(__file__).parent
sdata_dir = dir / "data"  # Static data dir
data_dir = Path.home() / "AppData" / "Local" / "leprechaun"
miners_dir = data_dir / "miners"
notepad_dir = data_dir / "notepad"
miner_crashes_dir = data_dir / "miner crashes"

from .application import Application
