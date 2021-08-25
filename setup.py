"""Install script for leprechaun."""
from setuptools import setup, find_packages

install_requires = [
    "cachetools",
    "pywin32",
    "pyyaml",
    "PySide2",
    "pyinstaller",
    "calc @ https://github.com/andreasxp/calc/archive/refs/heads/main.zip"
]

entry_points = {
    "gui_scripts": ["leprechaun = leprechaun.__init__:main"],
    "console_scripts": ["leprechaun-d = leprechaun.__init__:main"],
}

setup(
    name="leprechaun",
    version="0.2.0",
    description="Friendly crypto miner",
    author="Andrey Zhukov",
    author_email="andres.zhukov@gmail.com",
    license="MIT",
    install_requires=install_requires,
    packages=find_packages(),
    package_data={
        "leprechaun": ["data/*"]
    },
    entry_points=entry_points
)
