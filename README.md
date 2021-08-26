# Leprechaun
Leprechaun is a Windows system tray program that mines Ethereum, Monero, and other cryptocurrencies in the background while you work.
A configuration file allows you to fine-tune which miners work, at what time of day, while you are afk, etc.

## Install
To install leprechaun, execute the following command in powershell:
```
iwr https://github.com/andreasxp/leprechaun/releases/download/0.2.0/install-leprechaun.ps1 -outfile install-leprechaun.ps1; .\install-leprechaun.ps1
```
This will download and execute a script which will install leprechaun to your appdata folder.

On first launch, Leprechaun will prompt you to configure your miners as you wish.
The configuration will be located in `~/leprechaun.yml`.

## Manual build
Requirements: [python 3.9](https://www.python.org/), [git](https://git-scm.com/)
The following commands clone the repository to your PC and build the executable.
```
git clone https://github.com/andreasxp/leprechaun
cd leprechaun
python -m venv .venv
.venv/Scripts/Activate
pip install -e .
pyinstaller freeze.spec
deactivate
```
The executable will be in the `dist` folder. To launch it at startup, create a scheduled task that launches it at user logon with administrative privileges.
