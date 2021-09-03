import subprocess as sp
import sys
from argparse import ArgumentParser
from datetime import datetime
from pathlib import Path

import yaml
from PySide2.QtCore import QCoreApplication, QObject, QTimer, Signal

import leprechaun as le
from leprechaun.base import InvalidConfigError, elevated, format_exception
from leprechaun.miners import MinerStack


# CLI argument parser ==================================================================================================
def _get_parser():
    parser = ArgumentParser("leprechaun", description="A tiny crypto miner program that lives in your system tray.")

    # parse functions --------------------------------------------------------------------------------------------------
    def config_file(arg):
        path = Path(arg).expanduser()
        if path != Path("~/leprechaun.yml").expanduser() and not path.is_file():
            parser.error(f"config file {path} does not exist")
        else:
            return path

    # parser -----------------------------------------------------------------------------------------------------------
    parser.set_defaults(subcommand=None)
    subparsers = parser.add_subparsers(title="subcommands")

    # run --------------------------------------------------------------------------------------------------------------
    parser_run = subparsers.add_parser("run", description="Configure leprechaun.")
    parser_run.set_defaults(subcommand="run")
    parser_run.add_argument("file",
        type=config_file,
        help="config file with miner settings"
    )

    # config -----------------------------------------------------------------------------------------------------------
    parser_config = subparsers.add_parser("config", description="Configure leprechaun.")
    parser_config.set_defaults(subcommand="config")

    parser_config.add_argument("--add-shortcuts",
        action="store_true",
        help="add shortcuts to the start menu and desktop"
    )

    parser_config.add_argument("--add-scheduled-task",
        action="store_true",
        help="add scheduled task that launches Leprechaun at startup"
    )

    parser_config.add_argument("--add-security-exception",
        action="store_true",
        help="add windows security exception for the leprechaun folder"
    )

    return parser

parser = _get_parser()


# Config functions =====================================================================================================
def add_shortcuts():
    script = """
        $WshShell = New-Object -ComObject WScript.Shell
        function Set-Shortcut() {{
            param($Where)

            $Shortcut = $WshShell.CreateShortcut($Where)
            $Shortcut.TargetPath = "{path}"
            {set_args}
            $Shortcut.Save()
        }}

        Set-Shortcut("$env:USERPROFILE/Start Menu/Programs/Leprechaun Miner.lnk")
        Set-Shortcut("$env:USERPROFILE/Desktop/Leprechaun Miner.lnk")
    """

    if sys.argv[0].endswith("__main__.py"):
        path = sys.executable
        set_args = "$Shortcut.Arguments = '-m leprechaun'"
    else:
        path = Path(sys.argv[0]).parent / "leprechaun.exe"
        set_args = ""

    sp.run(["powershell.exe", "-Command", script.format(path=path, set_args=set_args)], check=True)


def add_scheduled_task():
    script = """
        $TaskName = "Leprechaun Miner Start Task"
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue

        $Description = "Start Leprechaun miner at user logon."
        $Action = New-ScheduledTaskAction {exe} {args}
        $Trigger = New-ScheduledTaskTrigger -AtLogOn
        Register-ScheduledTask -TaskName $TaskName -Description $Description -Action $Action -Trigger $Trigger -RunLevel Highest > $null
    """

    if sys.argv[0].endswith("__main__.py"):
        exe = f"-Execute '{sys.executable}'"
        args = "-Argument '-m leprechaun'"
    else:
        path = Path(sys.argv[0]).parent / "leprechaun.exe"
        exe = f"-Execute '{path}'"
        args = ""

    sp.run(["powershell.exe", "-Command", script.format(exe=exe, args=args)], check=True)


def add_security_exception():
    script = f"Add-MpPreference -ExclusionPath {le.data_dir}"
    sp.run(["powershell.exe", "-Command", script], check=True)


# CliApplication =======================================================================================================
class CliApplication(QObject):
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
        self.cpuminers = MinerStack(self)
        self.gpuminers = MinerStack(self)
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


# ======================================================================================================================
def main():
    """Run Leprechaun."""
    args = parser.parse_args()

    if args.subcommand == "config":
        # Configure ----------------------------------------------------------------------------------------------------
        if args.add_scheduled_task:
            if not elevated:
                parser.error("supplied arguments require administrator priveleges")
            add_scheduled_task()

        if args.add_security_exception:
            if not elevated:
                parser.error("supplied arguments require administrator priveleges")
            add_security_exception()

        if args.add_shortcuts:
            add_shortcuts()

    else:
        # Launch application -------------------------------------------------------------------------------------------
        if args.subcommand == "run":
            config_path=args.file
        else:
            config_path=None

        qapp = QCoreApplication([])

        app = CliApplication(config_path)
        app.start()

        return qapp.exec_()

if __name__ == "__main__":
    sys.exit(main())
