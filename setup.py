"""Install script for leprechaun."""
from setuptools import setup, find_packages

install_requires = [
    "appdirs",
    "cachetools",
    "pywin32; platform_system=='Windows'",
    "pyyaml",
    "PySide2",
    "better_exceptions",
    "calc @ https://github.com/andreasxp/calc/archive/refs/heads/main.zip",
    "idle @ https://github.com/andreasxp/idle/archive/refs/heads/main.zip"
]

extras_require = {
    "freeze":  [
        "pyinstaller",
    ],
    "docs": [
        "sphinx",
        "furo",
        "sphinx-copybutton"
    ]
}

entry_points = {
    "gui_scripts": ["leprechaun-gui = leprechaun.__main__:mainw"],
    "console_scripts": ["leprechaun = leprechaun.__main__:main"],
}

setup(
    name="leprechaun",
    version="0.4.0",
    description="Friendly crypto miner",
    author="Andrey Zhukov",
    author_email="andres.zhukov@gmail.com",
    license="MIT",
    install_requires=install_requires,
    extras_require=extras_require,
    packages=find_packages(include=[
        "leprechaun",
        "leprechaun.*"
    ]),
    package_data={
        "leprechaun": ["data/*"]
    },
    entry_points=entry_points
)
