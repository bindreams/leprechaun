# Leprechaun
Leprechaun is a Windows system tray program that mines XMR (Monero) at unintrusive rates. It has two miners: a weak one for when you are using your pc, and a strong one for when you are AFK. These can be controlled when leprechaun is running from the system tray.

## Setup
Requirements: python 3.9, git
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
The executable will be in the `dist` folder. To launch it at startup, create a shortcut to it in `%appdata%\Microsoft\Windows\Start Menu\Programs\Startup`.

## Configuration
To configure your wallet and other parameters, copy `leprechaun.yml` to your home directory (`C:/Users/<user>`). Open it (it's a text file), and input your wallet address.
Leprechaun only reads configuration files from your home directory.
