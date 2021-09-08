import atexit
import shutil
import sys

from PySide2.QtCore import QTimer
from PySide2.QtGui import QFontDatabase, QIcon
from PySide2.QtWidgets import QApplication, QDialog, QMenu, QSystemTrayIcon
from yaml.parser import ParserError as YamlParserError
from yaml.scanner import ScannerError as YamlScannerError

import leprechaun as le
from leprechaun import notepad
from leprechaun.util import InvalidConfigError
from leprechaun.cli import CliApplication
from leprechaun.widgets import Dashboard, ExceptionMessageBox, Setup


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

    def log(self, *args):
        for line in self.format_log(*args):
            self._fp_log.write(line)

    def excepthook(self, etype, value, tb):
        if not isinstance(value, KeyboardInterrupt):
            wmessage = ExceptionMessageBox(value)
            wmessage.exec_()

        super().excepthook(etype, value, tb)


def main():
    qapp = QApplication([])

    app = Application()
    app.start()

    return qapp.exec_()


if __name__ == "__main__":
    sys.exit(main())
