import sys
from pathlib import Path
from datetime import datetime
import shutil
import atexit

import yaml
from yaml.parser import ParserError as YamlParserError
from PySide2.QtCore import QObject, QTimer, Signal, QCoreApplication
from PySide2.QtGui import QIcon, QFontDatabase
from PySide2.QtWidgets import QApplication, QDialog, QSystemTrayIcon, QMenu

import leprechaun as le
from leprechaun import notepad
from .base import InvalidConfigError, format_exception, elevated
from .widgets import Dashboard, ExceptionMessageBox, Setup
from .miners import MinerStack


class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class ApplicationMetaclass(Singleton, type(QObject)):
    pass


class CliApplication(QObject, metaclass=ApplicationMetaclass):
    cpuMinerChanged = Signal(str)
    gpuMinerChanged = Signal(str)

    def __init__(self, config_path=None):
        super().__init__()

        # Exception catching -------------------------------------------------------------------------------------------
        self.__excepthook__ = sys.excepthook
        sys.excepthook = self.excepthook

        # Folders and logs ---------------------------------------------------------------------------------------------
        le.data_dir.mkdir(exist_ok=True)
        le.miners_dir.mkdir(exist_ok=True)
        le.miner_crashes_dir.mkdir(exist_ok=True)

        self.log("Initializing")
        self.config_path = Path(config_path or "~/leprechaun.yml").expanduser()

        # Qt Application -----------------------------------------------------------------------------------------------
        qapp = QCoreApplication.instance()
        qapp.setApplicationName("leprechaun")

        # Miners -------------------------------------------------------------------------------------------------------
        self.cpuminers = MinerStack()
        self.gpuminers = MinerStack()
        self.cpuminers.onchange = self.cpuMinerChanged.emit
        self.gpuminers.onchange = self.gpuMinerChanged.emit

        self.heartbeat = QTimer()
        self.heartbeat.setInterval(5000)
        self.heartbeat.timeout.connect(self.update)

        self.paused = False

        # --------------------------------------------------------------------------------------------------------------
        if not elevated:
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

        addresses = config["addresses"]
        for currency, value in addresses.items():
            if value == "<your address here>":
                raise InvalidConfigError(f"placeholder address for '{currency}' currency")
        
        self.cpuminers.loadconfig(config, "cpu")
        self.gpuminers.loadconfig(config, "gpu")

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
            print(line, end="")

    def excepthook(self, etype, value, tb):
        if isinstance(value, KeyboardInterrupt):
            self.log("Keyboard interrupt received")
            self.exit(0)
        else:
            self.log("Fatal exception raised:", value)
            self.exit(1)


class Application(CliApplication):
    def __init__(self, config_path=None):
        self._fp_log = open(le.data_dir / "log.txt", "a", encoding="utf-8", buffering=1)
        atexit.register(self._fp_log.close)
        
        super().__init__()

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
        self.system_icon_menu = QMenu()
        self.system_icon_status = self.system_icon_menu.addAction("Initializing")
        self.system_icon_status.setEnabled(False)
        self.system_icon_menu.addAction("Open Dashboard", self.actionOpenDashboard)
        self.menu_pause = self.system_icon_menu.addMenu("Pause mining")
        self.menu_pause.addAction("Pause for 5 minutes", lambda: self.actionPauseMining(5 * 60))
        self.menu_pause.addAction("Pause for 20 minutes", lambda: self.actionPauseMining(20 * 60))
        self.menu_pause.addAction("Pause for 1 hour", lambda: self.actionPauseMining(1 * 60 * 60))
        self.menu_pause.addAction("Pause for 8 hours", lambda: self.actionPauseMining(8 * 60 * 60))

        self.action_resume = self.system_icon_menu.addAction("Resume mining")
        self.action_resume.triggered.connect(self.actionResumeMining)
        self.action_resume.setVisible(False)

        self.system_icon_menu.addSeparator()
        self.system_icon_menu.addAction("Exit", self.exit)

        self.system_icon.setContextMenu(self.system_icon_menu)

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
        
            dialog = Setup(Setup.welcome_message)
            if dialog.exec_() == QDialog.Rejected:
                QApplication.instance().exit()
                return
        except (YamlParserError, InvalidConfigError) as e:
            dialog = Setup("There has been an error loading the configuration file.")
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
            self.dashboard = Dashboard()
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

    def log(self, *args):
        for line in self.format_log(*args):
            self._fp_log.write(line)

    def excepthook(self, etype, value, tb):
        if not isinstance(value, KeyboardInterrupt):
            wmessage = ExceptionMessageBox(value)
            wmessage.exec_()

        super().excepthook(etype, value, tb)
