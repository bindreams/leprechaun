from collections.abc import MutableMapping
from typing import Union
from datetime import datetime
import leprechaun as le
from leprechaun.base import InvalidConfigError
from .xmr import XmrMiner
from .eth import EthMiner


class MinerStack(MutableMapping):
    def __init__(self):
        super().__init__()

        self.miners = {}
        self.active_name = None
        self.onchange = None
    
    @property
    def active(self):
        return self.get(self.active_name, None)

    def loadconfig(self, config, type: Union["cpu", "gpu"]):
        if type == "cpu":
            data = config.get("cpu-miners", {})
        elif type == "gpu":
            data = config.get("gpu-miners", {})
        else:
            raise ValueError("Unknown value for parameter 'type'")
        
        self.clear()

        for miner_name, miner_data in data.items():
            try:
                self[miner_name] = miner(type, miner_name, miner_data, config)
            except InvalidConfigError as e:
                raise InvalidConfigError(f"{type.upper()} miner '{miner_name}': {e}") from None

    def update(self):
        """Traverse the stack and maybe switch the miner for another miner."""
        active = self.active

        if active is not None and not active.running:
            log_path = le.miner_crashes_dir / f"{datetime.now().isoformat(' ', 'milliseconds')} {active.name}.txt"
            with open(log_path, "w", encoding="utf-8") as f:
                for line in active.log:
                    f.write(line)
            
            raise RuntimeError(f"Miner '{active.name}' stopped unexpectedly")

        for name, miner in self.items():
            if miner.enabled and miner.allowed:
                if self.active_name != name:
                    if active is not None:
                        active.stop()
                    
                    miner.start()
                    self.active_name = name
                    self._impl_onchange(name)

                break
        else:
            if active is not None:
                active.stop()
            self.active_name = None
            self._impl_onchange(None)
    
    def _impl_onchange(self, name):
        if self.onchange is not None:
            self.onchange(name)

    def __getitem__(self, key):
        return self.miners[key]
    
    def __setitem__(self, key, value):
        self.miners[key] = value
    
    def __delitem__(self, key):
        del self.miners[key]
    
    def __iter__(self):
        return iter(self.miners)
    
    def __len__(self):
        return len(self.miners)


def miner(type: Union["cpu", "gpu"], name, data, config):
    try:
        currency = data["currency"]
    except KeyError:
        raise InvalidConfigError("missing property 'currency'") from None
    
    if type == "cpu":
        # CPU miners ---------------------------------------------------------------------------------------------------
        if currency == "XMR":
            return XmrMiner(name, data, config)
        else:
            raise InvalidConfigError(f"no known CPU miners for currency '{currency}'")
    elif type == "gpu":
        # GPU miners ---------------------------------------------------------------------------------------------------
        if currency == "ETH":
            return EthMiner(name, data, config)
        # elif currency == "GRLC":
        #     return GrlcMiner(name, data, config)
        else:
            raise InvalidConfigError(f"no known GPU miners for currency '{currency}'")
    else:
        raise ValueError("Unknown value for parameter 'type'")
