from PySide2.QtCore import Qt
from PySide2.QtWidgets import QDialog, QWidget, QLabel, QProgressBar, QApplication, QVBoxLayout, QFrame, QDialogButtonBox, QPushButton, QSizePolicy, QHBoxLayout, QButtonGroup
from .base import rem, rempt, font
import leprechaun as le
from leprechaun.util import download, extract, InvalidConfigError
from concurrent.futures import ThreadPoolExecutor
from yaml.parser import ParserError as YamlParserError
from yaml.scanner import ScannerError as YamlScannerError


class Setup(QDialog):
    welcome_message = (
        "Welcome to Leprechaun!\n\n"
        "To start mining, you need to write a simple configuration file. This file will be stored in your home "
        "directory as leprechaun.yml. Leprechaun prepared an example for you. Please customize it for yourself, then "
        "start the miner with the 'Continue' button below.\n\n"
    )

    def __init__(self, app, message):
        super().__init__()
        self.app = app

        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)

        self.wlabel = QLabel(message)
        self.wlabel.setWordWrap(True)

        self.werrorlabel = QLabel()
        self.werrorlabel.setFont(font("Consolas", size=rempt() * 1.2))
        self.werrorlabel.setWordWrap(True)
        self.werrorlabel.setStyleSheet("color: #cc0000")

        self.wdocumentationlabel = QLabel("<a href=\"https://github.com/andreasxp/leprechaun#configuration\">Config file documentation</a>")
        self.wdocumentationlabel.setTextFormat(Qt.RichText)
        self.wdocumentationlabel.setTextInteractionFlags(Qt.TextBrowserInteraction)
        self.wdocumentationlabel.setOpenExternalLinks(True)

        wline = QFrame()
        wline.setFrameShape(QFrame.HLine)
        wline.setFrameShadow(QFrame.Sunken)

        # Buttons ------------------------------------------------------------------------------------------------------
        self.wbutton_edit = QPushButton("Edit Config")
        self.wbutton_edit.setDefault(True)
        self.wbutton_edit.clicked.connect(self.actionEditConfig)
        self.wbutton_continue = QPushButton("Continue")
        self.wbutton_continue.setEnabled(False)
        self.wbutton_continue.clicked.connect(self.actionContinue)
        self.wbutton_exit = QPushButton("Exit")
        self.wbutton_exit.clicked.connect(self.reject)

        wline2 = QFrame()
        wline2.setFrameShape(QFrame.VLine)
        wline2.setFrameShadow(QFrame.Sunken)

        # Layout -------------------------------------------------------------------------------------------------------
        self.setFixedSize(rem()*30, rem()*20)

        lybuttons = QHBoxLayout()
        lybuttons.addStretch()
        lybuttons.addWidget(self.wbutton_edit)
        lybuttons.addWidget(wline2)
        lybuttons.addWidget(self.wbutton_continue)
        lybuttons.addWidget(self.wbutton_exit)

        ly = QVBoxLayout()
        self.setLayout(ly)

        ly.addWidget(self.wlabel)
        ly.addWidget(self.werrorlabel)
        ly.addWidget(self.wdocumentationlabel)
        ly.addStretch()
        ly.addWidget(wline)
        ly.addLayout(lybuttons)

    def actionContinue(self):
        try:
            self.app.loadconfig()
        except (YamlScannerError, YamlParserError, InvalidConfigError, FileNotFoundError) as e:
            self.werrorlabel.setText(str(e))
        else:
            self.accept()

    def actionEditConfig(self):
        self.app.actionEditConfig()
        self.wbutton_continue.setEnabled(True)
        self.wbutton_continue.setDefault(True)
        self.wbutton_continue.setFocus()
