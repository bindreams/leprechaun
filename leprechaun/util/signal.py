from PySide6.QtCore import QObject, Signal as QtSignal

class Signal:
    """A wrapper around PySide6 Signal that allows normal instantiation and usage (i.e. no class variable, no
    inheriting from QObject)."""

    def __init__(self, *args):
        class QtSignalStorage(QObject):
            signal = QtSignal(*args)

        self._signal_storage = QtSignalStorage()
        self._signal = self._signal_storage.signal

    def connect(self, slot):
        """Connect a signal to a slot."""
        self._signal.connect(slot)

    def disconnect(self, slot=None):
        """Disconnect one or all slots from a signal."""
        if slot is None:
            self._signal.disconnect()
        else:
            self._signal.disconnect(slot)

    def emit(self, *args):
        """Emit a signal."""
        self._signal.emit(*args)