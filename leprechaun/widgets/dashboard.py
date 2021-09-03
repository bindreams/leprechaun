from itertools import chain
from PySide2.QtCore import Qt, Signal, QSize
from PySide2.QtGui import QIcon
from PySide2.QtWidgets import QGridLayout, QLabel, QWidget, QTextEdit, QFrame, QListWidget
import leprechaun as le
from leprechaun.api.messari import usdprice
from .base import font, rem, rempt


class Log(QTextEdit):
    _registry = {}

    def __init__(self, name, miner):
        super().__init__()
        self.setWindowTitle(f"Log file for miner '{name}'")
        self.setAttribute(Qt.WA_DeleteOnClose, True)

        self.setFontFamily("Consolas")
        self.setLineWrapMode(QTextEdit.NoWrap)
        self.setReadOnly(True)
        self.setText("\n".join(miner.log))
        miner.logUpdated.connect(self.append)

        # Add self to a registry to not get accidentally deleted
        self._registry[id(self)] = self
    
    def append(self, text: str):
        scrollbar = self.verticalScrollBar()
        at_bottom = scrollbar.value() == scrollbar.maximum()

        super().append(text)

        if at_bottom:
            scrollbar.setValue(scrollbar.maximum())

    def closeEvent(self, event):
        super().closeEvent(event)
        self._registry.pop(id(self))


class MinerStack(QListWidget):
    icon_ready       = None
    icon_running     = None
    icon_not_allowed = None
    icon_disabled    = None
    icon_broken      = None
    icon_paused      = None

    def __init__(self, app, miners):
        super().__init__()
        self.app = app
        self.miners = miners

        for name in miners:
            self.addItem(name)
        
        self.setIconSize(QSize(rem()*2, rem()*2))
        self.itemDoubleClicked.connect(self.onItemDoubleClicked)

        if self.icon_ready is None:
            MinerStack.icon_ready       = QIcon(str(le.sdata_dir / "icons" / "status-ready.svg"))
            MinerStack.icon_running     = QIcon(str(le.sdata_dir / "icons" / "status-running.svg"))
            MinerStack.icon_not_allowed = QIcon(str(le.sdata_dir / "icons" / "status-not-allowed.svg"))
            MinerStack.icon_disabled    = QIcon(str(le.sdata_dir / "icons" / "status-disabled.svg"))
            MinerStack.icon_broken      = QIcon(str(le.sdata_dir / "icons" / "status-broken.svg"))
            MinerStack.icon_paused      = QIcon(str(le.sdata_dir / "icons" / "status-paused.svg"))
    
    def update(self):
        for i in range(self.count()):
            item = self.item(i)
            name = item.text()
            miner = self.miners[name]

            if miner.running:
                item.setIcon(self.icon_running)
            elif miner.broken:
                item.setIcon(self.icon_broken)
            elif not miner.enabled:
                item.setIcon(self.icon_disabled)
            elif self.app.paused:
                item.setIcon(self.icon_paused)
            elif not miner.allowed:
                item.setIcon(self.icon_not_allowed)
            else:
                item.setIcon(self.icon_ready)

    def onItemDoubleClicked(self, item):
        name = item.text()
        wlog = Log(name, self.miners[name])
        wlog.show()


class Dashboard(QWidget):
    closed = Signal()

    def __init__(self, app):
        super().__init__()
        self.app = app

        moneyfont = font("Open Sans", size=2.25*rempt())

        f = self.font()
        f.setPointSizeF(1.2*rempt())
        self.setFont(f)

        self.wtotal = QLabel()
        self.wtotal.setStyleSheet("padding: 0 0.5em 0 0.5em")
        self.wtotal.setFont(moneyfont)
        self.wtotal.setAlignment(Qt.AlignCenter)
        self.wtotal.setFrameStyle(QFrame.Panel | QFrame.Sunken)

        self.wpending = QLabel()
        self.wpending.setStyleSheet("padding: 0 0.5em 0 0.5em")
        self.wpending.setFont(moneyfont)
        self.wpending.setAlignment(Qt.AlignCenter)
        self.wpending.setFrameStyle(QFrame.Panel | QFrame.Sunken)

        # Miners
        self.wcpuminers = MinerStack(app, app.cpuminers)
        self.wgpuminers = MinerStack(app, app.gpuminers)

        # Layout -------------------------------------------------------------------------------------------------------
        ly = QGridLayout()
        self.setLayout(ly)

        ly.addWidget(QLabel("Total earnings:"), 0, 0)
        ly.addWidget(QLabel("Pending:"), 0, 1)
        ly.addWidget(self.wtotal, 1, 0)
        ly.addWidget(self.wpending, 1, 1)

        ly.addWidget(QLabel("CPU Miners:"), 2, 0)
        ly.addWidget(QLabel("GPU Miners:"), 2, 1)
        ly.addWidget(self.wcpuminers, 3, 0)
        ly.addWidget(self.wgpuminers, 3, 1)
    
    def update(self):
        self.wcpuminers.update()
        self.wgpuminers.update()

        known_ids = set()

        self.wtotal.setText("$--.--")
        self.wpending.setText("$--.--")

        etotal = 0
        epending = 0

        for miner in chain(self.app.cpuminers.values(), self.app.gpuminers.values()):
            try:
                earnings = miner.earnings()
                currency = miner.currency
                price = usdprice(currency)

                if earnings["scope"] == "currency":
                    earnings_id = (currency,)

                if earnings["scope"] == "address":
                    earnings_id = (currency, miner.address)

                if earnings["scope"] == "with-id":
                    earnings_id = earnings["id"]
                
                if earnings_id in known_ids:
                    continue
                
                known_ids.add(earnings_id)

                etotal += earnings["total"] * price
                epending += earnings["pending"] * price
            except OSError as e:
                self.app.log(f"Exception raised while getting earnings of miner '{miner.name}':", e)
                return  # Skip setting earnings
        
        self.wtotal.setText(f"${etotal:,.2f}")
        self.wpending.setText(f"${epending:,.2f}")
    
    def closeEvent(self, event):
        super().closeEvent(event)
        self.app.dashboard = None
        self.deleteLater()

    def sizeHint(self):
        return QSize(rem()*30, rem()*20)
