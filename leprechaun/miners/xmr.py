import multiprocessing
import re

import leprechaun as le
from leprechaun.util import InvalidConfigError, calc, download_and_extract
from leprechaun.api.supportxmr import totaldue, totalpaid
from .base import Miner


class XmrMiner(Miner):
    miner_version = "6.14.1"
    miner_url = \
        f"https://github.com/xmrig/xmrig/releases/download/v{miner_version}/xmrig-{miner_version}-msvc-win64.zip"
    miner_dir = le.miners_dir / f"xmrig-{miner_version}"
    miner_exe = miner_dir / "xmrig.exe"

    re_hashrate = \
        re.compile(r"\[\d\d\d\d-\d\d-\d\d \d\d:\d\d:\d\d\.\d\d\d\]  miner    speed 10s\/60s\/15m (\d+.\d|n\/a) (\d+.\d|n\/a) (\d+.\d|n\/a) H\/s")

    def __init__(self, name, data, config):
        super().__init__(name, data, config)

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

    def args(self):
        return [
            self.miner_exe,
            "-o", "pool.supportxmr.com:443",
            "-u", self.address,
            "--rig-id", self.workername,
            "--cpu-priority", str(self.process_priority),
            "-t", str(self.process_threads),
            "-k", "--tls", "--no-color"
        ]

    def hashrate(self):
        fee_coef = 0.99 * 0.994  # Adjust for miner fee, then pool fee

        for line in reversed(self.log):
            m = re.match(self.re_hashrate, line)

            if not m:
                continue

            if m.group(3) != "n/a":
                return float(m.group(3)) * fee_coef
            if m.group(2) != "n/a":
                return float(m.group(2)) * fee_coef
            if m.group(1) != "n/a":
                return float(m.group(1)) * fee_coef

        return None

    def earnings_total(self):
        return totalpaid(self.address) + totaldue(self.address)

    def earnings_pending(self):
        return totaldue(self.address)
