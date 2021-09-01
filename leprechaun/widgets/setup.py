from PySide2.QtCore import Qt
from PySide2.QtWidgets import QDialog, QWidget, QLabel, QProgressBar, QApplication, QVBoxLayout, QFrame, QDialogButtonBox, QPushButton, QSizePolicy, QHBoxLayout, QButtonGroup
from .base import rem, font
import leprechaun as le
from leprechaun.base import download, extract, InvalidConfigError
from concurrent.futures import ThreadPoolExecutor
from yaml.parser import ParserError as YamlParserError

class Setup(QDialog):
    welcome_message = (
        "Welcome to Leprechaun!\n\n"
        "To start mining, you need to write a simple configuration file. This file will be stored in your home "
        "directory as leprechaun.yml. Leprechaun prepared an example for you. Please customize it for yourself, then "
        "start the miner with the 'Continue' button below.\n\n"
    )

    def __init__(self, message, parent=None):
        super().__init__(parent)
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)

        self.wlabel = QLabel(message)
        self.wlabel.setWordWrap(True)

        self.werrorlabel = QLabel()
        self.werrorlabel.setFont(font("Consolas"))
        self.werrorlabel.setWordWrap(True)
        self.werrorlabel.setStyleSheet("QLabel {color: red;}")

        self.wdocumentationlabel = QLabel("<a href=\"https://github.com/andreasxp/leprechaun#configuration\">Config file documentation</a>")
        self.wlabel.setTextFormat(Qt.RichText)
        self.wlabel.setTextInteractionFlags(Qt.TextBrowserInteraction)
        self.wlabel.setOpenExternalLinks(True)

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
        app = le.Application()

        try:
            app.loadconfig()
        except (YamlParserError, InvalidConfigError, FileNotFoundError) as e:
            self.werrorlabel.setText(str(e))
        else:
            self.accept()

    def actionEditConfig(self):
        app = le.Application()

        app.actionEditConfig()
        self.wbutton_continue.setEnabled(True)
        self.wbutton_continue.setDefault(True)
        self.wbutton_continue.setFocus()
