# -*- coding: utf-8 -*-

from PyQt4.QtCore import Qt, SIGNAL
from PyQt4.QtGui import QLineEdit, QPalette, QColor, QLabel
import logging

def whatsThisFormat(title, text):
     #html = "<b>" + title + "</b><br><br>" + text
     html = "<table><tr><td><b>" + title + "</b></td></tr></table>" + "<table><tr><td>" + text + "</td></tr></table>"
     return html

class LineView(QLineEdit):
    def __init__(self, contents=""):
        QLineEdit.__init__(self, contents)
        # read-only
        self.setReadOnly(True)
        # set background color
        self.pal = QPalette(self.palette())
        newcolor = QColor(QLabel().palette().color(QPalette.Active, QLabel().backgroundRole()))
        self.pal.setColor(QPalette.Active, self.backgroundRole(), newcolor)
        self.pal.setColor(QPalette.Inactive, self.backgroundRole(), newcolor)
        self.setPalette(self.pal)
        # remove from taborder
        self.setFocusPolicy(Qt.NoFocus)
        # prohibit text selection
        self.connect(self, SIGNAL("selectionChanged()"), self.deselect)
        # disable context menu
        self.setContextMenuPolicy(Qt.NoContextMenu)
