# Lepricon
Lepricon is a Windows system tray program that mines XMR (Monero) at unintrusive rates.

## Setup
Requirements: python 3.9, git
The following commands clone the repository to your PC and build the executable.
```
git clone https://github.com/andreasxp/lepricon
cd lepricon
python -m venv .venv
.venv/Scripts/Activate
pip install -e .
pyinstaller freeze.spec
deactivate
```
The executable will be in the `dist` folder. To launch it at startup, create a shortcut to it in `%appdata%\Microsoft\Windows\Start Menu\Programs\Startup`.
