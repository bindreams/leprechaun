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
iex (iwr https://github.com/andreasxp/leprechaun/releases/download/0.4.0/install-leprechaun.ps1)
```
This will download and execute a script which will install leprechaun to your appdata folder. On first launch, Leprechaun will prompt you to configure your miners as you wish.
The configuration file will be located in `~/leprechaun.yml`.

<details><summary>Building Leprechaun from source</summary><p>
  
  Requirements: [python 3.9+](https://www.python.org/), [git](https://git-scm.com/)
  
  Leprechaun is a python package that can be run by itself, but is distributed by being "frozen" into an executable using [pyinstaller](https://www.pyinstaller.org/).
  Regardless of the way you want to run Leprechaun, you will need to clone this repository and run `pip install --editable` to obtain all the necessary packages automatically:
  ```
  $ git clone https://github.com/andreasxp/leprechaun
  $ cd leprechaun
  $ pip install --editable .
  ```
  
  After `pip install`, you can launch the package from command line as follows:
  ```
  $ python -m leprechaun      # Launch Leprechaun GUI
  $ leprechaun                # Launch Leprechaun GUI (alternative)
  
  $ python -m leprechaun.cli  # Launch Leprechaun CLI
  $ leprechaun-cli            # Launch Leprechaun CLI (alternative)
  ```
  Leprechaun CLI supports interaction using command line. Use `leprechaun-cli --help` to find out more.
  
  To freeze the python package into an executable, use the included script:
  ```
  $ python build.py
  ```
  The executables will be in the `dist` folder. To add shortcuts, launch at startup, or otherwise configure the application, use `leprechaun-cli.exe config <options>`.
  
</p></details>

## Configuration
This section is a work in progress. Thank you for your patience!
