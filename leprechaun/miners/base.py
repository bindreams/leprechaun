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
        self.currency = None
        self.address = None
        self.enabled = None
        self.broken = False
        self.condition = None

        self.running_process = None
        self.log = deque(maxlen=1000)

        # Parsing configuration ----------------------------------------------------------------------------------------
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
            # If no condition is found, it's okay
            if str(e) != "no condition found":
                raise

    # Abstract methods =================================================================================================
    @abstractmethod
    def earnings(self) -> dict:
        """Return earnings from this miner as a dict.
        The dict must contain the following fields: `total`, `pending`, `scope`.
        The `scope` field scecifies, to how many miners this statistic applies. Variants are: "miner" for only this
        miner, "currency" for all miners of this currency, "address" for all miners for this address, or "with-id" for
        all miners with the same `id` field.
        The `total` and `pending` values need to be in miner's currency.

        Note: all miners for one currency should return the same value for `scope`.
        """

    @abstractmethod
    def process(self):
        """Create a new subprocess.Popen instance running the miner with specified settings."""

    # Properties =======================================================================================================
    @property
    def allowed(self):
        return self.condition is None or self.condition.satisfied()

    @property
    def running(self):
        return self.running_process is not None and self.running_process.returncode is None

    @property
    def returncode(self):
        if self.running_process is None:
            return None
        return self.running_process.returncode

    @property
    def workername(self):
        return f"{platform.node()}/{self.name}"

    # Actions ==========================================================================================================
    def start(self):
        if not self.running:
            self.running_process = self.process()
            Thread(target=self._poll).start()

    def stop(self):
        if self.running:
            self.running_process.terminate()

    # Internal =========================================================================================================
    def _poll(self):
        proc = self.running_process

        for line in iter(proc.stdout.readline, ""):
            line = line.strip()
            if line != "":
                self.log.append(line)
                self.logUpdated.emit(line)

        proc.wait()
        self.processFinished.emit(proc.returncode)

    # ==================================================================================================================
    def __repr__(self):
        return f"{type(self).__name__}(name='{self.name}', enabled={self.enabled}, running={self.running}, broken={self.broken})"
