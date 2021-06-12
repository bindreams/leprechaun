import subprocess as sp
from threading import Thread
from collections import deque
from PySide2.QtCore import QObject, Signal
import lepricon as package


class Miner(QObject):
    logUpdated = Signal(str)
    processFinished = Signal(int)

    def __init__(self, address, rig_id, priority, thread_count):
        super().__init__()

        self.address = address
        self.rig_id = rig_id
        self.priority = priority
        self.thread_count = thread_count

        self.process = None

    @property
    def alive(self):
        return self.process is not None and self.process.returncode is None
    
    @property
    def returncode(self):
        if self.process is None:
            return None
        return self.process.returncode

    def start(self):
        if self.alive:
            return

        self.process = sp.Popen([
                package.dir / "data/xmrig-6.8.2/xmrig.exe",
                "-o", "pool.supportxmr.com:443",
                "-u", self.address,
                "--rig-id", self.rig_id,
                "--cpu-priority", str(self.priority),
                "-t", str(self.thread_count),
                "-k", "--tls", "--no-color"
            ],
            stdin=sp.DEVNULL,
            stdout=sp.PIPE,
            stderr=sp.STDOUT,
            text=True,
            creationflags=sp.CREATE_NO_WINDOW
        )
        Thread(target=self.poll).start()

    def stop(self):
        if self.alive:
            self.process.terminate()

    def poll(self):
        for line in iter(self.process.stdout.readline, ""):
            line = line.strip()
            if line != "":
                self.logUpdated.emit(line)

        self.process.wait()
        self.processFinished.emit(self.process.returncode)
