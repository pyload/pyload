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

from os.path import join

from uuid import uuid4 as uuid

class ConnectionManager(QWidget):


    warningShown = False

    def __init__(self):
        QWidget.__init__(self)

        if not self.warningShown:
            QMessageBox.warning(self, 'Warning',
            "We are sorry but the GUI is not stable yet. Please use the webinterface for much better experience. \n", QMessageBox.Ok)
            ConnectionManager.warningShown = True

        mainLayout = QHBoxLayout()
        buttonLayout = QVBoxLayout()

        self.setWindowTitle(_("pyLoad ConnectionManager"))
        self.setWindowIcon(QIcon(join(pypath, "icons","logo.png")))

        connList = QListWidget()
        
        new = QPushButton(_("New"))
        edit = QPushButton(_("Edit"))
        remove = QPushButton(_("Remove"))
        connect = QPushButton(_("Connect"))

        #box = QFrame()
        boxLayout = QVBoxLayout()
        #box.setLayout(boxLayout)

        boxLayout.addWidget(QLabel(_("Connect:")))
        boxLayout.addWidget(connList)

        line = QFrame()
        #line.setFixedWidth(100)
        line.setFrameShape(line.HLine)
        line.setFrameShadow(line.Sunken)
        line.setFixedHeight(10)

        boxLayout.addWidget(line)

        form = QFormLayout()
        form.setMargin(5)
        form.setSpacing(20)

        form.setAlignment(Qt.AlignRight)
        checkbox = QCheckBox()
        form.addRow(_("Use internal Core:"), checkbox)

        boxLayout.addLayout(form)

        mainLayout.addLayout(boxLayout)
        mainLayout.addLayout(buttonLayout)
        
        buttonLayout.addWidget(new)
        buttonLayout.addWidget(edit)
        buttonLayout.addWidget(remove)
        buttonLayout.addStretch()
        buttonLayout.addWidget(connect)
        
        self.setLayout(mainLayout)

        self.internal = checkbox
        self.new = new
        self.connectb = connect
        self.remove = remove
        self.editb = edit
        self.connList = connList
        self.edit = self.EditWindow()
        self.connectSignals()
        
        self.defaultStates = {}
    
    def connectSignals(self):
        self.connect(self, SIGNAL("setConnections"), self.setConnections)
        self.connect(self.new, SIGNAL("clicked()"), self.slotNew)
        self.connect(self.editb, SIGNAL("clicked()"), self.slotEdit)
        self.connect(self.remove, SIGNAL("clicked()"), self.slotRemove)
        self.connect(self.connectb, SIGNAL("clicked()"), self.slotConnect)
        self.connect(self.edit, SIGNAL("save"), self.slotSave)
        self.connect(self.connList, SIGNAL("itemDoubleClicked(QListWidgetItem *)"), self.slotItemDoubleClicked)
        self.connect(self.internal, SIGNAL("clicked()"), self.slotInternal)
    
    def setConnections(self, connections):
        self.connList.clear()
        for conn in connections:
            item = QListWidgetItem()
            item.setData(Qt.DisplayRole, QVariant(conn["name"]))
            item.setData(Qt.UserRole, QVariant(conn))
            self.connList.addItem(item)
            if conn["default"]:
                item.setData(Qt.DisplayRole, QVariant(_("%s (Default)") % conn["name"]))
                self.connList.setCurrentItem(item)
    
    def slotNew(self):
        data = {"id":uuid().hex, "type":"remote", "default":False, "name":"", "host":"", "port":"7228", "user":"admin", "password":""}
        self.edit.setData(data)
        self.edit.show()
    
    def slotEdit(self):
        item = self.connList.currentItem()
        data = item.data(Qt.UserRole).toPyObject()
        data = self.cleanDict(data)
        self.edit.setData(data)
        self.edit.show()
    
    def slotRemove(self):
        item = self.connList.currentItem()
        data = item.data(Qt.UserRole).toPyObject()
        data = self.cleanDict(data)
        self.emit(SIGNAL("removeConnection"), data)
    
    def slotConnect(self):
        if self.internal.checkState() == 2:
            data = {"type": "internal"}
            self.emit(SIGNAL("connect"), data)
        else:
            item = self.connList.currentItem()
            data = item.data(Qt.UserRole).toPyObject()
            data = self.cleanDict(data)
            self.emit(SIGNAL("connect"), data)
    
    def cleanDict(self, data):
        tmp = {}
        for k, d in data.items():
            tmp[str(k)] = d
        return tmp
    
    def slotSave(self, data):
        self.emit(SIGNAL("saveConnection"), data)
        
    def slotItemDoubleClicked(self, defaultItem):
        data = defaultItem.data(Qt.UserRole).toPyObject()
        self.setDefault(data, True)
        did = self.cleanDict(data)["id"]
        #allItems = self.connList.findItems("*", Qt.MatchWildcard)
        count = self.connList.count()
        for i in range(count):
            item = self.connList.item(i)
            data = item.data(Qt.UserRole).toPyObject()
            if self.cleanDict(data)["id"] == did:
                continue
            self.setDefault(data, False)

    def slotInternal(self):
        if self.internal.checkState() == 2:
            self.connList.clearSelection()
    
    def setDefault(self, data, state):
        data = self.cleanDict(data)
        self.edit.setData(data)
        data = self.edit.getData()
        data["default"] = state
        self.edit.emit(SIGNAL("save"), data)
    
    class EditWindow(QWidget):
        def __init__(self):
            QWidget.__init__(self)

            self.setWindowTitle(_("pyLoad ConnectionManager"))
            self.setWindowIcon(QIcon(join(pypath, "icons","logo.png")))
            
            grid = QGridLayout()
            
            nameLabel = QLabel(_("Name:"))
            hostLabel = QLabel(_("Host:"))
            localLabel = QLabel(_("Local:"))
            userLabel = QLabel(_("User:"))
            pwLabel = QLabel(_("Password:"))
            portLabel = QLabel(_("Port:"))
            
            name = QLineEdit()
            host = QLineEdit()
            local = QCheckBox()
            user = QLineEdit()
            password = QLineEdit()
            password.setEchoMode(QLineEdit.Password)
            port = QSpinBox()
            port.setRange(1,10000)
            
            save = QPushButton(_("Save"))
            cancel = QPushButton(_("Cancel"))
            
            grid.addWidget(nameLabel,  0, 0)
            grid.addWidget(name,       0, 1)
            grid.addWidget(localLabel, 1, 0)
            grid.addWidget(local,      1, 1)
            grid.addWidget(hostLabel,  2, 0)
            grid.addWidget(host,       2, 1)
            grid.addWidget(portLabel,  3, 0)
            grid.addWidget(port,       3, 1)
            grid.addWidget(userLabel,  4, 0)
            grid.addWidget(user,       4, 1)
            grid.addWidget(pwLabel,    5, 0)
            grid.addWidget(password,   5, 1)
            grid.addWidget(cancel,     6, 0)
            grid.addWidget(save,       6, 1)
            
            self.setLayout(grid)
            self.controls = {"name": name,
                             "host": host,
                             "local": local,
                             "user": user,
                             "password": password,
                             "port": port,
                             "save": save,
                             "cancel": cancel}

            self.connect(cancel, SIGNAL("clicked()"), self.hide)
            self.connect(save, SIGNAL("clicked()"), self.slotDone)
            self.connect(local, SIGNAL("stateChanged(int)"), self.slotLocalChanged)
            
            self.id = None
            self.default = None
        
        def setData(self, data):
            if not data: return
            
            self.id = data["id"]
            self.default = data["default"]
            self.controls["name"].setText(data["name"])
            if data["type"] == "local":
                data["local"] = True
            else:
                data["local"] = False
            self.controls["local"].setChecked(data["local"])
            if not data["local"]:
                self.controls["user"].setText(data["user"])
                self.controls["password"].setText(data["password"])
                self.controls["port"].setValue(int(data["port"]))
                self.controls["host"].setText(data["host"])
                self.controls["user"].setDisabled(False)
                self.controls["password"].setDisabled(False)
                self.controls["port"].setDisabled(False)
                self.controls["host"].setDisabled(False)
            else:
                self.controls["user"].setText("")
                self.controls["port"].setValue(1)
                self.controls["host"].setText("")
                self.controls["user"].setDisabled(True)
                self.controls["password"].setDisabled(True)
                self.controls["port"].setDisabled(True)
                self.controls["host"].setDisabled(True)
        
        def slotLocalChanged(self, val):
            if val == 2:
                self.controls["user"].setDisabled(True)
                self.controls["password"].setDisabled(True)
                self.controls["port"].setDisabled(True)
                self.controls["host"].setDisabled(True)
            elif val == 0:
                self.controls["user"].setDisabled(False)
                self.controls["password"].setDisabled(False)
                self.controls["port"].setDisabled(False)
                self.controls["host"].setDisabled(False)
        
        def getData(self):
            d = {}
            d["id"] = self.id
            d["default"] = self.default
            d["name"] = self.controls["name"].text()
            d["local"] = self.controls["local"].isChecked()
            d["user"] = self.controls["user"].text()
            d["password"] = self.controls["password"].text()
            d["host"] = self.controls["host"].text()
            d["port"] = self.controls["port"].value()
            if d["local"]:
                d["type"] = "local"
            else:
                d["type"] = "remote"
            return d
        
        def slotDone(self):
            data = self.getData()
            self.hide()
            self.emit(SIGNAL("save"), data)

