import leprechaun as le
from leprechaun.base import InvalidConfigError, download_and_extract
from leprechaun.api.ethermine import totaldue, totalpaid
from .base import Miner


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

    def earnings(self):
        paid = totalpaid(self.address)
        pending = totaldue(self.address)

        return {
            "total": paid + pending,
            "pending": pending,
            "scope": "address"
        }
