# -*- coding: utf-8 -*-
# @author: mkaay

import re
from builtins import str

from PyQt4.QtCore import *
from PyQt4.QtGui import *


class NewPackageDock(QDockWidget):
    def __init__(self):
        QDockWidget.__init__(self, _("New Package"))
        self.setObjectName("New Package Dock")
        self.widget = NewPackageWindow(self)
        self.setWidget(self.widget)
        self.setAllowedAreas(Qt.RightDockWidgetArea | Qt.LeftDockWidgetArea)
        self.hide()

    def slotDone(self):
        text = str(self.widget.box.toPlainText())
        pw = str(self.widget.passwordInput.text())
        if not pw:
            pw = None
        lines = []
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            lines.append(line)
        self.emit(SIGNAL("done"), str(self.widget.nameInput.text()), lines, pw)
        self.widget.nameInput.setText("")
        self.widget.passwordInput.setText("")
        self.widget.box.clear()
        self.hide()

    def parseUri(self):

        text = str(self.widget.box.toPlainText())
        self.widget.box.setText("")
        result = re.findall(
            r"(?:ht|f)tps?:\/\/[a-zA-Z0-9\-\.\/\?=_&%#]+[<| |\"|\'|\r|\n|\t]{1}", text)
        for url in result:
            if "\n" or "\t" or "\r" or "\"" or "<" or "'" in url:
                url = url[:-1]
            self.widget.box.append("{} ".format(url))


class NewPackageWindow(QWidget):
    def __init__(self, dock):
        QWidget.__init__(self)
        self.dock = dock
        self.setLayout(QGridLayout())
        layout = self.layout()

        nameLabel = QLabel(_("Name"))
        nameInput = QLineEdit()
        passwordLabel = QLabel(_("Password"))
        passwordInput = QLineEdit()

        linksLabel = QLabel(_("Links in this Package"))

        self.box = QTextEdit()
        self.nameInput = nameInput
        self.passwordInput = passwordInput

        save = QPushButton(_("Create"))
        parseUri = QPushButton(_("Filter URLs"))

        layout.addWidget(nameLabel, 0, 0)
        layout.addWidget(nameInput, 0, 1)
        layout.addWidget(passwordLabel, 1, 0)
        layout.addWidget(passwordInput, 1, 1)
        layout.addWidget(linksLabel, 2, 0, 1, 2)
        layout.addWidget(self.box, 3, 0, 1, 2)
        layout.addWidget(parseUri, 4, 0, 1, 2)
        layout.addWidget(save, 5, 0, 1, 2)

        self.connect(save, SIGNAL("clicked()"), self.dock.slotDone)
        self.connect(parseUri, SIGNAL("clicked()"), self.dock.parseUri)
