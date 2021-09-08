from pathlib import Path
import subprocess as sp
from time import sleep
from leprechaun.util import download_and_extract

version = "1.59.1"
url = f"https://github.com/VSCodium/vscodium/releases/download/{version}/VSCodium-win32-x64-{version}.zip"

settings = """
{
    "security.workspace.trust.enabled": false,
    "editor.minimap.enabled": false,
    "window.title": "${dirty}${activeEditorShort}${separator}${rootName}",
    "window.restoreWindows": "none",
    "telemetry.enableTelemetry": false,
    "telemetry.enableCrashReporter": false,
    "update.mode": "none",

    "workbench.colorTheme": "Default Light+",
    "workbench.editor.showTabs": false,
    "workbench.activityBar.visible": false,
    "workbench.statusBar.visible": false,
    "workbench.editor.showIcons": false,

    "workbench.colorCustomizations": {
        "window.activeBorder": "#707070",
        "window.inactiveBorder": "#aaaaaa",
        "titleBar.activeBackground": "#ffffff",
        "titleBar.inactiveBackground": "#ffffff",
        "titleBar.border": "#dcdcdc",
        "editorGroupHeader.noTabsBackground": "#f0f0f0",
        "editorGroupHeader.border": "#dcdcdc",
        "editor.lineHighlightBackground": "#f0f0ff"
    },
}
"""

def download(path, callback=None):
    path = Path(path)
    download_and_extract(url, path / "vscodium", callback)

    settingspath = path / "user-data" / "User" / "settings.json"
    settingspath.parent.mkdir(parents=True, exist_ok=True)

    with open(settingspath, "w", encoding="utf-8") as f:
        f.write(settings)

def launch(path, file=None):
    if file is None:
        file = ""
    else:
        file = str(file)

    return sp.Popen([
            path / "vscodium" / "vscodium.exe", file,
            "--user-data-dir", path / "user-data",
            "--extensions-dir", path / "user-extenstions",
            "--wait"
        ],
        stdin=sp.DEVNULL,
        stdout=sp.DEVNULL,
        stderr=sp.DEVNULL,
        creationflags=sp.CREATE_NO_WINDOW
    )
