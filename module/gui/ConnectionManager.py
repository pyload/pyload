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

import logging
from os.path import join
from uuid import uuid4 as uuid

from module.gui.Tools import whatsThisFormat

class ConnectionManager(QDialog):
    def __init__(self):
        QDialog.__init__(self)
        self.log = logging.getLogger("guilog")
        
        self.setWindowFlags(self.windowFlags() | Qt.WindowContextHelpButtonHint)
        self.setWindowTitle(_("Connection Manager"))
        self.setWindowIcon(QIcon(join(pypath, "icons", "logo.png")))
        
        mainLayout   = QHBoxLayout()
        boxLayout    = QVBoxLayout()
        buttonLayout = QVBoxLayout()
        
        self.connList = self.ListWidget()
        self.connList.setDragDropMode(QAbstractItemView.InternalMove)
        boxLayout.addWidget(QLabel(_("Connections") + ":"))
        boxLayout.addWidget(self.connList)
        
        self.btnNew     = QPushButton(_("New"))
        self.btnEdit    = QPushButton(_("Edit"))
        self.btnDefault = QPushButton(_("Default"))
        self.btnDefault.setWhatsThis(whatsThisFormat(_("Default"), _("Toggles the default connection.")))
        self.btnRemove  = QPushButton(_("Remove"))
        self.btnConnect = QPushButton(_("Connect"))
        self.btnConnect.setDefault(True)
        buttonLayout.addWidget(self.btnNew)
        buttonLayout.addWidget(self.btnEdit)
        buttonLayout.addWidget(self.btnDefault)
        buttonLayout.addWidget(self.btnRemove)
        buttonLayout.addStretch()
        buttonLayout.addWidget(self.btnConnect)
        
        mainLayout.addLayout(boxLayout)
        mainLayout.addLayout(buttonLayout)
        self.setLayout(mainLayout)
        
        self.edit = self.EditWindow()
        self.connectSignals()
    
    def connectSignals(self):
        self.connect(self,            SIGNAL("setConnections"), self.setConnections)
        self.connect(self,            SIGNAL("setCurrentItem"), self.slotSetCurrentItem)
        self.connect(self.btnNew,     SIGNAL("clicked()"), self.slotNew)
        self.connect(self.btnEdit,    SIGNAL("clicked()"), self.slotEdit)
        self.connect(self.btnDefault, SIGNAL("clicked()"), self.slotDefault)
        self.connect(self.btnRemove,  SIGNAL("clicked()"), self.slotRemove)
        self.connect(self.btnConnect, SIGNAL("clicked()"), self.slotConnect)
        self.connect(self.edit,       SIGNAL("save"),      self.slotSave)
        self.connect(self.connList,   SIGNAL("saveAll"),   self.slotSaveAll)
        self.connect(self.connList,   SIGNAL("itemDoubleClicked(QListWidgetItem *)"), self.slotItemDoubleClicked)
    
    def setConnections(self, connections):
        self.connList.clear()
        for conn in connections:
            item = QListWidgetItem()
            item.setData(Qt.DisplayRole, QVariant(conn["name"]))
            item.setData(Qt.UserRole, QVariant(conn))
            self.connList.addItem(item)
            if conn["default"]:
                item.setData(Qt.DisplayRole, QVariant(conn["name"] + " (" + _("Default") + ")"))
                self.connList.setCurrentItem(item)
            else:
                self.connList.setCurrentRow(0)
    
    def slotSetCurrentItem(self, l):
        id = l["id"]
        count = self.connList.count()
        for i in range(count):
            item = self.connList.item(i)
            d = item.data(Qt.UserRole).toPyObject()
            if self.cleanDict(d)["id"] == id:
                self.connList.setCurrentItem(item)
                break
    
    def slotNew(self):
        self.edit.setWindowTitle(_("New"))
        data = {"id":uuid().hex, "type":"remote", "default":False, "name":"", "host":"", "port":7227, "user":"", "password":"", "cnlpf":False, "cnlpfPort":9666, "cnlpfGetPort":False}
        self.edit.setData(data)
        self.edit.controls["name"].setFocus(Qt.OtherFocusReason)
        self.edit.exec_()
    
    def slotEdit(self):
        self.edit.setWindowTitle(_("Edit"))
        item = self.connList.currentItem()
        data = item.data(Qt.UserRole).toPyObject()
        data = self.cleanDict(data)
        self.edit.setData(data)
        self.edit.controls["cancel"].setFocus(Qt.OtherFocusReason)
        self.edit.exec_()
    
    def slotRemove(self):
        item = self.connList.currentItem()
        data = item.data(Qt.UserRole).toPyObject()
        data = self.cleanDict(data)
        row = self.connList.currentRow()
        self.emit(SIGNAL("removeConnection"), data)
        if row >= self.connList.count():
            row = self.connList.count() - 1
        self.connList.setCurrentRow(row)
    
    def slotConnect(self):
        item = self.connList.currentItem()
        data = item.data(Qt.UserRole).toPyObject()
        data = self.cleanDict(data)
        self.emit(SIGNAL("connect"), data)
    
    def cleanDict(self, data):
        tmp = {}
        for k, d in data.items():
            if type(d) == QString:
                tmp[str(k)] = unicode(d)    # get rid of QString asap
            else:
                tmp[str(k)] = d
        return tmp
    
    def slotSave(self, data):
        id = self.cleanDict(data)["id"]
        self.emit(SIGNAL("saveConnection"), data)
        count = self.connList.count()
        for i in range(count):
            item = self.connList.item(i)
            d = item.data(Qt.UserRole).toPyObject()
            if self.cleanDict(d)["id"] == id:
                self.connList.setCurrentItem(item)
                break
    
    def slotSaveAll(self):
        item = self.connList.currentItem()
        data = item.data(Qt.UserRole).toPyObject()
        id = self.cleanDict(data)["id"]
        connections = []
        count = self.connList.count()
        for i in range(count):
            item = self.connList.item(i)
            data = item.data(Qt.UserRole).toPyObject()
            data = self.cleanDict(data)
            self.edit.setData(data)
            data = self.edit.getData()
            connections.append(data)
        self.emit(SIGNAL("saveAllConnections"), connections)
        count = self.connList.count()
        for i in range(count):
            item = self.connList.item(i)
            d = item.data(Qt.UserRole).toPyObject()
            if self.cleanDict(d)["id"] == id:
                self.connList.setCurrentItem(item)
                break
    
    def slotItemDoubleClicked(self, item):
        # this fixes a segfault that happens when emitting "connect" directly from here
        QTimer.singleShot(0, self.slotConnect) 
    
    def slotDefault(self):
        currentRow = self.connList.currentRow()
        item = self.connList.currentItem()
        data = item.data(Qt.UserRole).toPyObject()
        data = self.cleanDict(data)
        did = data["id"]
        self.setDefault(data, not data["default"])
        count = self.connList.count()
        for i in range(count):
            item = self.connList.item(i)
            data = item.data(Qt.UserRole).toPyObject()
            if self.cleanDict(data)["id"] == did:
                continue
            self.setDefault(data, False)
        self.connList.setCurrentRow(currentRow)
    
    def setDefault(self, data, state):
        data = self.cleanDict(data)
        self.edit.setData(data)
        data = self.edit.getData()
        data["default"] = state
        self.emit(SIGNAL("saveConnection"), data)
    
    def keyPressEvent(self, event):
        if event.key() != Qt.Key_Escape:
            QDialog.keyPressEvent(self, event)
    
    def closeEvent(self, event):
        event.ignore()
        self.emit(SIGNAL("quitConnWindow"))


    class ListWidget(QListWidget):
        def __init__(self):
            QListWidget.__init__(self)
            self.log = logging.getLogger("guilog")
        
        def dropEvent(self, event):
            QListWidget.dropEvent(self, event)
            self.emit(SIGNAL("saveAll"))


    class EditWindow(QDialog):
        def __init__(self):
            QDialog.__init__(self)
            self.log = logging.getLogger("guilog")
            
            self.setAttribute(Qt.WA_DeleteOnClose, False)
            self.setWindowFlags(self.windowFlags() | Qt.WindowContextHelpButtonHint)
            self.setWindowIcon(QIcon(join(pypath, "icons", "logo.png")))
            
            grid1 = QGridLayout()
            
            nameLabel  = QLabel(_("Name"))
            typeLabel  = QLabel(_("Type"))
            hostLabel  = QLabel(_("Host"))
            portLabel  = QLabel(_("Port"))
            userLabel  = QLabel(_("User"))
            pwLabel    = QLabel(_("Password"))
            
            name = QLineEdit()
            typeLocal    = QRadioButton(_("Local"))
            typeLocal.setWhatsThis(whatsThisFormat(_("Local"), _("Use this for administrator permissions on a local server that requires no authentication ('No authentication on local connections').")))
            typeInternal = QRadioButton(_("Internal"))
            typeInternal.setWhatsThis(whatsThisFormat(_("Internal"), _("Starts and connects to the internal server.")))
            typeRemote   = QRadioButton(_("Remote"))
            typeRemote.setWhatsThis(whatsThisFormat(_("Remote"), _("Connects to a remote server.")))
            typeBtnHbox = QHBoxLayout()
            typeBtnHbox.addWidget(typeLocal)
            typeBtnHbox.addWidget(typeInternal)
            typeBtnHbox.addWidget(typeRemote)
            typeBtnHbox.addSpacing(10)
            typeBtnHbox.addStretch(1)
            typeRemote.setChecked(True)
            host = QLineEdit()
            port = QSpinBox()
            port.setRange(1, 65535)
            user = QLineEdit()
            password = QLineEdit()
            password.setEchoMode(QLineEdit.Password)
            
            nameHbox = QHBoxLayout()
            nameHbox.addWidget(nameLabel)
            nameHbox.addWidget(name)
            
            grid1.addWidget(typeLabel,    0, 0)
            grid1.addLayout(typeBtnHbox,  0, 1)
            grid1.addWidget(hostLabel,    1, 0)
            grid1.addWidget(host,         1, 1)
            grid1.addWidget(portLabel,    2, 0)
            grid1.addWidget(port,         2, 1)
            grid1.addWidget(userLabel,    3, 0)
            grid1.addWidget(user,         3, 1)
            grid1.addWidget(pwLabel,      4, 0)
            grid1.addWidget(password,     4, 1)
            #grid1.setRowMinimumHeight(    5, 7)
            
            gb1 = QGroupBox(_("Login"))
            gb1.setLayout(grid1)
            
            grid2 = QGridLayout()
            
            cnlpfPortLabel  = QLabel(_("Remote Port"))
            cnlpfPort = QSpinBox()
            cnlpfPort.setRange(1, 65535)
            cnlpfGetPort = QCheckBox(_("Get Remote Port from Server Settings"))
            cnlpfGetPort.setWhatsThis(whatsThisFormat(_("Get Remote Port from Server Settings"), _("Needs") + " '" + _("Settings") + "'" + " (SETTINGS) " + _("permission on the server.")))
            
            grid2.addWidget(cnlpfPortLabel, 0, 0, 1, 1)
            grid2.addWidget(cnlpfPort,      0, 1, 1, 1)
            grid2.addWidget(cnlpfGetPort,   1, 0, 1, 2)
            grid2.setColumnStretch(1, 1)
            #grid2.setRowMinimumHeight(2, 7)
            
            cnlpf = QGroupBox(_("Enable ClickNLoad Port Forwarding"))
            cnlpf.setCheckable(True)
            cnlpf.setLayout(grid2)
            
            self.buttons = QDialogButtonBox(Qt.Horizontal)
            save = self.buttons.addButton(QDialogButtonBox.Save)
            cancel = self.buttons.addButton(QDialogButtonBox.Cancel)
            self.buttons.button(QDialogButtonBox.Save).setText(_("Save"))
            self.buttons.button(QDialogButtonBox.Cancel).setText(_("Cancel"))
            
            vbox = QVBoxLayout()
            vbox.addLayout(nameHbox)
            vbox.addSpacing(3)
            vbox.addWidget(gb1)
            vbox.addWidget(cnlpf)
            vbox.addWidget(self.buttons)
            
            self.setLayout(vbox)
            #self.setMinimumWidth(300)
            self.adjustSize()
            self.setFixedHeight(self.height())
            
            self.id      = None
            self.default = None
            
            # keep references of the QDialog elements
            self.controls = { "name":         name,
                              "typeLocal":    typeLocal,
                              "typeInternal": typeInternal,
                              "typeRemote":   typeRemote,
                              "host":         host,
                              "port":         port,
                              "user":         user,
                              "password":     password,
                              "cnlpf":        cnlpf,
                              "cnlpfPort":    cnlpfPort,
                              "cnlpfGetPort": cnlpfGetPort,
                              "save":         save,
                              "cancel":       cancel }
            
            self.connect(cancel, SIGNAL("clicked()"), self.hide)
            self.connect(save,   SIGNAL("clicked()"), self.slotDone)
            self.connect(typeLocal,    SIGNAL("clicked()"), self.slotTypeChanged)
            self.connect(typeInternal, SIGNAL("clicked()"), self.slotTypeChanged)
            self.connect(typeRemote,   SIGNAL("clicked()"), self.slotTypeChanged)
            self.connect(cnlpfGetPort, SIGNAL("toggled(bool)"), cnlpfPort.setDisabled)
        
        def setData(self, data):
            if not data:
                return
            self.id = data["id"]
            self.default = data["default"]
            self.controls["name"].setText(data["name"])
            if data["type"] == "local":
                self.controls["typeLocal"].setChecked(True)
            elif data["type"] == "internal":
                self.controls["typeInternal"].setChecked(True)
            elif data["type"] == "remote":
                self.controls["typeRemote"].setChecked(True)
            else:
                raise ValueError("Invalid connection type: '%s'" % unicode(data["type"]))
            if data["type"] == "local" or data["type"] == "internal":
                self.controls["host"].setText("")
                self.controls["port"].setValue(1)
                self.controls["user"].setText("")
                self.controls["cnlpf"].setChecked(False)
                self.controls["cnlpfPort"].setValue(1)
                self.controls["cnlpfGetPort"].setChecked(False)
                self.controls["host"].setDisabled(True)
                self.controls["port"].setDisabled(True)
                self.controls["user"].setDisabled(True)
                self.controls["password"].setDisabled(True)
                self.controls["cnlpf"].setDisabled(True)
            else:
                self.controls["host"].setText(data["host"])
                self.controls["port"].setValue(data["port"])
                self.controls["user"].setText(data["user"])
                self.controls["password"].setText(data["password"])
                self.controls["cnlpf"].setChecked(data["cnlpf"])
                self.controls["cnlpfPort"].setValue(data["cnlpfPort"])
                self.controls["cnlpfGetPort"].setChecked(data["cnlpfGetPort"])
                self.controls["host"].setDisabled(False)
                self.controls["port"].setDisabled(False)
                self.controls["user"].setDisabled(False)
                self.controls["password"].setDisabled(False)
                self.controls["cnlpf"].setDisabled(False)
        
        def slotTypeChanged(self):
            if self.controls["typeLocal"].isChecked() or self.controls["typeInternal"].isChecked():
                self.controls["host"].setDisabled(True)
                self.controls["port"].setDisabled(True)
                self.controls["user"].setDisabled(True)
                self.controls["password"].setDisabled(True)
                self.controls["cnlpf"].setDisabled(True)
                self.controls["cnlpf"].setChecked(False)
            else:
                self.controls["host"].setDisabled(False)
                self.controls["port"].setDisabled(False)
                self.controls["user"].setDisabled(False)
                self.controls["password"].setDisabled(False)
                self.controls["cnlpf"].setDisabled(False)
                self.controls["cnlpf"].setChecked(False)
        
        def getData(self):
            d = {}
            d["id"]           = str(self.id)
            d["default"]      = bool(self.default)
            d["name"]         = unicode(self.controls["name"].text())
            if self.controls["typeLocal"].isChecked():
                d["type"]     = str("local")
            elif self.controls["typeInternal"].isChecked():
                d["type"]     = str("internal")
            else:
                d["type"]     = str("remote")
            d["host"]         = unicode(self.controls["host"].text())
            d["port"]         = int(self.controls["port"].value())
            d["user"]         = unicode(self.controls["user"].text())
            d["password"]     = unicode(self.controls["password"].text())
            d["cnlpf"]        = bool(self.controls["cnlpf"].isChecked())
            d["cnlpfPort"]    = int(self.controls["cnlpfPort"].value())
            d["cnlpfGetPort"] = bool(self.controls["cnlpfGetPort"].isChecked())
            return d
        
        def slotDone(self):
            data = self.getData()
            self.hide()
            self.emit(SIGNAL("save"), data)

