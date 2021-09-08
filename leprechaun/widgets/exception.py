from PySide2.QtWidgets import QMessageBox, QTextEdit
from leprechaun.util import format_exception
from .base import rem


class ExceptionMessageBox(QMessageBox):
    def __init__(self, exception):
        super().__init__()
        self.exception = exception

        self.setWindowTitle("Critical Error")
        self.setText(
            "An unknown critical error occured in Leprechaun.\n\n"
            "Please inform the developer, attaching your config file, as well as the text below."
        )
        self.setIcon(self.Icon.Critical)

        exception_field = QTextEdit()
        exception_field.setText(
            "".join(format_exception(None, exception, exception.__traceback__))
        )

        exception_field.setReadOnly(True)
        self.layout().addWidget(exception_field, 1, 0, 1, -1)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.setFixedHeight(35*rem())
