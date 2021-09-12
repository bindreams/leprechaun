import atexit
import shutil
import sys
from collections import namedtuple
from datetime import datetime
from functools import wraps
from itertools import chain
from pathlib import Path

import yaml
from PySide2.QtCore import QCoreApplication, QObject, QTimer, Signal
from PySide2.QtGui import QFontDatabase, QIcon
from PySide2.QtWidgets import QApplication, QDialog, QMenu, QSystemTrayIcon
from yaml.parser import ParserError as YamlParserError
from yaml.scanner import ScannerError as YamlScannerError

import leprechaun as le
from leprechaun import notepad
from leprechaun.api import minerstat
from leprechaun.miners import MinerStack
from leprechaun.util import InvalidConfigError, format_exception, isroot
from leprechaun.widgets import Dashboard, ExceptionMessageBox, Setup


# CliApplication =======================================================================================================
Earnings = namedtuple("Earnings", ["total", "pending", "daily"])

class CliApplication(QObject):
    cpuMinerChanged = Signal(str)
    gpuMinerChanged = Signal(str)

    def __init__(self, config_path=None, pipe_log=False):
        super().__init__()

        # Exception catching -------------------------------------------------------------------------------------------
        self.__excepthook__ = sys.excepthook
        sys.excepthook = self.excepthook

        # Folders and logs ---------------------------------------------------------------------------------------------
        le.data_dir.mkdir(exist_ok=True)
        le.miners_dir.mkdir(exist_ok=True)
        le.miner_crashes_dir.mkdir(exist_ok=True)

        if pipe_log:
            self._fp_log = open(le.data_dir / "log.txt", "a", encoding="utf-8", buffering=1)
            atexit.register(self._fp_log.close)
        else:
            self._fp_log = sys.stdout

        self.log("Initializing")
        self.config_path = Path(config_path or "~/leprechaun.yml").expanduser()

        # Qt Application -----------------------------------------------------------------------------------------------
        qapp = QCoreApplication.instance()
        qapp.setApplicationName("leprechaun")

        # Miners -------------------------------------------------------------------------------------------------------
        self.cpuminers = MinerStack(self)
        self.gpuminers = MinerStack(self)
        self.cpuminers.onchange = self.cpuMinerChanged.emit
        self.gpuminers.onchange = self.gpuMinerChanged.emit

        self.heartbeat = QTimer()
        self.heartbeat.setInterval(5000)
        self.heartbeat.timeout.connect(self.update)

        self.paused = False

        # --------------------------------------------------------------------------------------------------------------
        if not isroot:
            self.log("Warning: running without administrator priveleges may be detrimental to mining speed")

    def start(self):
        self.log("Starting")
        self.loadconfig()
        self.heartbeat.start()
        self.update()

    def update(self):
        if not self.paused:
            self.cpuminers.update()
            self.gpuminers.update()

    def loadconfig(self):
        with open(self.config_path, encoding="utf-8") as f:
            config_text = f.read()
        config = yaml.safe_load(config_text)

        if "addresses" in config:
            addresses = config["addresses"]

            for currency, value in addresses.items():
                if value == "<your address here>":
                    raise InvalidConfigError(f"placeholder address for '{currency}' currency")

        self.cpuminers.loadconfig(config, "cpu")
        self.gpuminers.loadconfig(config, "gpu")

    def earnings(self) -> Earnings:
        """Calculate earnings in USD from all miners.

        Returns a named tuple with properties `total`, `pending`, and `daily`. `daily` can be None if not possible to
        calculate at the moment.
        """
        currencies = {miner.currency for miner in chain(self.cpuminers.values(), self.gpuminers.values())}
        try:
            info = minerstat.stats(currencies)
        except OSError as e:
            raise RuntimeError("could not get currency information from minerstat") from e
        info = {coin["coin"]: coin for coin in info}

        used_addresses = set()
        total = 0
        pending = 0
        daily = 0

        for miner in chain(self.cpuminers.values(), self.gpuminers.values()):
            currency = miner.currency
            address = miner.address
            price = info[currency]["price"]
            reward = info[currency]["reward"]  # Reward in coins per 1 H/s for one hour
            if info[currency]["reward_unit"] != currency:
                raise RuntimeError("rewards in units that are not this currency are not supported")

            try:
                if miner.running:
                    hashrate = miner.hashrate()
                    if hashrate is None:
                        daily = None
                    elif daily is not None:
                        daily += miner.hashrate() * reward * price * 24

                if (currency, address) not in used_addresses:
                    total += miner.earnings_total() * price
                    pending += miner.earnings_pending() * price
                    used_addresses.add((currency, address))
            except OSError as e:
                raise RuntimeError(f"could not get earnings of miner '{miner.name}'") from e

        return Earnings(total, pending, daily)

    def exit(self, code=0):
        self.log("Exiting")

        self.cpuminers.stop()
        self.gpuminers.stop()

        QCoreApplication.instance().exit(code)

    def format_log(self, *args):
        timestamp = f"[{datetime.now().isoformat(' ', 'milliseconds')}] "
        padding = " " * len(timestamp)
        prefix = timestamp

        for arg in args:
            if isinstance(arg, BaseException):
                external_lines = format_exception(None, arg, arg.__traceback__)
                lines = (line for external_line in external_lines for line in external_line[:-1].splitlines())
            else:
                lines = str(arg).splitlines()

            for line in lines:
                yield f"{prefix}{line}\n"
                prefix = padding

    def log(self, *args):
        for line in self.format_log(*args):
            self._fp_log.write(line)

    def excepthook(self, etype, value, tb):
        if isinstance(value, KeyboardInterrupt):
            self.log("Keyboard interrupt received")
            self.exit(0)
        else:
            self.log("Fatal exception raised:", value)
            self.exit(1)


# Application ==========================================================================================================
class Application(CliApplication):
    @wraps(CliApplication)
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Icons --------------------------------------------------------------------------------------------------------
        self.icon_active = QIcon(str(le.sdata_dir / "icons" / "icon.png"))
        self.icon_idle   = QIcon(str(le.sdata_dir / "icons" / "icon-idle.png"))

        # Qt Application -----------------------------------------------------------------------------------------------
        qapp = QApplication.instance()
        qapp.setQuitOnLastWindowClosed(False)
        qapp.setApplicationDisplayName("Leprechaun Miner")
        qapp.setWindowIcon(self.icon_active)

        # Notepad for config editing -----------------------------------------------------------------------------------
        self.notepad_dir = le.data_dir / "notepad"
        if not self.notepad_dir.exists():
            self.notepad_dir.mkdir()
            notepad.download(self.notepad_dir)

        # Fonts
        for path in (le.sdata_dir / "fonts").rglob("*.ttf"):
            QFontDatabase.addApplicationFont(str(path))

        # Dashboard ----------------------------------------------------------------------------------------------------
        self.dashboard = None
        """Created and deleted on request to conserve memory."""

        # System tray icon ---------------------------------------------------------------------------------------------
        self.system_icon = QSystemTrayIcon(self.icon_active)
        system_icon_menu = QMenu()
        self.system_icon_status = system_icon_menu.addAction("Initializing")
        self.system_icon_status.setEnabled(False)
        system_icon_menu.addAction("Open Dashboard", self.actionOpenDashboard)
        self.menu_pause = system_icon_menu.addMenu("Pause mining")
        self.menu_pause.addAction("Pause for 5 minutes", lambda: self.actionPauseMining(5 * 60))
        self.menu_pause.addAction("Pause for 20 minutes", lambda: self.actionPauseMining(20 * 60))
        self.menu_pause.addAction("Pause for 1 hour", lambda: self.actionPauseMining(1 * 60 * 60))
        self.menu_pause.addAction("Pause for 8 hours", lambda: self.actionPauseMining(8 * 60 * 60))

        self.action_resume = system_icon_menu.addAction("Resume mining")
        self.action_resume.triggered.connect(self.actionResumeMining)
        self.action_resume.setVisible(False)

        system_icon_menu.addSeparator()
        system_icon_menu.addAction("Exit", self.exit)

        self.system_icon.setContextMenu(system_icon_menu)

    def start(self):
        # Execute user-facing launch as soon as the event loop starts.
        QTimer.singleShot(0, self._impl_start)

    def _impl_start(self):
        """User-facing action triggered on program launch."""
        self.log("Starting")

        try:
            self.loadconfig()
        except FileNotFoundError:
            shutil.copy(le.sdata_dir / "leprechaun-template.yml", self.config_path)

            dialog = Setup(self, Setup.welcome_message)
            if dialog.exec_() == QDialog.Rejected:
                QApplication.instance().exit()
                return
        except (YamlScannerError, YamlParserError, InvalidConfigError) as e:
            dialog = Setup(self, "There has been an error loading the configuration file.")
            dialog.werrorlabel.setText(str(e))
            if dialog.exec_() == QDialog.Rejected:
                QApplication.instance().exit()
                return

        self.system_icon.show()
        self.heartbeat.start()
        self.update()

    def update(self):
        super().update()

        # Status -------------------------------------------------------------------------------------------------------
        if self.cpuminers.active:
            if self.gpuminers.active:
                status = f"{self.cpuminers.active.name} && {self.gpuminers.active.name}"
            else:
                status = self.cpuminers.active.name
        else:
            if self.gpuminers.active:
                status = self.gpuminers.active.name
            else:
                status = "No active miners"

        self.system_icon_status.setText(status)

        # --------------------------------------------------------------------------------------------------------------
        if self.dashboard is not None:
            self.dashboard.update()

    def actionOpenDashboard(self):
        if self.dashboard is None:
            self.dashboard = Dashboard(self)
        self.dashboard.update()

        self.dashboard.show()
        self.dashboard.raise_()
        self.dashboard.activateWindow()

    def actionPauseMining(self, duration):
        self.log(f"Mining paused for {duration}s")
        self.paused = True

        self.cpuminers.stop()
        self.gpuminers.stop()

        self.system_icon_status.setText("Mining paused")
        self.menu_pause.menuAction().setVisible(False)
        self.action_resume.setVisible(True)
        self.system_icon.setIcon(self.icon_idle)

        QTimer.singleShot(duration * 1000, self.actionResumeMining)

    def actionResumeMining(self):
        self.log("Mining resumed")
        self.paused = False

        self.menu_pause.menuAction().setVisible(True)
        self.action_resume.setVisible(False)
        self.system_icon.setIcon(self.icon_active)

        self.update()

    def actionEditConfig(self):
        notepad.launch(self.notepad_dir, self.config_path)

    def excepthook(self, etype, value, tb):
        if not isinstance(value, KeyboardInterrupt):
            wmessage = ExceptionMessageBox(value)
            wmessage.exec_()

        super().excepthook(etype, value, tb)
