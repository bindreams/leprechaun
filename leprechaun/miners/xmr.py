import multiprocessing
import subprocess as sp

import leprechaun as le
from leprechaun.base import InvalidConfigError, calc, download_and_extract
from leprechaun.api.supportxmr import totaldue, totalpaid
from .base import Miner


class XmrMiner(Miner):
    miner_version = "6.14.1"
    miner_url = \
        f"https://github.com/xmrig/xmrig/releases/download/v{miner_version}/xmrig-{miner_version}-msvc-win64.zip"

    def __init__(self, name, data, config):
        super().__init__(name, data, config)

        self.miner_dir = le.miners_dir / f"xmrig-{self.miner_version}"
        self.miner_exe = self.miner_dir / "xmrig.exe"

        download_and_extract(self.miner_url, self.miner_dir, remove_nested=True)

        # Configuration ------------------------------------------------------------------------------------------------
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

        # Process threads
        max_threads = multiprocessing.cpu_count()
        try:
            process_threads = calc(data.get("process-threads", "max"), {"min": 1, "max": max_threads})
            if process_threads != int(process_threads):
                raise InvalidConfigError(f"process thread count must an integer (got '{process_threads}')")

            self.process_threads = int(process_threads)
        except ValueError:
            raise InvalidConfigError("invalid expression in field 'process-threads'") from None

        if not 1 <= self.process_threads <= max_threads:
            raise InvalidConfigError(
                f"process thread count must be in range [1, {max_threads}] (got '{self.process_threads}')"
            )

    def process(self):
        return sp.Popen([
                self.miner_exe,
                "-o", "pool.supportxmr.com:443",
                "-u", self.address,
                "--rig-id", self.workername,
                "--cpu-priority", str(self.process_priority),
                "-t", str(self.process_threads),
                "-k", "--tls", "--no-color"
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
