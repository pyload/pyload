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
        if self.sections and self.psections:
            self.data = self.connector.getConfig()
            self.pdata = self.connector.getPluginConfig()

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

        self.data = self.connector.getConfig()
        self.pdata = self.connector.getPluginConfig()
        for k, section in self.data.iteritems():
            s = Section(section, general)
            self.sections[k] = s

        for k, section in self.pdata.iteritems():
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

        for k, section in enumerate(pdata):
            if k in sections:
                widget = sections[k]
                for item in section.items:
                    if item.name in widget.inputs:
                        i = widget.inputs[item.name]

                        if item.type == "int":
                            i.setValue(int(item.value))
                        elif not item.type.find(";") == -1:
                            i.setCurrentIndex(i.findText(item.value))
                        elif item.type == "bool":
                            if True if item.value.lower() in ("1","true", "on", "an","yes") else False:
                                i.setCurrentIndex(0)
                            else:
                                i.setCurrentIndex(1)
                        else:
                            i.setText(item.value)


    def saveConfig(self):
        self.data = self.connector.getConfig()
        self.pdata = self.connector.getPluginConfig()

        self.saveSection(self.sections, self.data)
        self.saveSection(self.psections, self.pdata, "plugin")


    def saveSection(self, sections, pdata, sec="core"):
        for k, section in enumerate(pdata):
            if k in sections:
                widget = sections[k]
                for item in section.items:
                    if item.name in widget.inputs:
                        i = widget.inputs[item.name]

                        #TODO : unresolved reference: option

                        if item.type == "int":
                            if i.value() != int(item.value):
                                self.connector.setConfigValue(k, option, i.value(), sec)
                        elif not item.type.find(";") == -1:
                            if i.currentText() != item.value:
                                self.connector.setConfigValue(k, option, i.currentText(), sec)
                        elif item.type == "bool":
                            if (True if item.value.lower() in ("1","true", "on", "an","yes") else False) ^ (not i.currentIndex()):
                                self.connector.setConfigValue(k, option, not i.currentIndex(), sec)
                        else:
                            if i.text() != item.value:
                                self.connector.setConfigValue(k, option, str(i.text()), sec)

class Section(QGroupBox):
    def __init__(self, data, parent, ctype="core"):
        self.data = data
        QGroupBox.__init__(self, data.description, parent)
        self.labels = {}
        self.inputs = {}
        self.ctype = ctype
        layout = QFormLayout(self)
        self.setLayout(layout)
        
        sw = QWidget()
        sw.setLayout(QVBoxLayout())
        sw.layout().addWidget(self)
        
        sa = QScrollArea()
        sa.setWidgetResizable(True)
        sa.setWidget(sw)
        sa.setFrameShape(sa.NoFrame)
        
        parent.addTab(sa, data.description)
        
        for option in self.data.items:
            if option.type == "int":
                i = QSpinBox(self)
                i.setMaximum(999999)
                i.setValue(int(option.value))
            elif not option.type.find(";") == -1:
                choices = option.type.split(";")
                i = QComboBox(self)
                i.addItems(choices)
                i.setCurrentIndex(i.findText(option.value))
            elif option.type == "bool":
                i = QComboBox(self)
                i.addItem(_("Yes"), QVariant(True))
                i.addItem(_("No"), QVariant(False))
                if True if option.value.lower() in ("1","true", "on", "an","yes") else False:
                    i.setCurrentIndex(0)
                else:
                    i.setCurrentIndex(1)
            else:
                i = QLineEdit(self)
                i.setText(option.value)
            layout.addRow(option.description, i)
            layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
