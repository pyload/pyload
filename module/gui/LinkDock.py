# -*- coding: utf-8 -*-
# @author: mkaay


from builtins import str
from PyQt4.QtCore import *
from PyQt4.QtGui import *


class NewLinkDock(QDockWidget):
    def __init__(self):
        QDockWidget.__init__(self, "New Links")
        self.setObjectName("New Links Dock")
        self.widget = NewLinkWindow(self)
        self.setWidget(self.widget)
        self.setAllowedAreas(Qt.RightDockWidgetArea | Qt.LeftDockWidgetArea)
        self.hide()

    def slotDone(self):
        text = str(self.widget.box.toPlainText())
        lines = text.splitlines()
        self.emit(SIGNAL("done"), lines)
        self.widget.box.clear()
        self.hide()


class NewLinkWindow(QWidget):
    def __init__(self, dock):
        QWidget.__init__(self)
        self.dock = dock
        self.setLayout(QVBoxLayout())
        layout = self.layout()

        explanationLabel = QLabel("Select a package and then click Add button.")
        boxLabel = QLabel("Paste URLs here:")
        self.box = QTextEdit()

        save = QPushButton("Add")

        layout.addWidget(explanationLabel)
        layout.addWidget(boxLabel)
        layout.addWidget(self.box)
        layout.addWidget(save)

        self.connect(save, SIGNAL("clicked()"), self.dock.slotDone)
