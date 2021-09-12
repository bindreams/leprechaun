import subprocess as sp
import sys
from pathlib import Path

import leprechaun as le


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
        $Action = New-ScheduledTaskAction {exe_arg} {args}
        $Trigger = New-ScheduledTaskTrigger -AtLogOn
        Register-ScheduledTask -TaskName $TaskName -Description $Description -Action $Action -Trigger $Trigger -RunLevel Highest > $null
    """

    if sys.argv[0].endswith("__main__.py"):
        exe = Path(sys.executable).with_stem("pythonw")

        exe_arg = f"-Execute '{exe}'"
        args = "-Argument '-m leprechaun -gp'"
    else:
        path = Path(sys.argv[0]).parent / "leprechaun-gui.exe"
        exe_arg = f"-Execute '{path}'"
        args = ""

    sp.run(["powershell.exe", "-Command", script.format(exe_arg=exe_arg, args=args)], check=True)


def add_security_exception():
    script = f"Add-MpPreference -ExclusionPath {le.data_dir}"
    sp.run(["powershell.exe", "-Command", script], check=True)
