import sys
import traceback
from pathlib import Path
from collections import deque
from datetime import datetime
import win32api
import yaml
from PySide2.QtCore import QStandardPaths, QTimer, QUrl
from PySide2.QtGui import QIcon, QDesktopServices
from PySide2.QtWidgets import QApplication, QSystemTrayIcon, QMenu

import lepricon as package
from lepricon.miner import Miner
from lepricon.dashboard import Dashboard


def idleTime():
    return (win32api.GetTickCount() - win32api.GetLastInputInfo()) / 1000.0

class Lepricon:
    def __init__(self):
        super().__init__()

        # Exception catching -------------------------------------------------------------------------------------------
        self.__excepthook__ = sys.excepthook
        sys.excepthook = self.excepthook

        # Data and logs ------------------------------------------------------------------------------------------------
        self.app_data_dir = Path(QStandardPaths.writableLocation(QStandardPaths.AppLocalDataLocation))
        self.app_data_dir.mkdir(parents=True, exist_ok=True)

        # Logs
        self.fp_log = open(self.app_data_dir / "log.txt", "a", encoding="utf-8")
        self.deque_log = deque(maxlen=1000)
        self.log("Initializing")

        # Miners -------------------------------------------------------------------------------------------------------
        with open(Path.home() / "lepricon.yml") as f:
            self.config = yaml.safe_load(f)

        self.weak_miner = Miner(
            self.config["address"],
            "lw-weak",
            self.config["weak-priority"],
            self.config["weak-threads"]
        )

        self.strong_miner = Miner(
            self.config["address"],
            "lw-strong",
            self.config["strong-priority"],
            self.config["strong-threads"]
        )

        self.heartbeat = QTimer()
        self.heartbeat.setInterval(5000)
        self.heartbeat.timeout.connect(self.updateMiners)

        self.weak_miner.logUpdated.connect(self.logRaw)
        self.strong_miner.logUpdated.connect(self.logRaw)

        # System tray icon ---------------------------------------------------------------------------------------------
        self.icon_active = QIcon(str(package.dir / "data/icon.png"))
        self.icon_idle = QIcon(str(package.dir / "data/icon-idle.png"))

        self.system_icon = QSystemTrayIcon(self.icon_active)
        self.system_icon_menu = QMenu()
        self.system_icon_status = self.system_icon_menu.addAction("Initializing")
        self.system_icon_status.setEnabled(False)
        self.system_icon_menu.addAction("Open Dashboard", self.openDashboard)
        self.system_icon_menu.addAction("Open Pool Dashboard", self.openPoolDashboard)
        self.menu_pause = self.system_icon_menu.addMenu("Pause mining")
        self.menu_pause.addAction("Pause for 5 minutes", lambda: self.pauseMining(5 * 60))
        self.menu_pause.addAction("Pause for 20 minutes", lambda: self.pauseMining(20 * 60))
        self.menu_pause.addAction("Pause for 1 hour", lambda: self.pauseMining(1 * 60 * 60))
        self.menu_pause.addAction("Pause for 8 hours", lambda: self.pauseMining(8 * 60 * 60))

        self.action_resume = self.system_icon_menu.addAction("Resume mining")
        self.action_resume.triggered.connect(self.resumeMining)
        self.action_resume.setVisible(False)

        self.system_icon_menu.addSeparator()
        self.system_icon_menu.addAction("Exit", self.exit)

        self.system_icon.setContextMenu(self.system_icon_menu)

    def run(self):
        self.log("Starting")
        self.system_icon.show()
        self.heartbeat.start()
        self.updateMiners()

    def openDashboard(self):
        self.log("Opening Dashboard")
        self._wdashboard = Dashboard(self)

        self._wdashboard.show()
        self._wdashboard.raise_()
        self._wdashboard.activateWindow()
    
    def openPoolDashboard(self):
        self.log("Opening Pool Dashboard")
        QDesktopServices.openUrl(QUrl("https://supportxmr.com/"))

    def startWeakMiner(self):
        self.log("Starting weak miner")
        self.strong_miner.stop()
        self.weak_miner.start()
    
    def startStrongMiner(self):
        self.log("Starting strong miner")
        self.weak_miner.stop()
        self.strong_miner.start()

    def updateMiners(self):
        idle_time = idleTime()
        target_idle_time = self.config["idle-timeout"] * 60

        if idle_time < target_idle_time:
            if not self.weak_miner.alive:
                self.system_icon_status.setText("Mining: Weak Mode")
                self.startWeakMiner()
        else:
            if not self.strong_miner.alive:
                self.system_icon_status.setText("Mining: Strong Mode")
                self.startStrongMiner()

    def pauseMining(self, duration):
        self.log("Mining paused for {duration}s")
        self.heartbeat.stop()
        self.weak_miner.stop()
        self.strong_miner.stop()
        self.system_icon_status.setText("Mining paused")
        self.menu_pause.menuAction().setVisible(False)
        self.action_resume.setVisible(True)
        self.system_icon.setIcon(self.icon_idle)

        QTimer.singleShot(duration * 1000, self.resumeMining)
    
    def resumeMining(self):
        self.log("Mining resumed")
        self.heartbeat.start()
        self.updateMiners()
        self.menu_pause.menuAction().setVisible(True)
        self.action_resume.setVisible(False)
        self.system_icon.setIcon(self.icon_active)
    
    def exit(self):
        self.log("Exiting")
        self.heartbeat.stop()
        self.weak_miner.stop()
        self.strong_miner.stop()

        self.fp_log.close()
        QApplication.instance().quit()
    
    def logRaw(self, line):
        self.fp_log.write(line + "\n")
        self.deque_log.append(line)

    def log(self, line):
        time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        self.logRaw(f"[Lepricon ({time})] {line}")

    def excepthook(self, etype, value, tb):        
        self.log("Exception occured!")
        for line in traceback.format_exception(None, value, value.__traceback__):
            self.logRaw(line)
        self.exit()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("lepricon")
    app.setApplicationDisplayName("Lepricon Miner")
    app.setWindowIcon(QIcon(str(package.dir / "data" / "icon.png")))
    app.setQuitOnLastWindowClosed(False)

    lp = Lepricon()
    lp.run()
    return app.exec_()

if __name__ == "__main__":
    sys.exit(main())
