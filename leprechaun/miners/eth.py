import leprechaun as le
from leprechaun.base import InvalidConfigError, download_and_extract
from leprechaun.api.ethermine import totaldue, totalpaid
from .base import Miner
import re


class EthMiner(Miner):
    trex_version = "0.21.6"
    trex_url = \
        f"https://github.com/trexminer/T-Rex/releases/download/{trex_version}/t-rex-{trex_version}-win.zip"
    trex_dir = le.miners_dir / f"t-rex-{trex_version}"
    trex_exe = trex_dir / "t-rex.exe"

    nsfminer_version = "1.3.14"
    nsfminer_url = \
        f"https://github.com/no-fee-ethereum-mining/nsfminer/releases/download/v{nsfminer_version}/nsfminer_{nsfminer_version}-windows_10-cuda_11.3-opencl.zip"
    nsfminer_dir = le.miners_dir / f"nsfminer-{nsfminer_version}"
    nsfminer_exe = nsfminer_dir / "nsfminer.exe"

    re_trex_hashrate = re.compile(r"(\d+\.\d\d) MH\/s")
    re_ethminer_hashrate = re.compile(r"(\d+\.\d\d) (h|Kh|Mh)")

    def __init__(self, name, data, config):
        super().__init__(name, data, config)

        self.backend = data.get("backend", "t-rex")
        if self.backend not in ("t-rex", "ethminer"):
            raise InvalidConfigError(f"backend must be one of: 't-rex', 'ethminer' (got '{self.backend}')")

        if self.backend == "t-rex":
            download_and_extract(self.trex_url, self.trex_dir)
        else:
            download_and_extract(self.nsfminer_url, self.nsfminer_dir)

    def args(self):
        if self.backend == "t-rex":
            return [
                self.trex_exe,
                "-a", "ethash",
                "-o", "stratum+tcp://eu1.ethermine.org:4444",
                "-u", self.address,
                "-p", "x",
                "-w", self.workername,
            ]

        return [
            self.nsfminer_exe,
            "-P", f"stratum+ssl://{self.address}.{self.workername}:x@eu1.ethermine.org:5555",
            "--nocolor"
        ]

    def hashrate(self):
        for line in reversed(self.log):
            if self.backend == "t-rex":
                m = re.search(self.re_trex_hashrate, line)
                if not m:
                    continue

                hashrate = float(m.group(1)) * 10**6
                return hashrate * 0.99 * 0.99  # Adjust for miner fee, then pool fee
            else:
                m = re.search(self.re_ethminer_hashrate, line)
                if not m:
                    continue

                if m.group(2) == "h":
                    power = 0
                elif m.group(2) == "Kh":
                    power = 3
                elif m.group(2) == "Mh":
                    power = 6

                hashrate = float(m.group(1)) * 10**power
                return hashrate * 0.99  # Adjust for pool fee

        return None

    def earnings_total(self):
        return totalpaid(self.address) + totaldue(self.address)

    def earnings_pending(self):
        return totaldue(self.address)
