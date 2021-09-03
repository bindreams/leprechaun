import sys
from argparse import ArgumentParser
from pathlib import Path
import subprocess as sp
from PySide2.QtCore import QCoreApplication
import leprechaun as le
from leprechaun.base import elevated

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

        app = le.CliApplication(config_path)
        app.start()

        return qapp.exec_()

if __name__ == "__main__":
    sys.exit(main())
