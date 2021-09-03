from collections.abc import MutableMapping
from typing import Union, Optional, Callable
from datetime import datetime

import win32api
import win32con
import win32job

import leprechaun as le
from leprechaun.base import InvalidConfigError
from .xmr import XmrMiner
from .eth import EthMiner
from .base import Miner

class MinerStack(MutableMapping):
    # Create a Job Object - a container for running processes in Windows that ensures that child processes will die
    # Borrowed from https://stackoverflow.com/a/23587108
    hJob = win32job.CreateJobObject(None, "")
    extended_info = win32job.QueryInformationJobObject(hJob, win32job.JobObjectExtendedLimitInformation)
    extended_info['BasicLimitInformation']['LimitFlags'] = win32job.JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
    win32job.SetInformationJobObject(hJob, win32job.JobObjectExtendedLimitInformation, extended_info)

    perms = win32con.PROCESS_TERMINATE | win32con.PROCESS_SET_QUOTA

    def __init__(self, app):
        super().__init__()
        self.app = app

        self.miners: dict[str, Miner] = {}
        self.active_name: Optional[str] = None
        self.onswitch: Optional[Callable] = None
    
    @property
    def active(self):
        return self.get(self.active_name, None)
    
    @active.setter
    def active(self, value):
        if value is None:
            self.active_name = None
        else:
            self.active_name = value.name

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
            active.broken = True

            log_filename = f"[{datetime.now().isoformat(' ', 'milliseconds').replace(':', '.')}] {active.name}.txt"
            log_path = le.miner_crashes_dir / log_filename
            with open(log_path, "w", encoding="utf-8") as f:
                for line in active.log:
                    f.write(line + "\n")
            
            self.app.log(f"Miner '{active.name}' stopped unexpectedly.\nMiner log available as '{log_filename}'")

        for name, miner in self.items():
            if miner.enabled and miner.allowed and not miner.broken:
                if self.active_name != name:
                    self.switch(miner)

                break
        else:
            self.stop()
    
    def switch(self, new_miner: Union[str, Miner, None]):
        """Switch to a new miner."""
        active = self.active

        if active is not None:
            active.stop()
        
        if isinstance(new_miner, str):
            new_miner = self[new_miner]
        
        if new_miner is not None:
            new_miner.start()

            # Assign new process to a Job, ensuring it will die if Leprechaun crashes
            hProcess = win32api.OpenProcess(self.perms, False, new_miner.running_process.pid)
            win32job.AssignProcessToJobObject(self.hJob, hProcess)
        
        self.active = new_miner
        self._impl_onswitch(active, new_miner)

    def stop(self):
        """Stop the active miner."""
        self.switch(None)

    def _impl_onswitch(self, old, new):
        if self.onswitch is not None:
            self.onswitch(old, new)

    def __getitem__(self, key) -> Miner:
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
