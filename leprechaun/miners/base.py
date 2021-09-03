from abc import ABC, abstractmethod
from collections import deque
import platform
from threading import Thread
import shlex
import subprocess as sp

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
        self.extra_backend_args = None

        self.running_process = None
        self.log = deque(maxlen=1000)

        # Parsing configuration ----------------------------------------------------------------------------------------
        if "currency" not in data:
            raise InvalidConfigError("missing field 'currency'")
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

        self.extra_backend_args = data.get("extra-backend-args", [])
        if isinstance(self.extra_backend_args, str):
            self.extra_backend_args = shlex.split(self.extra_backend_args)

        if not isinstance(self.extra_backend_args, list):
            raise InvalidConfigError("field 'extra-backend-args' must be a list or a string")

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
    def args(self):
        """Return a list of command-line arguments required to launch the process, like for subprocess.run.

        Example: return [leprechaun.miners_dir / "ethminer" / "ethminer.exe", "--pool", "..."]
        """

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
            self.running_process = sp.Popen(self.args() + self.extra_backend_args,
                stdin=sp.DEVNULL,
                stdout=sp.PIPE,
                stderr=sp.STDOUT,
                text=True,
                creationflags=sp.CREATE_NO_WINDOW
            )
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
