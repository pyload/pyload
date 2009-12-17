#!/usr/bin/env python
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
    @version: v0.3
"""

SERVER_VERSION = "0.3"

import sys
import os

from time import sleep, time

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.QtXml import *

from xmlrpclib import ServerProxy

from uuid import uuid4 as uuid

class main(QObject):
    def __init__(self):
        """
            main setup
        """
        QObject.__init__(self)
        self.app = QApplication(sys.argv)
        self.mainWindow = mainWindow()
        self.pwWindow = PWInputWindow()
        self.connWindow = ConnectionManager()
        self.connector = connector()
        self.mainloop = self.Loop(self)
        self.connectSignals()
        self.parser = XMLParser("guiconfig.xml", "guiconfig_default.xml")
        
        self.refreshConnections()
        self.connData = None
        self.connWindow.show()
    
    def startMain(self):
        self.connector.start()
        sleep(1)
        self.mainWindow.show()
        self.testStuff()
        self.mainloop.start()
    
    def connectSignals(self):
        """
            signal and slot stuff, yay!
        """
        self.connect(self.connector, SIGNAL("error_box"), self.slotErrorBox)
        self.connect(self.connWindow, SIGNAL("saveConnection"), self.slotSaveConnection)
        self.connect(self.connWindow, SIGNAL("removeConnection"), self.slotRemoveConnection)
        self.connect(self.connWindow, SIGNAL("connect"), self.slotConnect)
        self.connect(self.pwWindow, SIGNAL("ok"), self.slotPasswordTyped)
        self.connect(self.pwWindow, SIGNAL("cancel"), self.quit)
    
    def quit(self):
        self.app.quit()
    
    def loop(self):
        """
            start exec loop
        """
        sys.exit(self.app.exec_())
    
    def slotErrorBox(self, msg):
        """
            display a nice error box
        """
        QMessageBox(QMessageBox.Warning, "Error", msg)
    
    def testStuff(self):
        """
            only for testing ;)
        """
        #test for link collector
        ids = self.connector.getLinkCollector()
        for id in ids:
            data = self.connector.getLinkInfo(id)
            item = QListWidgetItem()
            item.setData(Qt.UserRole, QVariant(data))
            item.setData(Qt.DisplayRole, QVariant(data["url"]))
            self.mainWindow.tabs["collector_links"]["listwidget"].addItem(item)
        
        #test for package collector
        packs = self.connector.getPackageCollector()
        for data in packs:
            item = QTreeWidgetItem()
            item.setData(0, Qt.UserRole, QVariant(data))
            item.setData(0, Qt.DisplayRole, QVariant(data["package_name"]))
            files = self.connector.getPackageFiles(data["id"])
            for id in files:
                info = self.connector.getLinkInfo(id)
                sub = QTreeWidgetItem(item)
                sub.setData(0, Qt.DisplayRole, QVariant(info["filename"]))
            self.mainWindow.tabs["collector_packages"]["treewidget"].addTopLevelItem(item)
        
        #test for queue
        """
        packs = self.connector.getPackageQueue()
        for data in packs:
            item = QTreeWidgetItem()
            item.setData(0, Qt.UserRole, QVariant(data))
            item.setData(0, Qt.DisplayRole, QVariant(data["package_name"]))
            files = self.connector.getPackageFiles(data["id"])
            for id in files:
                info = self.connector.getLinkInfo(id)
                sub = QTreeWidgetItem(item)
                sub.setData(0, Qt.DisplayRole, QVariant(info["filename"]))
                sub.setData(1, Qt.DisplayRole, QVariant(info["status_type"]))
            self.mainWindow.tabs["queue"]["treewidget"].addTopLevelItem(item)
            
        model = QueueModel(self.connector)
        model.setView(self.mainWindow.tabs["queue"]["view"])
        self.mainWindow.tabs["queue"]["view"].setModel(model)
        self.mainWindow.tabs["queue"]["view"].setup()
        model.startLoop()
        """
        view = self.mainWindow.tabs["queue"]["view"]
        view.setColumnCount(3)
        view.setHeaderLabels(["Name", "Status", "Fortschritt"])
        view.setColumnWidth(0, 300)
        view.setColumnWidth(1, 200)
        view.setColumnWidth(2, 100)
        self.queue = Queue(view, self.connector)
        delegate = QueueProgressBarDelegate(view, self.queue)
        view.setItemDelegateForColumn(2, delegate)
        #view.setup(self.queue)
        self.queue.start()
    
    def refreshServerStatus(self):
        status = self.connector.getServerStatus()
        if status["pause"]:
            status["status"] = "Paused"
        else:
            status["status"] = "Running"
        status["speed"] = int(status["speed"])
        text = "Status: %(status)s | Speed: %(speed)s kb/s" % status
        self.mainWindow.serverStatus.setText(text)
    
    def getConnections(self):
        connectionsNode = self.parser.xml.elementsByTagName("connections").item(0)
        if connectionsNode.isNull():
            raise Exception("null")
        connections = self.parser.parseNode(connectionsNode)
        ret = []
        for conn in connections:
            data = {}
            data["type"] = conn.attribute("type", "remote")
            data["default"] = conn.attribute("default", "False")
            data["id"] = conn.attribute("id", uuid().hex)
            if data["default"] == "True":
                data["default"] = True
            else:
                data["default"] = False
            subs = self.parser.parseNode(conn, "dict")
            if not subs.has_key("name"):
                data["name"] = "Unnamed"
            else:
                data["name"] = subs["name"].text()
            if data["type"] == "remote":
                if not subs.has_key("server"):
                    continue
                else:
                    data["host"] = subs["server"].text()
                    data["ssl"] = subs["server"].attribute("ssl", "False")
                    if data["ssl"] == "True":
                        data["ssl"] = True
                    else:
                        data["ssl"] = False
                    data["user"] = subs["server"].attribute("user", "admin")
                    data["port"] = int(subs["server"].attribute("port", "7227"))
            ret.append(data)
        return ret
    
    def slotSaveConnection(self, data):
        connectionsNode = self.parser.xml.elementsByTagName("connections").item(0)
        if connectionsNode.isNull():
            raise Exception("null")
        connections = self.parser.parseNode(connectionsNode)
        connNode = self.parser.xml.createElement("connection")
        connNode.setAttribute("default", data["default"])
        connNode.setAttribute("type", data["type"])
        connNode.setAttribute("id", data["id"])
        nameNode = self.parser.xml.createElement("name")
        nameText = self.parser.xml.createTextNode(data["name"])
        nameNode.appendChild(nameText)
        connNode.appendChild(nameNode)
        if data["type"] == "remote":
            serverNode = self.parser.xml.createElement("server")
            serverNode.setAttribute("ssl", data["ssl"])
            serverNode.setAttribute("user", data["user"])
            serverNode.setAttribute("port", data["port"])
            hostText = self.parser.xml.createTextNode(data["host"])
            serverNode.appendChild(hostText)
            connNode.appendChild(serverNode)
        found = False
        for c in connections:
            cid = c.attribute("id", "None")
            if str(cid) == str(data["id"]):
                found = c
                break
        if found:
            connectionsNode.replaceChild(connNode, found)
        else:
            connectionsNode.appendChild(connNode)
        self.parser.saveData()
        self.refreshConnections()
    
    def slotRemoveConnection(self, data):
        connectionsNode = self.parser.xml.elementsByTagName("connections").item(0)
        if connectionsNode.isNull():
            raise Exception("null")
        connections = self.parser.parseNode(connectionsNode)
        found = False
        for c in connections:
            cid = c.attribute("id", "None")
            if str(cid) == str(data["id"]):
                found = c
                break
        if found:
            connectionsNode.removeChild(found)
        self.parser.saveData()
        self.refreshConnections()
    
    def slotConnect(self, data):
        self.connWindow.hide()
        self.connData = data
        if data["type"] == "local":
            self.slotPasswordTyped("")
        self.pwWindow.show()
    
    def slotPasswordTyped(self, pw):
        data = self.connData
        data["password"] = pw
        if data["type"] == "remote":
            if data["ssl"]:
                data["ssl"] = "s"
            else:
                data["ssl"] = ""
            server_url = "http%(ssl)s://%(user)s:%(password)s@%(host)s:%(port)s/" % data
            self.connector.setAddr(server_url)
            self.startMain()
        else:
            print "comming soon ;)"
            self.quit()
    
    def refreshConnections(self):
        self.parser.loadData()
        conns = self.getConnections()
        self.connWindow.emit(SIGNAL("setConnections(connections)"), conns)
    
    class Loop(QThread):
        def __init__(self, parent):
            QThread.__init__(self)
            self.parent = parent
            self.running = True
        
        def run(self):
            while self.running:
                sleep(1)
                self.update()
        
        def update(self):
            self.parent.refreshServerStatus()

#############################################
############## Connector Stuff ##############
#############################################

class connector(QThread):
    def __init__(self):
        """
            init thread
        """
        QThread.__init__(self)
        self.mutex = QMutex()
        self.running = True
        self.proxy = None
        self.addr = None
    
    def setAddr(self, addr):
        self.mutex.lock()
        self.addr = addr
        self.mutex.unlock()
    
    def run(self):
        """
            start thread
            (called from thread.start())
        """
        self.connectProxy(self.addr)
        while self.running:
            sleep(1)
    
    def stop(self):
        """
            stop thread
        """
        self.running = False
    
    def connectProxy(self, addr):
        """
            connect to remote server
        """
        self.proxy = ServerProxy(addr, allow_none=True)
        server_version = self.proxy.get_server_version()
        if not server_version == SERVER_VERSION:
            self.emit(SIGNAL("error_box"), "server is version %s client accepts version %s" % (server_version, SERVER_VERSION))
    
    def getLinkCollector(self):
        """
            grab links from collector and return the ids
        """
        self.mutex.lock()
        try:
            return self.proxy.get_collector_files()
        finally:
            self.mutex.unlock()
    
    def getPackageCollector(self):
        """
            grab packages from collector and return the data
        """
        self.mutex.lock()
        try:
            return self.proxy.get_collector_packages()
        finally:
            self.mutex.unlock()
    
    def getLinkInfo(self, id):
        """
            grab file info for the given id and return it
        """
        self.mutex.lock()
        try:
            return self.proxy.get_file_info(id)
        finally:
            self.mutex.unlock()
    
    def getPackageInfo(self, id):
        """
            grab package info for the given id and return it
        """
        self.mutex.lock()
        try:
            return self.proxy.get_package_data(id)
        finally:
            self.mutex.unlock()
    
    def getPackageQueue(self):
        """
            grab queue return the data
        """
        self.mutex.lock()
        try:
            return self.proxy.get_queue()
        finally:
            self.mutex.unlock()
    
    def getPackageFiles(self, id):
        """
            grab package files and return ids
        """
        self.mutex.lock()
        try:
            return self.proxy.get_package_files(id)
        finally:
            self.mutex.unlock()
    
    def getDownloadQueue(self):
        """
            grab files that are currently downloading and return info
        """
        self.mutex.lock()
        try:
            return self.proxy.status_downloads()
        finally:
            self.mutex.unlock()
    
    def getServerStatus(self):
        """
            return server status
        """
        self.mutex.lock()
        try:
            return self.proxy.status_server()
        finally:
            self.mutex.unlock()

##########################################
############## Window Stuff ##############
##########################################

class mainWindow(QMainWindow):
    def __init__(self):
        """
            set up main window
        """
        QMainWindow.__init__(self)
        #window stuff
        self.setWindowTitle("pyLoad Client")
        self.setWindowIcon(QIcon("icons/logo.png"))
        self.resize(750,500)
        
        #central widget, layout
        self.masterlayout = QVBoxLayout()
        lw = QWidget()
        lw.setLayout(self.masterlayout)
        self.setCentralWidget(lw)
        
        #set menubar and statusbar
        self.menubar = self.menuBar()
        self.statusbar = self.statusBar()
        self.serverStatus = QLabel("Status: Not Connected")
        self.statusbar.addPermanentWidget(self.serverStatus)
        
        #menu
        self.menus = {}
        self.menus["file"] = self.menubar.addMenu("&File")
        self.menus["connections"] = self.menubar.addMenu("&Connections")
        
        #menu actions
        self.mactions = {}
        self.mactions["exit"] = QAction("Exit", self.menus["file"])
        self.mactions["manager"] = QAction("Connection manager", self.menus["connections"])
        
        #add menu actions
        self.menus["file"].addAction(self.mactions["exit"])
        self.menus["connections"].addAction(self.mactions["manager"])
        
        #tabs
        self.tabw = QTabWidget()
        self.tabs = {}
        self.tabs["queue"] = {"w":QWidget()}
        self.tabs["collector_packages"] = {"w":QWidget()}
        self.tabs["collector_links"] = {"w":QWidget()}
        self.tabw.addTab(self.tabs["queue"]["w"], "Queue")
        self.tabw.addTab(self.tabs["collector_packages"]["w"], "Package collector")
        self.tabw.addTab(self.tabs["collector_links"]["w"], "Link collector")
        
        #init tabs
        self.init_tabs()
        
        #layout
        self.masterlayout.addWidget(self.tabw)
    
    def init_tabs(self):
        """
            create tabs
        """
        #queue
        self.tabs["queue"]["l"] = QGridLayout()
        self.tabs["queue"]["w"].setLayout(self.tabs["queue"]["l"])
        self.tabs["queue"]["view"] = QTreeWidget()
        self.tabs["queue"]["l"].addWidget(self.tabs["queue"]["view"])
        
        #collector_packages
        self.tabs["collector_packages"]["l"] = QGridLayout()
        self.tabs["collector_packages"]["w"].setLayout(self.tabs["collector_packages"]["l"])
        self.tabs["collector_packages"]["treewidget"] = QTreeWidget()
        self.tabs["collector_packages"]["l"].addWidget(self.tabs["collector_packages"]["treewidget"])
        
        #collector_links
        self.tabs["collector_links"]["l"] = QGridLayout()
        self.tabs["collector_links"]["w"].setLayout(self.tabs["collector_links"]["l"])
        self.tabs["collector_links"]["listwidget"] = QListWidget()
        self.tabs["collector_links"]["l"].addWidget(self.tabs["collector_links"]["listwidget"])

class ConnectionManager(QWidget):
    def __init__(self):
        QWidget.__init__(self)
        
        mainLayout = QHBoxLayout()
        buttonLayout = QVBoxLayout()
        
        connList = QListWidget()
        
        new = QPushButton("New")
        edit = QPushButton("Edit")
        remove = QPushButton("Remove")
        connect = QPushButton("Connect")
        
        mainLayout.addWidget(connList)
        mainLayout.addLayout(buttonLayout)
        
        buttonLayout.addWidget(new)
        buttonLayout.addWidget(edit)
        buttonLayout.addWidget(remove)
        buttonLayout.addStretch()
        buttonLayout.addWidget(connect)
        
        self.setLayout(mainLayout)
        
        self.new = new
        self.connectb = connect
        self.remove = remove
        self.editb = edit
        self.connList = connList
        self.edit = self.EditWindow()
        self.connectSignals()
    
    def connectSignals(self):
        self.connect(self, SIGNAL("setConnections(connections)"), self.setConnections)
        self.connect(self.new, SIGNAL("clicked()"), self.slotNew)
        self.connect(self.editb, SIGNAL("clicked()"), self.slotEdit)
        self.connect(self.remove, SIGNAL("clicked()"), self.slotRemove)
        self.connect(self.connectb, SIGNAL("clicked()"), self.slotConnect)
        self.connect(self.edit, SIGNAL("save"), self.slotSave)
    
    def setConnections(self, connections):
        self.connList.clear()
        for conn in connections:
            item = QListWidgetItem()
            item.setData(Qt.DisplayRole, QVariant(conn["name"]))
            item.setData(Qt.UserRole, QVariant(conn))
            self.connList.addItem(item)
            if conn["default"]:
                self.connList.setCurrentItem(item)
    
    def slotNew(self):
        data = {"id":uuid().hex, "type":"remote", "default":False, "name":"", "host":"", "ssl":False, "port":"7227", "user":"admin"}
        self.edit.setData(data)
        self.edit.show()
    
    def slotEdit(self):
        item = self.connList.currentItem()
        data = item.data(Qt.UserRole).toPyObject()
        tmp = {}
        for k, d in data.items():
            tmp[str(k)] = d
        data = tmp
        self.edit.setData(data)
        self.edit.show()
    
    def slotRemove(self):
        item = self.connList.currentItem()
        data = item.data(Qt.UserRole).toPyObject()
        tmp = {}
        for k, d in data.items():
            tmp[str(k)] = d
        data = tmp
        self.emit(SIGNAL("removeConnection"), data)
    
    def slotConnect(self):
        item = self.connList.currentItem()
        data = item.data(Qt.UserRole).toPyObject()
        tmp = {}
        for k, d in data.items():
            tmp[str(k)] = d
        data = tmp
        self.emit(SIGNAL("connect"), data)
    
    def slotSave(self, data):
        self.emit(SIGNAL("saveConnection"), data)
        
    class EditWindow(QWidget):
        def __init__(self):
            QWidget.__init__(self)
            
            grid = QGridLayout()
            
            nameLabel = QLabel("Name:")
            hostLabel = QLabel("Host:")
            sslLabel = QLabel("SSL:")
            localLabel = QLabel("Local:")
            userLabel = QLabel("User:")
            portLabel = QLabel("Port:")
            
            name = QLineEdit()
            host = QLineEdit()
            ssl = QCheckBox()
            local = QCheckBox()
            user = QLineEdit()
            port = QSpinBox()
            port.setRange(1,10000)
            
            save = QPushButton("Save")
            cancel = QPushButton("Cancel")
            
            grid.addWidget(nameLabel,  0, 0)
            grid.addWidget(name,       0, 1)
            grid.addWidget(localLabel, 1, 0)
            grid.addWidget(local,      1, 1)
            grid.addWidget(hostLabel,  2, 0)
            grid.addWidget(host,       2, 1)
            grid.addWidget(sslLabel,   4, 0)
            grid.addWidget(ssl,        4, 1)
            grid.addWidget(userLabel,  5, 0)
            grid.addWidget(user,       5, 1)
            grid.addWidget(portLabel,  3, 0)
            grid.addWidget(port,       3, 1)
            grid.addWidget(cancel,     6, 0)
            grid.addWidget(save,       6, 1)
            
            self.setLayout(grid)
            self.controls = {}
            self.controls["name"] = name
            self.controls["host"] = host
            self.controls["ssl"] = ssl
            self.controls["local"] = local
            self.controls["user"] = user
            self.controls["port"] = port
            self.controls["save"] = save
            self.controls["cancel"] = cancel
            
            self.connect(cancel, SIGNAL("clicked()"), self.hide)
            self.connect(save, SIGNAL("clicked()"), self.slotDone)
            self.connect(local, SIGNAL("stateChanged(int)"), self.slotLocalChanged)
            
            self.id = None
            self.default = None
        
        def setData(self, data):
            self.id = data["id"]
            self.default = data["default"]
            self.controls["name"].setText(data["name"])
            if data["type"] == "local":
                data["local"] = True
            else:
                data["local"] = False
            self.controls["local"].setChecked(data["local"])
            if not data["local"]:
                self.controls["ssl"].setChecked(data["ssl"])
                self.controls["user"].setText(data["user"])
                self.controls["port"].setValue(int(data["port"]))
                self.controls["host"].setText(data["host"])
                self.controls["ssl"].setDisabled(False)
                self.controls["user"].setDisabled(False)
                self.controls["port"].setDisabled(False)
                self.controls["host"].setDisabled(False)
            else:
                self.controls["ssl"].setChecked(False)
                self.controls["user"].setText("")
                self.controls["port"].setValue(1)
                self.controls["host"].setText("")
                self.controls["ssl"].setDisabled(True)
                self.controls["user"].setDisabled(True)
                self.controls["port"].setDisabled(True)
                self.controls["host"].setDisabled(True)
        
        def slotLocalChanged(self, val):
            if val == 2:
                self.controls["ssl"].setDisabled(True)
                self.controls["user"].setDisabled(True)
                self.controls["port"].setDisabled(True)
                self.controls["host"].setDisabled(True)
            elif val == 0:
                self.controls["ssl"].setDisabled(False)
                self.controls["user"].setDisabled(False)
                self.controls["port"].setDisabled(False)
                self.controls["host"].setDisabled(False)
        
        def getData(self):
            d = {}
            d["id"] = self.id
            d["default"] = self.default
            d["name"] = self.controls["name"].text()
            d["local"] = self.controls["local"].isChecked()
            d["ssl"] = str(self.controls["ssl"].isChecked())
            d["user"] = self.controls["user"].text()
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

class PWInputWindow(QWidget):
    def __init__(self):
        QWidget.__init__(self)
        self.input = QLineEdit()
        label = QLabel("Password:")
        ok = QPushButton("OK")
        cancel = QPushButton("Cancel")
        grid = QGridLayout()
        grid.addWidget(label, 0, 0, 1, 2)
        grid.addWidget(self.input, 1, 0, 1, 2)
        grid.addWidget(cancel, 2, 0)
        grid.addWidget(ok, 2, 1)
        self.setLayout(grid)
        
        self.connect(ok, SIGNAL("clicked()"), self.slotOK)
        self.connect(cancel, SIGNAL("clicked()"), self.slotCancel)
        self.connect(self.input, SIGNAL("returnPressed()"), self.slotOK)
    
    def slotOK(self):
        self.hide()
        self.emit(SIGNAL("ok"), self.input.text())
    
    def slotCancel(self):
        self.hide()
        self.emit(SIGNAL("cancel"))
        
#########################################
############## Queue Stuff ##############
#########################################

class Queue(QThread):
    def __init__(self, view, connector):
        QThread.__init__(self)
        self.view = view
        self.connector = connector
        self.statusMap = {
            "finished":    0,
            "checking":    1,
            "waiting":     2,
            "reconnected": 3,
            "downloading": 4,
            "failed":      5,
            "aborted":     6,
        }
        self.statusMapReverse = dict((v,k) for k, v in self.statusMap.iteritems())
        self.queue = []
        self.interval = 2
        self.running = True
        self.mutex = QMutex()
    
    def run(self):
        while self.running:
            self.update()
            sleep(self.interval)
    
    def update(self):
        locker = QMutexLocker(self.mutex)
        packs = self.connector.getPackageQueue()
        downloading_raw = self.connector.getDownloadQueue()
        downloading = {}
        for d in downloading:
            did = d["id"]
            del d["id"]
            del d["name"]
            del d["status"]
            downloading[did] = d
        for data in packs:
            pack = self.getPack(data["id"])
            if not pack:
                pack = self.QueuePack(self)
            pack.setData(data)
            self.addPack(data["id"], pack)
            files = self.connector.getPackageFiles(data["id"])
            for fid in files:
                info = self.connector.getLinkInfo(fid)
                child = pack.getChild(fid)
                if not child:
                    child = self.QueueFile(self, pack)
                try:
                    info["downloading"] = downloading[data["id"]]
                except:
                    info["downloading"] = None
                child.setData(info)
                pack.addChild(fid, child)
    
    def addPack(self, pid, newPack):
        pos = None
        try:
            for k, pack in enumerate(self.queue):
                if pack.getData()["id"] == pid:
                    pos = k
                    break
            if pos == None:
                raise Exception()
            self.queue[pos] = newPack
        except:
            self.queue.append(newPack)
            pos = self.queue.index(newPack)
        item = self.view.topLevelItem(pos)
        if not item:
            item = QTreeWidgetItem()
            self.view.insertTopLevelItem(pos, item)
        item.setData(0, Qt.DisplayRole, QVariant(newPack.getData()["package_name"]))
        status = -1
        for child in newPack.getChildren():
            if self.statusMap.has_key(child.data["status_type"]) and self.statusMap[child.data["status_type"]] > status:
                status = self.statusMap[child.data["status_type"]]
        if status >= 0:
            item.setData(1, Qt.DisplayRole, QVariant(self.statusMapReverse[status]))
        item.setData(0, Qt.UserRole, QVariant(pid))
        item.setData(2, Qt.UserRole, QVariant(newPack))
    
    def getPack(self, pid):
        for k, pack in enumerate(self.queue):
            if pack.getData()["id"] == pid:
                return pack
        return None
    
    def getProgress(self, q):
        locker = QMutexLocker(self.mutex)
        if isinstance(q, self.QueueFile):
            data = q.getData()
            if data["downloading"]:
                return int(data["downloading"]["percent"])
            if data["status_type"] == "finished" or \
                  data["status_type"] == "failed" or \
                  data["status_type"] == "aborted":
                return 100
        elif isinstance(q, self.QueuePack):
            children = q.getChildren()
            count = len(children)
            perc_sum = 0
            for child in children:
                val = 0
                data = child.getData()
                if data["downloading"]:
                    val = int(data["downloading"]["percent"])
                elif child.data["status_type"] == "finished" or \
                        child.data["status_type"] == "failed" or \
                        child.data["status_type"] == "aborted":
                    val = 100
                perc_sum += val
            if count == 0:
                return 0
            return perc_sum/count
        return 0
    
    def getSpeed(self, q):
        locker = QMutexLocker(self.mutex)
        if isinstance(q, self.QueueFile):
            data = q.getData()
            if data["downloading"]:
                return int(data["downloading"]["speed"])
        elif isinstance(q, self.QueuePack):
            children = q.getChildren()
            count = len(children)
            speed_sum = 0
            for child in children:
                val = 0
                data = child.getData()
                running = False
                if data["downloading"]:
                    val = int(data["downloading"]["speed"])
                    running = True
                speed_sum += val
            if count == 0 or not running:
                return None
            return speed_sum
        return None
    
    class QueuePack():
        def __init__(self, queue):
            self.queue = queue
            self.data = []
            self.children = []
        
        def addChild(self, cid, newChild):
            pos = None
            try:
                for k, child in enumerate(self.getChildren()):
                    if child.getData()["id"] == cid:
                        pos = k
                        break
                if pos == None:
                    raise Exception()
                self.children[pos] = newChild
            except:
                self.children.append(newChild)
                pos = self.children.index(newChild)
            ppos = self.queue.queue.index(self)
            parent = self.queue.view.topLevelItem(ppos)
            item = parent.child(pos)
            if not item:
                item = QTreeWidgetItem()
                parent.insertChild(pos, item)
            status = "%s (%s)" % (newChild.getData()["status_type"], newChild.getData()["plugin"])
            item.setData(0, Qt.DisplayRole, QVariant(newChild.getData()["filename"]))
            item.setData(1, Qt.DisplayRole, QVariant(status))
            item.setData(0, Qt.UserRole, QVariant(cid))
            item.setData(2, Qt.UserRole, QVariant(newChild))
        
        def getChildren(self):
            return self.children
        
        def getChild(self, cid):
            try:
                return self.children[cid]
            except:
                return None
        
        def hasChildren(self, data):
            return (len(self.children) > 0)
        
        def setData(self, data):
            self.data = data
        
        def getData(self):
            return self.data

    class QueueFile():
        def __init__(self, queue, pack):
            self.queue = queue
            self.pack = pack
        
        def getData(self):
            return self.data
        
        def setData(self, data):
            self.data = data
        
        def getPack(self):
            return self.pack

class QueueProgressBarDelegate(QItemDelegate):
    def __init__(self, parent, queue):
        QItemDelegate.__init__(self, parent)
        self.queue = queue
    
    def paint(self, painter, option, index):
        if index.column() == 2:
            qe = index.data(Qt.UserRole).toPyObject()
            progress = self.queue.getProgress(qe)
            opts = QStyleOptionProgressBarV2()
            opts.maximum = 100
            opts.minimum = 0
            opts.progress = progress
            opts.rect = option.rect
            opts.rect.setRight(option.rect.right()-1)
            opts.rect.setHeight(option.rect.height()-1)
            opts.textVisible = True
            opts.textAlignment = Qt.AlignCenter
            speed = self.queue.getSpeed(qe)
            if speed == None:
                opts.text = QString.number(opts.progress) + "%"
            else:
                opts.text = QString("%s kb/s - %s" % (speed, opts.progress)) + "%"
            QApplication.style().drawControl(QStyle.CE_ProgressBar, opts, painter)
            return
        QItemDelegate.paint(self, painter, option, index)
        
#########################################
############## Other Stuff ##############
#########################################

class XMLParser():
    def __init__(self, data, dfile=""):
        self.mutex = QMutex()
        self.mutex.lock()
        self.xml = QDomDocument()
        self.file = data
        self.dfile = dfile
        self.mutex.unlock()
        self.loadData()
        self.root = self.xml.documentElement()
    
    def loadData(self):
        self.mutex.lock()
        f = self.file
        if not os.path.exists(f):
            f = self.dfile
        with open(f, 'r') as fh:
            content = fh.read()
        self.xml.setContent(content)
        self.mutex.unlock()
    
    def saveData(self):
        self.mutex.lock()
        content = self.xml.toString()
        with open(self.file, 'w') as fh:
            fh.write(content)
        self.mutex.unlock()
        return content
    
    def parseNode(self, node, ret_type="list"):
        if ret_type == "dict":
            childNodes = {}
        else:
            childNodes = []
        child = node.firstChild()
        while True:
            n = child.toElement()
            if n.isNull():
                break
            else:
                if ret_type == "dict":
                    childNodes[str(n.tagName())] = n
                else:
                    childNodes.append(n)
            child = child.nextSibling()
        return childNodes

if __name__ == "__main__":
    app = main()
    app.loop()
