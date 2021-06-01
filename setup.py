"""Install script for nfb_studio."""
from setuptools import setup, find_packages

install_requires = [
    "pywin32",
    "pyyaml",
    "PySide2",
    "pyinstaller"
]

entry_points = {
    "gui_scripts": ["lepricon = lepricon.__init__:main"],
    "console_scripts": ["lepricon-d = lepricon.__init__:main"],
}

setup(
    name="lepricon",
    version="0.1",
    description="Unobrusive Monero miner",
    author="Andrey Zhukov",
    author_email="andres.zhukov@gmail.com",
    license="MIT",
    install_requires=install_requires,
    packages=find_packages(),
    package_data={
        "lepricon": ["data/*"]
    },
    entry_points=entry_points
)
