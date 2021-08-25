from PySide2.QtGui import QTextOption, Qt
from PySide2.QtWidgets import QDialog, QGridLayout, QHBoxLayout, QLabel, QPushButton, QStyle, QTextEdit
from .monaco import MonacoEditor
from .base import font, rem, rempt


class ConfigFixDialog(QDialog):
    def __init__(self, title, description, config_text, icon = QStyle.SP_MessageBoxCritical):
        super().__init__()
        
        style = self.style()
        icon = style.standardIcon(icon)
        wicon = QLabel()
        wicon.setPixmap(icon.pixmap(32))
        wicon.setAlignment(Qt.AlignCenter)
        wicon.setFixedWidth(wicon.sizeHint().width())
        
        wtitle = QLabel(title)
        wtitle.setWordWrap(True)

        wdescription = QTextEdit(description)
        wdescription.setMinimumWidth(30*rem())
        wdescription.setWordWrapMode(QTextOption.NoWrap)
        wdescription.setReadOnly(True)
        wdescription.setFont(font("Consolas", "Regular", rempt()*1.1))

        self.weditor = MonacoEditor()
        self.weditor.setText(config_text)
        self.weditor.setLanguage("yaml")

        self.wexit = QPushButton("Exit")
        self.wexit.setFixedSize(self.wexit.sizeHint())
        self.wexit.clicked.connect(self.reject)
        self.wcontinue = QPushButton("Continue")
        self.wcontinue.setFixedSize(self.wcontinue.sizeHint())
        self.wcontinue.clicked.connect(self.accept)

        lybuttons = QHBoxLayout()
        lybuttons.addWidget(self.wexit)
        lybuttons.addWidget(self.wcontinue)

        ly = QGridLayout()
        ly.setVerticalSpacing(2*rem())
        self.setLayout(ly)

        ly.addWidget(wicon, 0, 0)
        ly.addWidget(wtitle, 0, 1)
        ly.addWidget(wdescription, 1, 0, 1, 2)
        ly.addLayout(lybuttons, 2, 0, 1, 2)
        ly.addWidget(self.weditor, 0, 2, 4, 1)

        ly.setColumnStretch(2, 1)
        ly.setRowStretch(3, 1)

    @classmethod    
    def Setup(cls, config_text):
        return cls(
            "Welcome to Leprechaun Miner first time setup!",
            "Lorem Ipsum is simply dummy text of the printing and typesetting industry. Lorem Ipsum has been the industry's standard dummy text ever since the 1500s, when an unknown printer took a galley of type and scrambled it to make a type specimen book. It has survived not only five centuries, but also the leap into electronic typesetting, remaining essentially unchanged. It was popularised in the 1960s with the release of Letraset sheets containing Lorem Ipsum passages, and more recently with desktop publishing software like Aldus PageMaker including versions of Lorem Ipsum.",
            config_text,
            QStyle.SP_MessageBoxInformation
        )
    
    @classmethod
    def ConfigError(cls, config_text, error):
        return cls(
            "Leprechaun encountered an error when loading the config file.\n\nPlease fix the error, then click 'Continue'. The error was:",
            error,
            config_text,
            QStyle.SP_MessageBoxCritical
        )
