from PySide2.QtCore import Qt
from PySide2.QtWidgets import QVBoxLayout, QWidget, QTextEdit

class Dashboard(QWidget):
    def __init__(self, lepricon):
        super().__init__()
        self.setAttribute(Qt.WA_DeleteOnClose)

        self.lepricon = lepricon

        self.wlog = QTextEdit()
        self.wlog.setFontFamily("Consolas")
        self.wlog.setFontPointSize(10)
        self.wlog.setReadOnly(True)
        self.wlog.setLineWrapMode(self.wlog.NoWrap)

        self.wlog.setText("\n".join(lepricon.deque_log))
        lepricon.weak_miner.logUpdated.connect(self.appendLogLine)
        lepricon.strong_miner.logUpdated.connect(self.appendLogLine)

        # Layout -------------------------------------------------------------------------------------------------------
        ly = QVBoxLayout()
        self.setLayout(ly)

        ly.addWidget(self.wlog)
        self.resize(800, 600)
    
    def appendLogLine(self, line):
        scrollbar = self.wlog.verticalScrollBar()

        atBottom = scrollbar.value() == scrollbar.maximum()

        self.wlog.append(line)

        if atBottom:
            scrollbar.setValue(scrollbar.maximum())

