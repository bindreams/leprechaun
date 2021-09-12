Installation
========================================================================================================================
This page describes all the ways to install and build Leprechaun. For a simple setup guide, visit :doc:`quickstart`.

Install Script
------------------------------------------------------------------------------------------------------------------------
The most simple and basic way to run Leprechaun is via an PowerShell script. This script is provided with every release
of Leprechaun on the `releases <https://github.com/andreasxp/leprechaun/releases>`_ Github page.
This script can be downloaded and run manually, or via a single command in PowerShell:

.. important::
	Always verify the security and contents of any script from the internet you are not familiar with!
	We know that this code does nothing malicious, but do you trust us? Open
	`install-leprechaun.ps1 <https://github.com/andreasxp/leprechaun/releases/download/0.5.0/install-leprechaun.ps1>`_
	and inspect it for yourself.

.. code:: PowerShell

	iex (iwr https://github.com/andreasxp/leprechaun/releases/download/0.5.0/install-leprechaun.ps1)

This script will download Leprechaun executables into your ``%AppData%\leprechaun`` directory, and optionally do one or more
things:

#. Create a scheduled task that launches Leprechaun on system startup. The reason why a scheduled task is used instead
   of the ``Startup`` folder is because Leprechaun needs admin privileges to run at full speed;
#. Add a Desktop shortcut;
#. Add Windows Security exception. This is the only known way to prevent antiviruses from flagging Leprechaun as malware
   for using mining software.

Manual Download
------------------------------------------------------------------------------------------------------------------------
Leprechaun can also be downloaded manually. A zip file with executables is available with every
`release <https://github.com/andreasxp/leprechaun/releases>`_. These executables don't need to be in any particular
location, but will still create their files in ``%AppData%\leprechaun``.

Installing via Pip
------------------------------------------------------------------------------------------------------------------------
The latest (or any) commit can be checked out by downloading the full Leprechaun repository and installing it as a
python package.

Requirements:
  - `Python 3.9+ <https://www.python.org/>`_
  - `Pip <https://pip.pypa.io/en/stable/>`_
  - `Git <https://git-scm.com/>`_

First, clone the repository and run ``pip install --editable`` to obtain all the necessary packages automatically:

.. code:: bash

	git clone https://github.com/andreasxp/leprechaun
	cd leprechaun
	pip install --editable .

After ``pip install``, you can launch the package from command line as follows:

.. code:: bash

  leprechaun-gui        # Launch Leprechaun GUI

  python -m leprechaun  # Launch Leprechaun CLI
  leprechaun            # Launch Leprechaun CLI (alternative)

Leprechaun CLI supports interaction using CLI as well as the GUI. Use ``leprechaun --help`` to find out more.

Freezing
------------------------------------------------------------------------------------------------------------------------
Leprechaun is a python package that can be run by itself, but is distributed by being "frozen" into an executable using
`pyinstaller <https://www.pyinstaller.org/>`_. If you would like to freeze Leprechaun yourself, first clone the
repository as described in `Installing via Pip`_. Then, run the install command with an additional requirement of
``freeze``:

.. code:: bash

  pip install --editable .[freeze]

Finally, to freeze the python package into an executable, use the included script:

.. code:: bash

  python build.py

The executables will be in the ``dist`` folder. To add shortcuts, launch at startup, or otherwise configure the
application, use ``./leprechaun config <options>``.
