from pathlib import Path
from appdirs import user_data_dir

__version__ = "0.4.0"

dir = Path(__file__).parent
sdata_dir = dir / "data"  # Static data dir
data_dir = Path(user_data_dir("leprechaun", appauthor=False, roaming=False))
miners_dir = data_dir / "miners"
miner_crashes_dir = data_dir / "miner-crashes"
