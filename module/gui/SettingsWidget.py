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

from PyQt4.QtCore import QMutex, QMutexLocker, QStringList, Qt, QTimer, QVariant, SIGNAL
from PyQt4.QtGui import (QApplication, QCheckBox, QComboBox, QCompleter, QFormLayout, QGroupBox, QHBoxLayout, QLabel,
                         QLayout, QLineEdit, QPushButton, QScrollArea, QSizePolicy, QSpinBox, QStackedLayout,
                         QStringListModel, QTabWidget, QVBoxLayout, QWidget)

import logging
from sip import delete
from collections import OrderedDict
from module.gui.Tools import WidgetDisable


class SettingsWidget(QWidget):
    def __init__(self, corePermissions):
        QWidget.__init__(self)
        self.log = logging.getLogger("guilog")
        self.corePermissions = corePermissions

        self.connector = None
        self.sections = {}
        self.psections = {}
        self.data = None
        self.pdata = None
        self.mutex = QMutex()
        self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.pluginsSearchName = ""
        self.menuPlugins = []

    def setCorePermissions(self, corePermissions):
        self.corePermissions = corePermissions

    def setConnector(self, connector):
        self.connector = connector

    def loadConfig(self):
        if not self.corePermissions["SETTINGS"]:
            return
        QMutexLocker(self.mutex)
        wdgd = WidgetDisable(self)

        if self.sections and self.psections:
            self.data = self.connector.proxy.getConfig()
            self.pdata = self.connector.proxy.getPluginConfig()
            self.reloadSection(self.sections, self.data)
            self.reloadSection(self.psections, self.pdata)
            wdgd.Enable()
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

        self.tab     = QTabWidget()
        self.general = QTabWidget()
        self.plugins = QWidget()
        self.plugins.setLayout(QVBoxLayout())
        self.pluginsComboBox = QComboBox()
        self.pluginsMenuCheckBox = QCheckBox(_("Add To Menu"))
        cbsp = self.pluginsMenuCheckBox.sizePolicy()
        cbsp.setHorizontalPolicy(QSizePolicy.Maximum)
        self.pluginsMenuCheckBox.setSizePolicy(cbsp)
        hbox = QHBoxLayout()
        hbox.addWidget(self.pluginsComboBox)
        hbox.addWidget(self.pluginsMenuCheckBox)
        self.plugins.layout().addLayout(hbox)
        self.pluginsStacked = QStackedLayout()
        self.plugins.layout().addLayout(self.pluginsStacked)
        
        gw = QWidget()
        gw.setLayout(QVBoxLayout())
        gw.layout().addWidget(self.general)
        pw = QWidget()
        pw.setLayout(QVBoxLayout())
        pw.layout().addWidget(self.plugins)

        pws = QWidget()
        pws.setLayout(QHBoxLayout())

        self.pluginsSearchMessageLabel = QLabel()
        self.pluginsSearchMessageLabel.hide()
        pws.layout().addWidget(self.pluginsSearchMessageLabel)

        self.pluginsSearchLabel = QLabel()
        self.pluginsSearchLabel.setText(_("Search for a plugin:"))
        pws.layout().addWidget(self.pluginsSearchLabel)

        self.pluginsSearchCompleter = QStringListModel()
        cp = QCompleter()
        cp.setModel(self.pluginsSearchCompleter)
        cp.setCaseSensitivity(Qt.CaseInsensitive)
        self.pluginsSearchEditBox = QLineEdit()
        self.pluginsSearchEditBox.setPlaceholderText(_("Enter a plugin name or search string"))
        self.pluginsSearchEditBox.setCompleter(cp)
        pws.layout().addWidget(self.pluginsSearchEditBox)

        self.pluginsSearchFind = QPushButton(_("Find"))
        pws.layout().addWidget(self.pluginsSearchFind)
        self.pluginsSearchClear = QPushButton(_("Clear"))
        pws.layout().addWidget(self.pluginsSearchClear)

        pw.layout().addWidget(pws)

        self.tab.addTab(gw, _("General"))
        self.tab.addTab(pw, _("Plugins"))

        layout.addWidget(self.tab)

        self.data = self.connector.proxy.getConfig()
        self.pdata = self.connector.proxy.getPluginConfig()

        self.data = OrderedDict(sorted(self.data.items(), key=lambda t: t[0]))      # add config tabs in alphabetical order
        self.pdata = OrderedDict(sorted(self.pdata.items(), key=lambda t: t[0]))    # add plugin tabs in alphabetical order

        for k, section in self.data.iteritems():
            s = Section(section, self.general)
            self.general.addTab(s.sa, section.description)
            self.sections[k] = s
            QApplication.processEvents()

        sl = QStringList()
        for k, section in self.pdata.iteritems():
            s = Section(section, self.plugins, "plugin")
            self.psections[k] = s
            self.pluginsComboBox.addItem(section.description)
            self.pluginsStacked.addWidget(s.sa)
            sl.append(section.description)
            QApplication.processEvents()
        self.pluginsMenuCheckBox.setChecked(str(self.pluginsComboBox.currentText()) in self.menuPlugins)

        self.pluginsSearchCompleter.setStringList(sl)

        self.reload = QPushButton(_("Reload All 'Server Settings' Forms"))
        self.save = QPushButton(_("Apply All 'Server Settings' Forms"))

        cont = QHBoxLayout()
        cont.addWidget(self.reload)
        cont.addWidget(self.save)

        layout.addLayout(cont)

        self.connect(self.pluginsSearchEditBox, SIGNAL("returnPressed()"), self.slotPluginsSearchFind)
        self.connect(self.pluginsSearchFind, SIGNAL("clicked()"), self.slotPluginsSearchFind)
        self.connect(self.pluginsSearchClear, SIGNAL("clicked()"), self.slotPluginsSearchClear)
        self.connect(self.save, SIGNAL("clicked()"), self.saveConfig)
        self.connect(self.reload, SIGNAL("clicked()"), self.loadConfig)
        self.connect(self.pluginsComboBox, SIGNAL("activated(int)"), self.slotPluginsComboBoxActivated)
        self.connect(self.pluginsMenuCheckBox, SIGNAL("clicked(bool)"), self.slotPluginsMenuCheckBoxClicked)

        wdgd.Enable()

    def clearConfig(self):
        self.sections = {}

    @classmethod
    def reloadSection(self, sections, pdata):
        for k, section in pdata.iteritems():
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
                            if True if item.value.lower() in ("1", "true", "on", "an", "yes") else False:
                                i.setCurrentIndex(0)
                            else:
                                i.setCurrentIndex(1)
                        else:
                            i.setText(item.value)

    def saveConfig(self):
        if not self.corePermissions["SETTINGS"]:
            return
        wdgd = WidgetDisable(self)
        self.data = self.connector.proxy.getConfig()
        self.pdata = self.connector.proxy.getPluginConfig()
        self.saveSection(self.sections, self.data)
        self.saveSection(self.psections, self.pdata, "plugin")
        self.data = self.connector.proxy.getConfig()
        self.pdata = self.connector.proxy.getPluginConfig()
        self.reloadSection(self.sections, self.data)
        self.reloadSection(self.psections, self.pdata)
        wdgd.Enable()

    def saveSection(self, sections, pdata, sec="core"):
        if not self.corePermissions["SETTINGS"]:
            return
        for k, section in pdata.iteritems():
            if k in sections:
                widget = sections[k]
                for item in section.items:
                    if item.name in widget.inputs:
                        opt = str(item.name)
                        cat = str(k)
                        # NOTE: Qt strings are of type QString
                        i = widget.inputs[item.name]
                        if item.type == "int":               # QSpinBox
                            if i.value() != int(item.value):
                                self.connector.proxy.setConfigValue(cat, opt, str(i.value()), sec)
                        elif not item.type.find(";") == -1:  # QComboBox
                            if i.currentText() != item.value:
                                self.connector.proxy.setConfigValue(cat, opt, str(i.currentText()), sec)
                        elif item.type == "bool":            # QComboBox
                            if (True if item.value.lower() in ("1", "true", "on", "an", "yes") else False) ^ (not i.currentIndex()):
                                self.connector.proxy.setConfigValue(cat, opt, str(not i.currentIndex()), sec)
                        else:
                            if i.text() != item.value:       # QLineEdit
                                self.connector.proxy.setConfigValue(cat, opt, unicode(i.text()), sec)

    def setSpeedLimitFromToolbar(self, enab, rate):
        if not self.corePermissions["SETTINGS"]:
            return
        QMutexLocker(self.mutex)
        if not (self.data and self.sections):
            return
        err1 = err2 = True
        for k, section in self.data.iteritems():
            if k in self.sections:
                if section.name == "download":
                    widget = self.sections[k]
                    for item in section.items:
                        if item.name == "limit_speed":
                            item.value = enab
                            if item.name in widget.inputs:
                                err1 = False
                                i = widget.inputs[item.name]
                                if True if enab.lower() in ("1", "true", "on", "an", "yes") else False:
                                    i.setCurrentIndex(0)
                                else:
                                    i.setCurrentIndex(1)
                        elif item.name == "max_speed":
                            item.value = rate
                            if item.name in widget.inputs:
                                err2 = False
                                i = widget.inputs[item.name]
                                i.setValue(int(rate))
        if err1 or err2:
            self.log.error("SettingsWidget.setSpeedLimitFromToolbar: Failed to update Server Settings tab, err1:%s err2:%s" % (err1, err2))

    def setMaxParallelDownloadsFromToolbar(self, value):
        if not self.corePermissions["SETTINGS"]:
            return
        QMutexLocker(self.mutex)
        if not (self.data and self.sections):
            return
        err = True
        for k, section in self.data.iteritems():
            if k in self.sections:
                if section.name == "download":
                    widget = self.sections[k]
                    for item in section.items:
                        if item.name == "max_downloads":
                            item.value = value
                            if item.name in widget.inputs:
                                err = False
                                i = widget.inputs[item.name]
                                i.setValue(int(value))
        if err:
            self.log.error("SettingsWidget.setMaxParallelDownloadsFromToolbar: Failed to update Server Settings tab.")

    def slotPluginsSearchClear(self):
        self.pluginsSearchName = ""
        self.pluginsSearchEditBox.setText("")

    def slotPluginsSearchFind(self):
        name = self.pluginsSearchEditBox.text()
        if not name:
            return
        if name.compare(self.pluginsSearchName, Qt.CaseInsensitive) != 0:
            self.pluginsSearchName = name
            self.pluginsSearchHitCount = 0
            self.pluginsSearchIndex = -1

        # start search from current plugin
        ci = self.pluginsComboBox.currentIndex()
        mc = self.pluginsSearchHitCount
        for i in range(self.pluginsComboBox.currentIndex(), self.pluginsComboBox.count()):
            if self.pluginsComboBox.itemText(i).indexOf(name, 0, Qt.CaseInsensitive) != -1:
                if i == self.pluginsComboBox.currentIndex():
                    if mc == 0:
                        self.pluginsSearchHitCount += 1
                        self.pluginsSearchIndex = i
                        break
                    else:
                        continue
                self.pluginsComboBox.setCurrentIndex(i)
                self.pluginsStacked.setCurrentIndex(i)
                if mc == 0:
                    self.pluginsSearchHitCount += 1
                    self.pluginsSearchIndex = i
                elif mc == 1:
                    if i != self.pluginsSearchIndex:
                        self.pluginsSearchHitCount += 1
                    self.pluginsSearchIndex = i
                else:
                    self.pluginsSearchHitCount += 1
                break

        # wrap, continue search from first plugin
        if self.pluginsSearchHitCount == mc:
            for i in range(0, self.pluginsComboBox.currentIndex()):
                if self.pluginsComboBox.itemText(i).indexOf(name, 0, Qt.CaseInsensitive) != -1:
                    if i == self.pluginsComboBox.currentIndex():
                        break
                    self.pluginsComboBox.setCurrentIndex(i)
                    self.pluginsStacked.setCurrentIndex(i)
                    if mc == 0:
                        self.pluginsSearchHitCount += 1
                        self.pluginsSearchIndex = i
                    elif mc == 1:
                        if i != self.pluginsSearchIndex:
                            self.pluginsSearchHitCount += 1
                            self.pluginsSearchIndex = i
                    else:
                        self.pluginsSearchHitCount += 1
                    break

        # status message
        if self.pluginsSearchHitCount == mc:
            if self.pluginsSearchHitCount < 1:
                self.pluginsSearchName = ""
                self.pluginsSearchMessageLabel.setText("<b>" + _("Not found") + "</b>")
                self.pluginsSearchMessage()
            elif self.pluginsComboBox.currentIndex() == ci:
                self.pluginsSearchMessageLabel.setText("<b>" + _("No more matches") + "</b>")
                self.pluginsSearchMessage()

        self.pluginsSearchEditBox.setFocus()

    def pluginsSearchMessage(self):
        self.pluginsSearchMessageLabel.setFixedHeight(self.pluginsSearchFind.height())
        self.pluginsSearchMessageLabel.show()
        self.pluginsSearchLabel.hide()
        self.pluginsSearchEditBox.hide()
        self.pluginsSearchFind.hide()
        self.pluginsSearchClear.hide()
        QTimer.singleShot(2000, self.slotPluginsSearchShow)

    def slotPluginsSearchShow(self):
        self.pluginsSearchMessageLabel.hide()
        self.pluginsSearchLabel.show()
        self.pluginsSearchEditBox.show()
        self.pluginsSearchFind.show()
        self.pluginsSearchClear.show()

    def slotPluginsComboBoxActivated(self, index):
        self.pluginsMenuCheckBox.setChecked(str(self.pluginsComboBox.currentText()) in self.menuPlugins)
        self.pluginsStacked.setCurrentIndex(index)  # Page

    def slotPluginsMenuCheckBoxClicked(self, checked):
        name = str(self.pluginsComboBox.currentText())
        if checked:
            if name not in self.menuPlugins:
                self.menuPlugins.append(name)
        else:
            if name in self.menuPlugins:
                self.menuPlugins.remove(name)
        self.menuPlugins = sorted(self.menuPlugins)
        self.emit(SIGNAL("setupPluginsMenu"))

class Section(QGroupBox):
    def __init__(self, data, parent, ctype="core"):
        title = data.description
        if ctype == "plugin" and data.outline:
            title = data.outline
        QGroupBox.__init__(self, title, parent)
        self.log = logging.getLogger("guilog")
        self.data = data
        self.ctype = ctype
        
        #self.labels = {}
        self.inputs = {}
        
        layout = QFormLayout(self)
        self.setLayout(layout)
        
        hb = QWidget()
        hb.setLayout(QHBoxLayout())
        hb.layout().addWidget(self)
        hb.layout().addSpacing(20)  # extra space left of the scrollbar
        
        sw = QWidget()
        sw.setLayout(QVBoxLayout())
        #sw.layout().addWidget(self)
        sw.layout().addWidget(hb)
        
        self.sa = QScrollArea()
        self.sa.setWidgetResizable(True)
        self.sa.setWidget(sw)
        self.sa.setFrameShape(self.sa.NoFrame)
        
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
                i.addItem("Yes", QVariant(True))
                i.addItem("No", QVariant(False))
                if True if option.value.lower() in ("1", "true", "on", "an", "yes") else False:
                    i.setCurrentIndex(0)
                else:
                    i.setCurrentIndex(1)
            else:
                i = QLineEdit(self)
                i.setText(option.value)
            self.inputs[option.name] = i;
            layout.addRow(option.description, i)
            layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
