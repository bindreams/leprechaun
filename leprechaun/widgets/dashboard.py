from itertools import chain
from concurrent.futures import ThreadPoolExecutor

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QFrame, QGridLayout, QLabel, QStyle, QStyledItemDelegate, QTextEdit, QTreeWidget, QTreeWidgetItem, QWidget
)

import leprechaun as le
from .base import defaultfont, font, rem, rempt


class Log(QTextEdit):
    _registry = {}

    def __init__(self, miner):
        super().__init__()
        self.setWindowTitle(f"Log file for miner '{miner.name}'")
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


class MinerTree(QTreeWidget):
    icon_ready = None
    icon_running = None
    icon_not_allowed = None
    icon_disabled = None
    icon_broken = None
    icon_paused = None

    class ItemDelegate(QStyledItemDelegate):
        def paint(self, painter, option, index):
            # create a styled option object
            super().initStyleOption(option, index)

            style = option.widget.style()
            indent = option.widget.indentation()

            # draw indented item
            option.rect.setLeft(indent)
            style.drawControl(QStyle.CE_ItemViewItem, option, painter, option.widget)

    def __init__(self, app):
        super().__init__()
        self.app = app

        self.wicpuminers = QTreeWidgetItem()
        self.wigpuminers = QTreeWidgetItem()
        self.addTopLevelItems([self.wicpuminers, self.wigpuminers])

        self.wicpuminers.setText(0, "CPU Miners")
        self.wicpuminers.setExpanded(True)
        for name in app.cpuminers:
            wi = QTreeWidgetItem()
            wi.setText(0, name)
            self.wicpuminers.addChild(wi)

        self.wigpuminers.setText(0, "GPU Miners")
        self.wigpuminers.setExpanded(True)
        for name in app.gpuminers:
            wi = QTreeWidgetItem()
            wi.setText(0, name)
            self.wigpuminers.addChild(wi)

        self.setHeaderHidden(True)
        self.setIconSize(QSize(rem()*1.6, rem()*1.6))
        self.itemDoubleClicked.connect(self.onItemDoubleClicked)
        self.setItemDelegate(self.ItemDelegate())

        if self.icon_ready is None:
            MinerTree.icon_ready = QIcon(str(le.sdata_dir / "icons" / "status-ready.svg"))
            MinerTree.icon_running = QIcon(str(le.sdata_dir / "icons" / "status-running.svg"))
            MinerTree.icon_not_allowed = QIcon(str(le.sdata_dir / "icons" / "status-not-allowed.svg"))
            MinerTree.icon_disabled = QIcon(str(le.sdata_dir / "icons" / "status-disabled.svg"))
            MinerTree.icon_broken = QIcon(str(le.sdata_dir / "icons" / "status-broken.svg"))
            MinerTree.icon_paused = QIcon(str(le.sdata_dir / "icons" / "status-paused.svg"))

    def update(self):
        for name, miner in chain(self.app.cpuminers.items(), self.app.gpuminers.items()):
            item = self.findItems(name, Qt.MatchExactly | Qt.MatchRecursive)[0]

            if miner.running:
                item.setIcon(0, self.icon_running)
            elif miner.broken:
                item.setIcon(0, self.icon_broken)
            elif not miner.enabled:
                item.setIcon(0, self.icon_disabled)
            elif self.app.paused:
                item.setIcon(0, self.icon_paused)
            elif not miner.allowed:
                item.setIcon(0, self.icon_not_allowed)
            else:
                item.setIcon(0, self.icon_ready)

            # For some reason, with custom item delegate, viewport does not update when
            # a mouse is not moving over it
            self.viewport().update()

    def onItemDoubleClicked(self, item):
        name = item.text(0)

        if item.parent() == self.wicpuminers:
            wlog = Log(self.app.cpuminers[name])
        elif item.parent() == self.wigpuminers:
            wlog = Log(self.app.gpuminers[name])

        wlog.show()


class NumericLabel(QLabel):
    def __init__(self, text=""):
        super().__init__(text)

        self.setStyleSheet("""
            padding: 0 0.5em 0 0.5em;
            font: 18pt "Open Sans";
        """)
        self.setAlignment(Qt.AlignCenter)


class Dashboard(QWidget):
    closed = Signal()

    def __init__(self, app):
        super().__init__()
        self.app = app

        f = self.font()
        f.setPointSizeF(1.2*rempt())
        self.setFont(f)

        self.wtotal = NumericLabel("$‒‒.‒‒")
        self.wpending = NumericLabel("$‒‒.‒‒")
        self.wdaily = NumericLabel("$‒‒.‒‒")

        # Footer
        self.wcredits = QLabel()
        self.wcredits.setStyleSheet("color: #808080")
        self.wcredits.setText(
            "Currency information provided by <a href=\"https://minerstat.com/\"><span style=\"color:#808080;\">minerstat</span>")
        self.wcredits.setTextFormat(Qt.RichText)
        self.wcredits.setTextInteractionFlags(Qt.TextBrowserInteraction)
        self.wcredits.setOpenExternalLinks(True)
        self.wcredits.setFont(defaultfont())

        # Miners
        self.wminertree = MinerTree(app)

        # Dashboard async updater
        self.executor_earnings = ThreadPoolExecutor(max_workers=1)
        self.future_earnings = None

        # Layout -------------------------------------------------------------------------------------------------------
        self.setContentsMargins(0, 0, 0, 0)
        ly = QGridLayout()
        ly.setSpacing(10)
        ly.setContentsMargins(10, 10, 10, 10)
        self.setLayout(ly)

        ly.addWidget(QLabel("Total earnings:"), 0, 0)
        ly.addWidget(self.wtotal, 1, 0)

        ly.addWidget(QLabel("Daily earnings:"), 2, 0)
        ly.addWidget(self.wdaily, 3, 0)

        ly.addWidget(QLabel("Pending:"), 4, 0)
        ly.addWidget(self.wpending, 5, 0)

        ly.addWidget(self.wminertree, 0, 1, 7, 1)
        ly.setRowStretch(6, 1)

        ly.addWidget(self.wcredits, 7, 0, 1, 2)
        ly.setAlignment(self.wcredits, Qt.AlignHCenter)

    def update(self):
        self.wminertree.update()

        if self.future_earnings is None:
            # Asynchronously query earnings from all miners
            self.future_earnings = self.executor_earnings.submit(self.app.earnings)
        elif self.future_earnings.done():
            # If already queried and completed, process them
            self.wtotal.setText("$‒‒.‒‒")
            self.wpending.setText("$‒‒.‒‒")
            self.wdaily.setText("$‒‒.‒‒")

            try:
                earnings = self.future_earnings.result()
                self.wtotal.setText(f"${earnings.total:,.2f}")
                self.wpending.setText(f"${earnings.pending:,.2f}")

                if earnings.daily is not None:
                    self.wdaily.setText(f"${earnings.daily:,.2f}")
            except RuntimeError as e:
                self.app.log("Exception while updating dashboard earnings:", e)

            self.future_earnings = self.executor_earnings.submit(self.app.earnings)

    def closeEvent(self, event):
        super().closeEvent(event)
        self.app.dashboard = None
        self.deleteLater()

    def sizeHint(self):
        return QSize(rem()*27, rem()*25)
