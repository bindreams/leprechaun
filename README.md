# Leprechaun 🍀
Leprechaun is a tiny program that lives in your system tray. It mines Ethereum, Monero, and other cryptocurrencies in the background while you work.  
A configuration file allows you to fine-tune which miners work, at what time of day, while you are afk, etc.

Leprechaun requires Windows 10, 64-bit.

## Installation
To install Leprechaun, execute the following command in powershell:

<table><tr><td>
⚠️ <b>NOTE:</b> Always verify the security and contents of any script from the internet you are not familiar with.
</td></tr></table>

```
iex (iwr https://github.com/andreasxp/leprechaun/releases/download/0.3.2/install-leprechaun.ps1)
```
This will download and execute a script which will install leprechaun to your appdata folder. On first launch, Leprechaun will prompt you to configure your miners as you wish.
The configuration file will be located in `~/leprechaun.yml`.

<details><summary>Building Leprechaun from source</summary><p>
  
Requirements: [python 3.9+](https://www.python.org/), [git](https://git-scm.com/)  
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
  
</p></details>

## Configuration
This section is a work in progress. Thank you for your patience!
