"""This script assumes that you are running it from the root directory of the repo."""
import subprocess as sp
import shutil

# Clean dist directory
shutil.rmtree("dist")

sp.run(["pyinstaller", "scripts/freeze.spec", "--distpath", "dist/temp"], check=True)
sp.run(["pyinstaller", "scripts/freeze-gui.spec", "--distpath", "dist/temp"], check=True)

archive = shutil.make_archive("dist/leprechaun", "zip", root_dir="dist/temp")

# Copy install script
shutil.copy("install-leprechaun.ps1", "dist")

# Cleat dist temp directory
shutil.rmtree("dist/temp")
