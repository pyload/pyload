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
        self.setStyleSheet("QTabWidget::pane { border: 0px solid black;}")
    
    def setConnector(self, connector):
        self.connector = connector

    def loadConfig(self):
        if self.sections and self.psections:
            self.data = self.connector.proxy.get_config()
            self.pdata = self.connector.proxy.get_plugin_config()

            self.reloadSection(self.sections, self.data)
            self.reloadSection(self.psections, self.pdata)

            return

        if self.layout():
            delete(self.layout())

        for s in self.sections.values()+self.psections.values():
            delete(s)

        self.sections = {}
        self.setLayout(QVBoxLayout())
        self.clearConfig()
        layout = self.layout()
        layout.setSizeConstraint(QLayout.SetMinAndMaxSize)

        general = QTabWidget()
        self.general = general

        plugins = QTabWidget()
        self.plugins = plugins

        tab = QTabWidget()
        self.tab = tab
        
        gw = QWidget()
        gw.setLayout(QVBoxLayout())
        gw.layout().addWidget(self.general)
        pw = QWidget()
        pw.setLayout(QVBoxLayout())
        pw.layout().addWidget(self.plugins)
        tab.addTab(gw, _("General"))
        tab.addTab(pw, _("Plugins"))

        layout.addWidget(tab)

        self.data = self.connector.proxy.get_config()
        self.pdata = self.connector.proxy.get_plugin_config()
        for k, section in self.data.items():
            s = Section(section, general)
            self.sections[k] = s

        for k, section in self.pdata.items():
            s = Section(section, plugins, "plugin")
            self.psections[k] = s

        rel = QPushButton(_("Reload"))
        save = QPushButton(_("Save"))

        layout.addWidget(save)

        cont = QHBoxLayout()
        cont.addWidget(rel)
        cont.addWidget(save)

        layout.addLayout(cont)

        self.connect(save, SIGNAL("clicked()"), self.saveConfig)
        self.connect(rel, SIGNAL("clicked()"), self.loadConfig)

    def clearConfig(self):
        self.sections = {}

    def reloadSection(self, sections, pdata):

        for k, section in pdata.iteritems():
            if sections.has_key(k):
                widget = sections[k]
                for option,data in section.iteritems():
                    if widget.inputs.has_key(option):
                        i = widget.inputs[option]

                        if data["type"] == "int":
                            i.setValue(int(data["value"]))
                        elif not data["type"].find(";") == -1:
                            i.setCurrentIndex(i.findText(data["value"]))
                        elif data["type"] == "bool":
                            if data["value"]:
                                i.setCurrentIndex(0)
                            else:
                                i.setCurrentIndex(1)
                        else:
                            i.setText(data["value"])


    def saveConfig(self):
        self.data = self.connector.proxy.get_config()
        self.pdata = self.connector.proxy.get_plugin_config()

        self.saveSection(self.sections, self.data)
        self.saveSection(self.psections, self.pdata, "plugin")


    def saveSection(self, sections, pdata, sec="core"):
        for k, section in pdata.iteritems():
            if sections.has_key(k):
                widget = sections[k]
                for option,data in section.iteritems():
                    if widget.inputs.has_key(option):
                        i = widget.inputs[option]

                        if data["type"] == "int":
                            if i.value() != data["value"]:
                                self.connector.proxy.set_conf_val(k, option, i.value(), sec)
                        elif not data["type"].find(";") == -1:
                            if i.currentText() != data["value"]:
                                self.connector.proxy.set_conf_val(k, option, i.currentText(), sec)
                        elif data["type"] == "bool":
                            if (data["value"] ^ (not i.currentIndex())):
                                self.connector.proxy.set_conf_val(k, option, not i.currentIndex(), sec)
                        else:
                            if i.text() != data["value"]:
                                self.connector.proxy.set_conf_val(k, option, str(i.text()), sec)

class Section(QGroupBox):
    def __init__(self, data, parent, ctype="core"):
        self.data = data
        QGroupBox.__init__(self, data["desc"], parent)
        self.labels = {}
        self.inputs = {}
        self.ctype = ctype
        layout = QGridLayout(self)
        self.setLayout(layout)
        
        sw = QWidget()
        sw.setLayout(QVBoxLayout())
        sw.layout().addWidget(self)
        
        sa = QScrollArea()
        sa.setWidgetResizable(True)
        sa.setWidget(sw)
        #sa.setFrameShape(sa.NoFrame)
        
        parent.addTab(sa, data["desc"])
        
        row = 0
        for k, option in self.data.iteritems():
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
