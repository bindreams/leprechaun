import sys
from argparse import ArgumentParser
from pathlib import Path

from PySide2.QtCore import QCoreApplication
from PySide2.QtWidgets import QApplication

import leprechaun as le
from leprechaun import config
from leprechaun.application import Application, CliApplication
from leprechaun.util import isroot


# Parser ===============================================================================================================
parser = ArgumentParser("leprechaun", description="A tiny crypto miner program that lives in your system tray.")

def config_file(arg):
    path = Path(arg).expanduser()
    if path != Path("~/leprechaun.yml").expanduser() and not path.is_file():
        parser.error(f"config file {path} does not exist")
    else:
        return path

parser.set_defaults(subcommand=None)
subparsers = parser.add_subparsers(title="subcommands")

parser.add_argument("-V", "--version", action="version", version=le.__version__)
parser.add_argument("file",
    nargs="?",
    default=Path("~/leprechaun.yml").expanduser(),
    type=config_file,
    help="config file with miner settings"
)
parser.add_argument("-g", "--gui", action="store_true", help="launch with graphical interface")
parser.add_argument("-p", "--pipe-log", action="store_true", help="write log to file instead of stdout")

# config ---------------------------------------------------------------------------------------------------------------
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


# ======================================================================================================================
def main():
    """Run Leprechaun."""
    args = parser.parse_args()

    if args.subcommand is None:
        # Run Leprechaun -----------------------------------------------------------------------------------------------
        if args.gui:
            qapp = QApplication([])
            app = Application(args.file, args.pipe_log)
        else:
            qapp = QCoreApplication([])
            app = CliApplication(args.file, args.pipe_log)

        app.start()
        return qapp.exec_()
    elif args.subcommand == "config":
        # Configure ----------------------------------------------------------------------------------------------------
        if args.add_scheduled_task:
            if not isroot:
                parser.error("supplied arguments require administrator priveleges")
            config.add_scheduled_task()

        if args.add_security_exception:
            if not isroot:
                parser.error("supplied arguments require administrator priveleges")
            config.add_security_exception()

        if args.add_shortcuts:
            config.add_shortcuts()


if __name__ == "__main__":
    sys.exit(main())
