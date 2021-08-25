import base64
from PySide2.QtCore import QUrl, QCoreApplication
from PySide2.QtWebEngineWidgets import QWebEngineView
from PySide2.QtWidgets import QFrame, QHBoxLayout


class MonacoEditor(QFrame):
    _no_result = object()

    index_html = None
    """Set this to a path to index.html"""

    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.webview = QWebEngineView()
        self.webview.load(QUrl.fromLocalFile(str(self.index_html)))

        # Layout
        ly = QHBoxLayout()
        self.setLayout(ly)
        self.setFrameShape(self.Box)
        self.setFrameShadow(self.Sunken)
        ly.setContentsMargins(0, 0, 0, 0)
        ly.addWidget(self.webview)

        # Spin event loop until initialization has finished ------------------------------------------------------------
        initialized = False
        def onInitialized():
            nonlocal initialized
            initialized = True
        
        self.webview.loadFinished.connect(onInitialized)

        app = QCoreApplication.instance()
        while not initialized:
            app.processEvents()

    def _run(self, query):
        """Communicate with the internal webpage by running JS and waiting for a result."""
        result = self._no_result
        def callback(query_result):
            nonlocal result
            result = query_result
        
        self.webview.page().runJavaScript(query, 0, callback)

        app = QCoreApplication.instance()
        while result is self._no_result:
            app.processEvents()
        return result

    def text(self):
        return self._run("monaco.editor.getModels()[0].getValue()")

    def setText(self, text):
        text = text.encode()
        text = base64.b64encode(text)
        text = text.decode()
        self._run(f"monaco.editor.getModels()[0].setValue(atob('{text}'))")

    def setLanguage(self, language):
        self._run(f"monaco.editor.setModelLanguage(monaco.editor.getModels()[0],'{language}')")
    