import sys
import traceback
from pathlib import Path
from datetime import datetime
import shutil

import yaml
from yaml.parser import ParserError as YamlParserError
from PySide2.QtCore import QObject, QStandardPaths, QTimer, Signal
from PySide2.QtGui import QIcon
from PySide2.QtWidgets import QApplication, QDialog, QStyleFactory, QSystemTrayIcon, QMenu

import leprechaun as package
from .base import InvalidConfigError, download_and_unpack
from .miners import cpuminer, gpuminer
from .widgets import MonacoEditor, Dashboard, ConfigFixDialog, ExceptionMessageBox


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

    def __init__(self):
        super().__init__()
        
        # Exception catching -------------------------------------------------------------------------------------------
        self.__excepthook__ = sys.excepthook
        sys.excepthook = self.excepthook

        # General application information ------------------------------------------------------------------------------
        qapp = QApplication(sys.argv)
        qapp.setQuitOnLastWindowClosed(False)
        #qapp.setStyle(QStyleFactory.create("fusion"))
        qapp.setApplicationName("leprechaun")
        qapp.setApplicationDisplayName("Leprechaun Miner")
        qapp.setWindowIcon(QIcon(str(package.dir / "data" / "icon.png")))

        # Folders and logs ---------------------------------------------------------------------------------------------
        self.data_dir = Path(QStandardPaths.writableLocation(QStandardPaths.AppLocalDataLocation))
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.miners_dir = self.data_dir / "miners"
        self.miners_dir.mkdir(exist_ok=True)

        self.temp_dir = Path(QStandardPaths.writableLocation(QStandardPaths.TempLocation)) / "leprechaun"
        self.temp_dir.mkdir(parents=True, exist_ok=True)

        # Logs
        self._fp_log = open(self.data_dir / "log.txt", "a", encoding="utf-8")
        self.log("Initializing")

        # Monaco editor ------------------------------------------------------------------------------------------------
        monaco_editor_version = "0.27.0"
        monaco_editor_filename = f"monaco-editor-{monaco_editor_version}"
        monaco_editor_url = f"https://registry.npmjs.org/monaco-editor/-/{monaco_editor_filename}.tgz"
        monaco_editor_path = self.data_dir / monaco_editor_filename
        MonacoEditor.index_html = monaco_editor_path / "index.html"
        if not monaco_editor_path.exists():
            download_and_unpack(monaco_editor_url, monaco_editor_path)
            shutil.copy(package.dir / "data" / "monaco-editor.html", MonacoEditor.index_html)

        # # Fonts
        # for path in (package.dir / "data" / "fonts").rglob("*.ttf"):
        #     QFontDatabase.addApplicationFont(str(path))

        # Miners -------------------------------------------------------------------------------------------------------
        self.cpuminers = {}
        self.gpuminers = {}

        self.cpupriorities = []
        self.gpupriorities = []

        self.cpuactive = None
        self.gpuactive = None

        self.heartbeat = QTimer()
        self.heartbeat.setInterval(5000)
        self.heartbeat.timeout.connect(self.onHeartbeat)

        # Dashboard ----------------------------------------------------------------------------------------------------
        self.dashboard = None
        """Created and deleted on request to conserve memory."""

        # System tray icon ---------------------------------------------------------------------------------------------
        self.icon_active = QIcon(str(package.dir / "data" / "icon.png"))
        self.icon_idle = QIcon(str(package.dir / "data" / "icon-idle.png"))

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
        # CPU miners ---------------------------------------------------------------------------------------------------
        cpuactiveminer = self.cpuminers.get(self.cpuactive, None)
        if cpuactiveminer is not None and not cpuactiveminer.running:
            raise RuntimeError(f"Miner '{self.cpuactive}' stopped unexpectedly")

        for minername in self.cpupriorities:
            miner = self.cpuminers[minername]
            if miner.enabled and miner.allowed:
                if self.cpuactive is None or self.cpuactive != minername:
                    if cpuactiveminer is not None:
                        cpuactiveminer.stop()
                    self.cpuactive = minername
                    miner.start()
                    self.cpuMinerChanged.emit(minername)

                break

        # GPU miners ---------------------------------------------------------------------------------------------------
        gpuactiveminer = self.gpuminers.get(self.gpuactive, None)
        if gpuactiveminer is not None and not gpuactiveminer.running:
            raise RuntimeError(f"Miner '{self.gpuactive}' stopped unexpectedly")

        for minername in self.gpupriorities:
            miner = self.gpuminers[minername]
            if miner.allowed and miner.enabled:
                if self.gpuactive is None or self.gpuactive != minername:
                    if gpuactiveminer is not None:
                        gpuactiveminer.stop()
                    self.gpuactive = minername
                    miner.start()
                    self.gpuMinerChanged.emit(minername)
                    
                break
        
        # Status -------------------------------------------------------------------------------------------------------
        if self.cpuactive:
            if self.gpuactive:
                status = f"⛏️ {self.cpuactive} && {self.gpuactive}"
            else:
                status = f"⛏️ {self.cpuactive}"
        else:
            if self.gpuactive:
                status = f"⛏️ {self.gpuactive}"
            else:
                status = "❌ No active miners"

        self.system_icon_status.setText(status)

        # --------------------------------------------------------------------------------------------------------------
        if self.dashboard is not None:
            self.dashboard.update()

    def actionLaunch(self):
        """User-facing action triggered on program launch."""
        config_changed = False

        try:
            with open(Path.home() / "leprechaun.yml", encoding="utf-8") as f:
                config_text = f.read()
        except FileNotFoundError:
            shutil.copy(package.dir / "data" / "leprechaun-template.yml", Path("~/leprechaun.yml").expanduser())
            
            with open(Path.home() / "leprechaun.yml", encoding="utf-8") as f:
                config_text = f.read()
            dialog = ConfigFixDialog.Setup(config_text)
            if dialog.exec_() == QDialog.Rejected:
                QApplication.instance().exit()
                return

            config_text = dialog.weditor.text()
            config_changed = True

        while True:
            try:
                config = yaml.safe_load(config_text)
                self.loadconfig(config)
            except (YamlParserError, InvalidConfigError) as e:
                dialog = ConfigFixDialog.ConfigError(config_text, str(e))
                status = dialog.exec_()
                if status == QDialog.Rejected:
                    QApplication.instance().exit()
                    return

                config_text = dialog.weditor.text()
                config_changed = True
            else:
                break

        # Success, write new config to file
        if config_changed:
            with open(Path.home() / "leprechaun.yml", "w", encoding="utf-8") as f:
                f.write(config_text)
        
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
        self.log("Mining paused for {duration}s")

        if self.cpuactive:
            self.cpuminers[self.cpuactive].stop()
        
        if self.gpuactive:
            self.gpuminers[self.gpuactive].stop()

        self.system_icon_status.setText("💤 Mining paused")
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

    def loadconfig(self, config):
        self.cpuminers = {}
        self.gpuminers = {}

        addresses = config["addresses"]
        for currency, value in addresses.items():
            if value == "<your address here>":
                raise InvalidConfigError(f"Placeholder address for '{currency}' currency")
        
        cpuconfigs = config.get("cpu-miners", {})
        for name, data in cpuconfigs.items():
            try:
                self.cpuminers[name] = cpuminer(name, data, config)
            except InvalidConfigError as e:
                raise InvalidConfigError(f"CPU miner '{name}': {e}") from None
        
        gpuconfigs = config.get("gpu-miners", {})
        for name, data in gpuconfigs.items():
            try:
                self.gpuminers[name] = gpuminer(name, data, config)
            except InvalidConfigError as e:
                raise InvalidConfigError(f"GPU miner '{name}': {e}") from None
        
        self.cpupriorities = sorted(self.cpuminers, key=lambda x: self.cpuminers[x].priority)
        self.gpupriorities = sorted(self.gpuminers, key=lambda x: self.gpuminers[x].priority)

    def exit(self, code=0):
        if self.cpuactive:
            self.cpuminers[self.cpuactive].stop()
        
        if self.gpuactive:
            self.gpuminers[self.gpuactive].stop()

        self.log("Exiting")
        self._fp_log.close()
        QApplication.instance().exit(code)

    def log(self, line):
        time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._fp_log.write(f"[{time}] {line}\n")

    def excepthook(self, etype, value, tb):        
        self.log("Exception occured!")
        for line in traceback.format_exception(None, value, value.__traceback__):
            internal_lines = line[:-1].split("\n")
            for internal_line in internal_lines:
                self.log(internal_line)
        
        wmessage = ExceptionMessageBox(value)
        wmessage.exec_()

        self.exit(1)
