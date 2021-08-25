from itertools import chain
from PySide2.QtCore import Qt, Signal, QSize
from PySide2.QtGui import QIcon, QBrush, QColor
from PySide2.QtWidgets import QApplication, QGridLayout, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget, QTextEdit, QFrame, QListWidget, QSizePolicy
import leprechaun
from .base import defaultfont, font, rem, rempt
from leprechaun.api.messari import usdprice


class Log(QTextEdit):
    _registry = {}

    def __init__(self, name, miner):
        super().__init__()
        self.setWindowTitle(f"Log file for miner '{name}'")
        self.setAttribute(Qt.WA_DeleteOnClose, True)

        self.setFontFamily("Consolas")
        self.setReadOnly(True)
        self.setText("\n".join(miner.log))
        miner.logUpdated.connect(self.append)

        # Add self to a registry to not get accidentally deleted
        self._registry[id(self)] = self
    
    def closeEvent(self, event):
        super().closeEvent(event)
        self._registry.pop(id(self))

class MinerList(QListWidget):
    icon_none = None
    icon_green = None
    icon_red = None
    icon_disable = None

    def __init__(self, miners, priorities):
        super().__init__()
        self.miners = miners
        self.priorities = priorities

        for name in priorities:
            self.addItem(name)
        
        self.setIconSize(QSize(rem()*1.5, rem()*1.5))
        self.itemDoubleClicked.connect(self.onItemDoubleClicked)

        cls = type(self)
        if cls.icon_none is None:
            cls.icon_none = QIcon(str(leprechaun.dir / "data" / "status-none.svg"))
            cls.icon_green = QIcon(str(leprechaun.dir / "data" / "status-green.svg"))
            cls.icon_red = QIcon(str(leprechaun.dir / "data" / "status-red.svg"))
            cls.icon_disable = QIcon(str(leprechaun.dir / "data" / "status-disable.svg"))
    
    def sizeHint(self):
        return self.minimumSizeHint()
    
    def update(self, active):
        before_active = True

        for i in range(self.count()):
            item = self.item(i)
            name = item.text()

            if name == active:
                item.setIcon(self.icon_green)
                before_active = False
            elif before_active:
                item.setIcon(self.icon_red)
            elif not self.miners[name].enabled:
                item.setIcon(self.icon_disable)
            else:
                item.setIcon(self.icon_none)

    def onItemDoubleClicked(self, item):
        name = item.text()
        wlog = Log(name, self.miners[name])
        wlog.show()


class Dashboard(QWidget):
    closed = Signal()

    def __init__(self):
        super().__init__()

        moneyfont = defaultfont()
        moneyfont.setPointSizeF(2.3*rempt())

        self.wtotal = QLabel()
        self.wtotal.setFont(moneyfont)
        self.wtotal.setAlignment(Qt.AlignHCenter)
        self.wtotal.setFrameStyle(QFrame.Panel | QFrame.Sunken)

        # self.wtotal24h = QLabel()
        # self.wtotal24h.setFont(moneyfont)
        # self.wtotal24h.setAlignment(Qt.AlignHCenter)
        # self.wtotal24h.setFrameStyle(QFrame.Panel | QFrame.Sunken)

        self.wpending = QLabel()
        self.wpending.setFont(moneyfont)
        self.wpending.setAlignment(Qt.AlignHCenter)
        self.wpending.setFrameStyle(QFrame.Panel | QFrame.Sunken)

        # Miners
        app = leprechaun.Application()
        self.wcpuminers = MinerList(app.cpuminers, app.cpupriorities)
        self.wgpuminers = MinerList(app.gpuminers, app.gpupriorities)

        # Layout -------------------------------------------------------------------------------------------------------
        # Earnings
        lyearnings = QHBoxLayout()
        lyearnings.setSpacing(2*rem())
        
        lytemp = QVBoxLayout()
        lytemp.setSpacing(0.5*rem())
        lytemp.addWidget(QLabel("Total earnings:"))
        lytemp.addWidget(self.wtotal)
        lyearnings.addLayout(lytemp)

        # lytemp = QVBoxLayout()
        # lytemp.setSpacing(0.5*rem())
        # lytemp.addWidget(QLabel("Last 24 H:"))
        # lytemp.addWidget(self.wtotal24h)
        # lyearnings.addLayout(lytemp)

        lytemp = QVBoxLayout()
        lytemp.setSpacing(0.5*rem())
        lytemp.addWidget(QLabel("Pending:"))
        lytemp.addWidget(self.wpending)
        lyearnings.addLayout(lytemp)

        lyearnings.insertStretch(0, 1)
        lyearnings.insertStretch(-1, 1)

        # Miners
        lyminers = QGridLayout()
        lyminers.addWidget(QLabel("CPU Miners:"), 0, 0)
        lyminers.addWidget(QLabel("GPU Miners:"), 0, 1)
        lyminers.addWidget(self.wcpuminers, 1, 0)
        lyminers.addWidget(self.wgpuminers, 1, 1)

        # Layout -------------------------------------------------------------------------------------------------------
        ly = QVBoxLayout()
        self.setLayout(ly)

        ly.addLayout(lyearnings)
        ly.addLayout(lyminers)
    
    def update(self):
        app = leprechaun.Application()

        self.wcpuminers.update(app.cpuactive)
        self.wgpuminers.update(app.gpuactive)

        known_ids = set()

        etotal = 0
        epending = 0

        for miner in chain(app.cpuminers.values(), app.gpuminers.values()):
            earnings = miner.earnings()
            currency = miner.currency
            price = usdprice(currency)

            if earnings["scope"] == "currency":
                earnings_id = f"__{currency}"

            if earnings["scope"] == "address":
                earnings_id = f"__{currency}_{miner.address}"

            if earnings["scope"] == "with-id":
                earnings_id = earnings["id"]
            
            if earnings_id in known_ids:
                continue
            
            known_ids.add(earnings_id)

            etotal += earnings["total"] * price
            epending += earnings["pending"] * price
        
        self.wtotal.setText(f" $ {etotal:.2f} ")
        self.wpending.setText(f" $ {epending:.2f} ")
    
    def closeEvent(self, event):
        super().closeEvent(event)
        self.deleteLater()
        app = leprechaun.Application()
        app.dashboard = None