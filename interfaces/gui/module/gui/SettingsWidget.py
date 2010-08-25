# -*- coding: utf-8 -*-
"""
    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 3 of the License,
    or (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
    See the GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program; if not, see <http://www.gnu.org/licenses/>.
    
    @author: mkaay
"""

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from sip import delete

class SettingsWidget(QWidget):
    def __init__(self):
        QWidget.__init__(self)
        self.connector = None
        self.sections = {}
        self.psections = {}
        self.data = None
        self.pdata = None
        self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
    
    def setConnector(self, connector):
        self.connector = connector
    
    def loadConfig(self):
        if self.layout():
            delete(self.layout())
        for s in self.sections.values()+self.psections.values():
            delete(s)
        self.sections = {}
        self.setLayout(QVBoxLayout())
        self.clearConfig()
        layout = self.layout()
        layout.setSizeConstraint(QLayout.SetMinAndMaxSize)
        
        self.data = self.connector.proxy.get_config()
        self.pdata = self.connector.proxy.get_plugin_config()
        for k, section in self.data.items():
            s = Section(section, self)
            self.sections[k] = s
            layout.addWidget(s)
        for k, section in self.pdata.items():
            s = Section(section, self, "plugin")
            self.psections[k] = s
            layout.addWidget(s)
        
        rel = QPushButton(_("Reload"))
        layout.addWidget(rel)
        save = QPushButton(_("Save"))
        #layout.addWidget(save)
        self.connect(rel, SIGNAL("clicked()"), self.loadConfig)
    
    def clearConfig(self):
        self.sections = {}

class Section(QGroupBox):
    def __init__(self, data, parent, ctype="core"):
        self.data = data
        QGroupBox.__init__(self, data["desc"], parent)
        self.labels = {}
        self.inputs = {}
        self.ctype = ctype
        layout = QGridLayout(self)
        self.setLayout(layout)
        
        row = 0
        for k, option in self.data.items():
            if k == "desc":
                continue
            l = QLabel(option["desc"], self)
            l.setMinimumWidth(400)
            self.labels[k] = l
            layout.addWidget(l, row, 0)
            if option["type"] == "int":
                i = QSpinBox(self)
                i.setMaximum(999999)
                i.setValue(int(option["value"]))
            elif not option["type"].find(";") == -1:
                choices = option["type"].split(";")
                i = QComboBox(self)
                i.addItems(choices)
                i.setCurrentIndex(i.findText(option["value"]))
            elif option["type"] == "bool":
                i = QComboBox(self)
                i.addItem(_("Yes"), QVariant(True))
                i.addItem(_("No"), QVariant(False))
                if option["value"]:
                    i.setCurrentIndex(0)
                else:
                    i.setCurrentIndex(1)
            else:
                i = QLineEdit(self)
                i.setText(option["value"])
            self.inputs[k] = i
            #i.setMaximumWidth(300)
            layout.addWidget(i, row, 1)
            row += 1
