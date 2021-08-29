import sys
from abc import ABC, abstractmethod
from collections import deque
import platform
from threading import Thread

from PySide2.QtCore import QObject, Signal

from leprechaun.base import InvalidConfigError
from leprechaun.conditions import condition


class MinerMetaclass(type(ABC), type(QObject)):
    pass


class Miner(ABC, QObject, metaclass=MinerMetaclass):
    logUpdated = Signal(str)
    processFinished = Signal(int)

    def __init__(self, name, data, config):
        super().__init__()
        self.name = name

        # Generic properties -------------------------------------------------------------------------------------------
        if "currency" not in data:
            raise InvalidConfigError("missing property 'currency'")
        self.currency = data["currency"]
        
        try:
            self.address = data["address"]
        except KeyError:
            addresses = config["addresses"]
            if self.currency not in addresses:
                raise InvalidConfigError(f"wallet address for currency {self.currency} not found") from None
            
            self.address = addresses[self.currency]
        
        self.enabled = data.get("enabled", True)
        
        try:
            self.condition = condition(data)
        except InvalidConfigError as e:
            if str(e) == "no condition found":
                self.condition = None
            else:
                raise
        
        self.log = deque(maxlen=1000)

        # Private variables --------------------------------------------------------------------------------------------
        self._running_process = None
    
    @property
    def allowed(self):
        return self.condition is None or bool(self.condition)

    @property
    def running(self):
        return self._running_process is not None and self._running_process.returncode is None

    @property
    def returncode(self):
        if self._running_process is None:
            return None
        return self._running_process.returncode

    @property
    def workername(self):
        return f"{platform.node()}/{self.name}"
    
    @abstractmethod
    def process(self):
        """Create a new subprocess.Popen instance running the miner with specified settings."""

    def start(self):
        if not self.running:
            self._running_process = self.process()
            Thread(target=self.poll).start()

    def stop(self):
        if self.running:
            self._running_process.terminate()

    def poll(self):
        proc = self._running_process

        for line in iter(proc.stdout.readline, ""):
            line = line.strip()
            if line != "":
                self.log.append(line)
                self.logUpdated.emit(line)

        proc.wait()
        self.processFinished.emit(proc.returncode)

    @abstractmethod
    def earnings(self) -> dict:
        """Return earnings from this miner as a dict.
        The dict must contain the following fields: `total`, `pending`, `scope`.
        The `scope` field scecifies, to how many miners this statistic applies. Variants are: "miner" for only this
        miner, "currency" for all miners of this currency, "address" for all miners for this address, or "with-id" for
        all miners with the same `id` field.
        The `total` and `pending` values need to be in miner's currency.

        Note: all miners for one currency should return the same value for `scope`.
        Note: `id` field should not start with two underscores.
        """
