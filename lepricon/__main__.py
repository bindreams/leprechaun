import sys
from pathlib import Path
import win32api
import yaml
from PySide2.QtCore import QTimer, QUrl
from PySide2.QtGui import QIcon, QDesktopServices
from PySide2.QtWidgets import QApplication, QSystemTrayIcon, QMenu

import lepricon as package
from lepricon.miner import Miner


def idleTime():
    return (win32api.GetTickCount() - win32api.GetLastInputInfo()) / 1000.0


class Lepricon:
    def __init__(self):
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

        # System tray icon ---------------------------------------------------------------------------------------------
        self.icon_active = QIcon(str(package.dir / "data/icon.png"))
        self.icon_idle = QIcon(str(package.dir / "data/icon-idle.png"))

        self.system_icon = QSystemTrayIcon(self.icon_active)
        self.system_icon_menu = QMenu()
        self.system_icon_status = self.system_icon_menu.addAction("Initializing")
        self.system_icon_status.setEnabled(False)
        self.system_icon_menu.addAction(
            "Open Dashboard", lambda: QDesktopServices.openUrl(QUrl("https://supportxmr.com/"))
        )
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
        self.system_icon.show()
        self.heartbeat.start()
        self.updateMiners()

    def startWeakMiner(self):
        self.strong_miner.stop()
        self.weak_miner.start()
    
    def startStrongMiner(self):
        self.weak_miner.stop()
        self.strong_miner.start()

    def updateMiners(self):
        idle_time = idleTime()
        target_idle_time = self.config["idle-timeout"] * 60

        if idle_time < target_idle_time:
            self.system_icon_status.setText("Mining: Weak Mode")
            self.startWeakMiner()
        else:
            self.system_icon_status.setText("Mining: Strong Mode")
            self.startStrongMiner()

    def pauseMining(self, duration):
        self.heartbeat.stop()
        self.weak_miner.stop()
        self.strong_miner.stop()
        self.system_icon_status.setText("Mining paused")
        self.menu_pause.menuAction().setVisible(False)
        self.action_resume.setVisible(True)
        self.system_icon.setIcon(self.icon_idle)

        QTimer.singleShot(duration * 1000, self.resumeMining)
    
    def resumeMining(self):
        self.heartbeat.start()
        self.updateMiners()
        self.menu_pause.menuAction().setVisible(True)
        self.action_resume.setVisible(False)
        self.system_icon.setIcon(self.icon_active)
    
    def exit(self):
        self.heartbeat.stop()
        self.weak_miner.stop()
        self.strong_miner.stop()
        QApplication.instance().quit()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Lepricon")
    lp = Lepricon()

    lp.run()
    return app.exec_()

if __name__ == "__main__":
    sys.exit(main())
