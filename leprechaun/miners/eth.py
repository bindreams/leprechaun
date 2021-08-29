import subprocess as sp

import leprechaun
from leprechaun.base import InvalidConfigError, calc, download_and_extract
from leprechaun.api.ethermine import totaldue, totalpaid
from .base import Miner


class EthMiner(Miner):
    miner_version = "0.21.6"
    miner_url = \
        f"https://github.com/trexminer/T-Rex/releases/download/{miner_version}/t-rex-{miner_version}-win.zip"

    def __init__(self, name, data, config):
        super().__init__(name, data, config)
        app = leprechaun.Application()

        self.miner_dir = app.miners_dir / f"t-rex-{self.miner_version}"
        self.miner_exe = self.miner_dir / "t-rex.exe"

        download_and_extract(self.miner_url, self.miner_dir)

        # Configuration ------------------------------------------------------------------------------------------------
        if sum(1 for field in ("fan-speed", "max-temp", "max-mem-temp") if field in data) > 1:
            raise InvalidConfigError(
                "only one of the fields 'fan-speed' 'max-temp' 'max-mem-temp' can be specified at a time"
            )
        
        self.temperature_config = None

        if "fan-speed" in data:
            val = round(calc(data["fan-speed"], {"min": 0, "max": 100}))
            self.temperature_config = f"{val}"

        if "max-temp" in data:
            val = round(calc(data["max-temp"], {"max": 90}))
            self.temperature_config = f"t:{val}"
        
        if "max-mem-temp" in data:
            val = round(calc(data["max-mem-temp"], {"max": 90}))
            self.temperature_config = f"tm:{val}"

        try:
            self.low_load = int(data.get("low-load-mode", False))
            if self.low_load not in (0, 1):
                raise InvalidConfigError(f"'low-load-mode' field must be true or false, got '{self.low_load}'")
        except ValueError:
            raise InvalidConfigError("invalid value for field 'low-load-mode' (need true or false)") from None

        # Process priority
        try:
            process_priority = calc(data.get("process-priority", 2), {"min": 0, "max": 5})
            if process_priority != int(process_priority):
                raise InvalidConfigError(f"process priority must an integer (got '{process_priority}')")

            self.process_priority = int(process_priority)
        except ValueError:
            raise InvalidConfigError("invalid expression in field 'process-priority'") from None

        if not 0 <= self.process_priority <= 5:
            raise InvalidConfigError(f"process priority must be in range [0, 5] (got '{self.process_priority}')")
        
    def process(self):
        if self.temperature_config is None:
            temperature_parameters = []
        else:
            temperature_parameters = ["--fan", self.temperature_config]

        return sp.Popen([
                self.miner_exe,
                "-a", "ethash",
                "-o", "stratum+tcp://eu1.ethermine.org:4444",
                "-u", self.address,
                "-p", "x",
                "-w", self.workername,
                "--cpu-priority", str(self.process_priority),
                *temperature_parameters
            ],
            stdin=sp.DEVNULL,
            stdout=sp.PIPE,
            stderr=sp.STDOUT,
            text=True,
            creationflags=sp.CREATE_NO_WINDOW
        )

    def earnings(self):
        paid = totalpaid(self.address)
        pending = totaldue(self.address)
        
        return {
            "total": paid + pending,
            "pending": pending,
            "scope": "address"
        }
