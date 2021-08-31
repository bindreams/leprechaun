import sys
import traceback
from pathlib import Path
from datetime import datetime
import shutil
import atexit

import yaml
from yaml.parser import ParserError as YamlParserError
from PySide2.QtCore import QObject, QTimer, Signal
from PySide2.QtGui import QIcon, QFontDatabase
from PySide2.QtWidgets import QApplication, QDialog, QSystemTrayIcon, QMenu

import leprechaun as le
from leprechaun import notepad
from .base import InvalidConfigError
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


class Application(QObject, metaclass=ApplicationMetaclass):
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

        # Logs
        self._fp_log = open(le.data_dir / "log.txt", "a", encoding="utf-8", buffering=1)
        self.log("Initializing")
        atexit.register(self._fp_log.close)

        self.config_path = Path(config_path)

        # Qt Application -----------------------------------------------------------------------------------------------
        qapp = QApplication(sys.argv)
        qapp.setQuitOnLastWindowClosed(False)
        qapp.setApplicationName("leprechaun")
        qapp.setApplicationDisplayName("Leprechaun Miner")
        qapp.setWindowIcon(QIcon(str(le.sdata_dir / "icon.png")))

        # Notepad for config editing -----------------------------------------------------------------------------------
        if not le.notepad_dir.exists():
            le.notepad_dir.mkdir()
            notepad.download(le.notepad_dir)

        # Fonts
        for path in (le.sdata_dir / "fonts").rglob("*.ttf"):
            QFontDatabase.addApplicationFont(str(path))

        # Miners -------------------------------------------------------------------------------------------------------
        self.cpuminers = MinerStack()
        self.gpuminers = MinerStack()
        self.cpuminers.onchange = self.cpuMinerChanged.emit
        self.gpuminers.onchange = self.gpuMinerChanged.emit

        self.heartbeat = QTimer()
        self.heartbeat.setInterval(5000)
        self.heartbeat.timeout.connect(self.onHeartbeat)

        # Dashboard ----------------------------------------------------------------------------------------------------
        self.dashboard = None
        """Created and deleted on request to conserve memory."""

        # System tray icon ---------------------------------------------------------------------------------------------
        self.icon_active = QIcon(str(le.sdata_dir / "icon.png"))
        self.icon_idle = QIcon(str(le.sdata_dir / "icon-idle.png"))

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

    def exec(self):
        self.log("Starting")
        # Execute user-facing launch as soon as the event loop starts.
        QTimer.singleShot(0, self.actionLaunch)

        qapp = QApplication.instance()
        return qapp.exec_()

    def onHeartbeat(self):
        self.cpuminers.update()
        self.gpuminers.update()
        
        # Status -------------------------------------------------------------------------------------------------------
        if self.cpuminers.active:
            if self.gpuminers.active:
                status = f"{self.cpuminers.active.name} && {self.gpuminers.active.name}"
            else:
                status = f"{self.cpuminers.active.name}"
        else:
            if self.gpuminers.active:
                status = f"{self.gpuminers.active.name}"
            else:
                status = "No active miners"

        self.system_icon_status.setText(status)

        # --------------------------------------------------------------------------------------------------------------
        if self.dashboard is not None:
            self.dashboard.update()

    def actionLaunch(self):
        """User-facing action triggered on program launch."""
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
        self.onHeartbeat()

    def actionOpenDashboard(self):
        if self.dashboard is None:
            self.dashboard = Dashboard()
        self.dashboard.update()

        self.dashboard.show()
        self.dashboard.raise_()
        self.dashboard.activateWindow()
    
    def actionPauseMining(self, duration):
        self.log(f"Mining paused for {duration}s")

        if self.cpuminers.active:
            self.cpuminers.active.stop()
        
        if self.gpuminers.active:
            self.gpuminers.active.stop()

        self.system_icon_status.setText("Mining paused")
        self.menu_pause.menuAction().setVisible(False)
        self.action_resume.setVisible(True)
        self.system_icon.setIcon(self.icon_idle)
        
        self.heartbeat.stop()
        QTimer.singleShot(duration * 1000, self.actionResumeMining)

    def actionResumeMining(self):
        self.log("Mining resumed")

        self.menu_pause.menuAction().setVisible(True)
        self.action_resume.setVisible(False)
        self.system_icon.setIcon(self.icon_active)

        self.heartbeat.start()
        self.onHeartbeat()

    def actionEditConfig(self):
        notepad.launch(le.notepad_dir, self.config_path)

    def loadconfig(self):
        with open(self.config_path, encoding="utf-8") as f:
            config_text = f.read()
        config = yaml.safe_load(config_text)

        addresses = config["addresses"]
        for currency, value in addresses.items():
            if value == "<your address here>":
                raise InvalidConfigError(f"Placeholder address for '{currency}' currency")
        
        self.cpuminers.loadconfig(config, "cpu")
        self.gpuminers.loadconfig(config, "gpu")

    def exit(self, code=0):
        if self.cpuminers.active:
            self.cpuminers.active.stop()
        
        if self.gpuminers.active:
            self.gpuminers.active.stop()

        self.log("Exiting")
        QApplication.instance().exit(code)

    def log(self, *args):
        timestamp = f"[{datetime.now().isoformat(' ', 'milliseconds')}] "
        padding = " " * len(timestamp)
        prefix = timestamp

        for arg in args:
            if isinstance(arg, BaseException):
                external_lines = traceback.format_exception(None, arg, arg.__traceback__)
                lines = (line for external_line in external_lines for line in external_line[:-1].splitlines())
            else:
                lines = str(arg).splitlines()
        
            for line in lines:
                self._fp_log.write(f"{prefix}{line}\n")
                prefix = padding

    def excepthook(self, etype, value, tb):        
        self.log("Fatal exception raised:", value)
        wmessage = ExceptionMessageBox(value)
        wmessage.exec_()

        self.exit(1)
