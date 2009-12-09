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

from time import sleep

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from xmlrpclib import ServerProxy

class main(QObject):
    def __init__(self):
        """
            main setup
        """
        QObject.__init__(self)
        self.app = QApplication(sys.argv)
        self.mainWindow = mainWindow()
        self.connector = connector()
        
        self.connector.start()
        self.mainWindow.show()
        self.testStuff()
    
    def connectSignals(self):
        """
            signal and slot stuff, yay!
        """
        self.connect(self.connector, SIGNAL("error_box"), self.slotErrorBox)
    
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

class connector(QThread):
    def __init__(self):
        """
            init thread
        """
        QThread.__init__(self)
        self.lock = QMutex()
        self.running = True
        self.proxy = None
    
    def run(self):
        """
            start thread
            (called from thread.start())
        """
        self.connectProxy("http://admin:pwhere@localhost:7227/")    #@TODO: change me!
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
        return self.proxy.get_collector_files()
    
    def getPackageCollector(self):
        """
            grab packages from collector and return the data
        """
        return self.proxy.get_collector_packages()
    
    def getLinkInfo(self, id):
        """
            grab file info for the given id and return it
        """
        return self.proxy.get_file_info(id)
    
    def getPackageInfo(self, id):
        """
            grab package info for the given id and return it
        """
        return self.proxy.get_package_data(id)
    
    def getPackageQueue(self):
        """
            grab queue return the data
        """
        return self.proxy.get_queue()
    
    def getPackageFiles(self, id):
        """
            grab package files and return ids
        """
        return self.proxy.get_package_files(id)

class mainWindow(QMainWindow):
    def __init__(self):
        """
            set up main window
        """
        QMainWindow.__init__(self)
        #window stuff
        self.setWindowTitle("pyLoad Client")
        self.setWindowIcon(QIcon("icons/logo.png"))
        self.resize(600,500)
        
        #central widget, layout
        self.masterlayout = QVBoxLayout()
        lw = QWidget()
        lw.setLayout(self.masterlayout)
        self.setCentralWidget(lw)
        
        #set menubar and statusbar
        self.menubar = self.menuBar()
        self.statusbar = self.statusBar()
        
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
        self.tabs["queue"]["treewidget"] = QTreeWidget()
        self.tabs["queue"]["l"].addWidget(self.tabs["queue"]["treewidget"])
        self.tabs["queue"]["treewidget"].setColumnCount(2)
        self.tabs["queue"]["treewidget"].setHeaderLabels(["Name", "Status"])
        
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

class QueueFile():
    def __init__(self, data, pack):
        self.pack = pack
        self.update(data)
    
    def update(self, data):
        self.data = data
    
    def getID(self):
        return self.data.id

class QueuePack():
    def __init__(self, data):
        self.data = {}
        self.children = []
        self.update(data)
    
    def update(self, data):
        self.data = data
    
    def addChild(self, NewQFile):
        for QFile in self.children:
            if QFile.getID() == NewQFile.getID():
                QFile.update(NewQFile.data)
                return
        self.children.append(QFile)
    
    def getChildren(self):
        return self.children
    
    def getID(self):
        return self.data["id"]

class QueueIndex(QModelIndex):
    def __init__(self):
        QModelIndex.__init__(self, model)
        self.model = model
        self.row = None
        self.col = None
        self.type = None
        self.id = None
    
    def isValid(self, checkID=True):
        if self.col >= self.model.columnCount():
            #column not exists
            return False
        if self.type == "pack":
            #index points to a package
            pos = self.model._inQueue(self.id)
            if pos == self.row:
                #row match
                if checkID and self.model.queue[pos].getID() != self.id:
                    #should I check the id? if yes, is it wrong?
                    return False
                #id okay or check off
                return True
        elif self.type == "file":
            #index points to a file
            for pack in self.model.queue:
                #all packs
                for k, child in enumerate(pack.getChildren()):
                    #all children
                    if k == self.row:
                        #row match
                        if checkID and child.getID() != self.id:
                            #should I check the id? if yes, is it wrong?
                            return False
                        #id okay or check off
                        return True
        #row invalid or type not matched
        return False

class QueueModel(QAbstractItemModel):
    def __init__(self, connector):
        self.connector = connector
        self.queue = []
        self.cols = 3
        self._update()
    
    def _update(self):
        packs = self.connector.getPackageQueue()
        previous = None
        for data in packs:
            pos = self._inQueue(data["id"])
            if pos != False:
                pack = self.queue[pos]
                pack.update(data)
            else:
                pack = QueuePack(data)
            files = self.connector.getPackageFiles(data["id"])
            for id in files:
                info = self.connector.getLinkInfo(id)
                qFile = QueueFile(info, pack)
                pack.addChild(qFile)
            if pos == False:
                tmpID = None
                if previous != None:
                    tmpID = previous.getID()
                self._insertPack(self, pack, tmpID)
            previous = pack
    
    def _inQueue(self, pid):
        for k, pack in enumerate(self.queue):
            if pack.getID() == pid:
                return k
        return False
    
    def _insertPack(self, pack, prevID):
        for k, pack in enumerate(self.queue):
            if pack.getID() == pid:
                break
        self.queue.insert(k+1, pack)
    
    def index(self, row, column, parent=QModelIndex()):
        if parent == QModelIndex():
            #create from root
            index = QueueIndex(self)
            index.row, index.col, index.type = row, col, "pack"
            if index.isValid(checkID=False):
                #row and column okay
                index.id = self.queue[row].getID()
        elif parent.isValid():
            #package or file
            index = QueueIndex(self)
            index.row, index.col, index.type = row, col, "file"
            if index.isValid(checkID=False):
                #row and column okay
                for pack in self.queue:
                    if pack.getID() == parent.id:
                        #it is our pack
                        #now grab the id of the file
                        index.id = pack.getChildren()[row].getID()
    
    def parent(self, index):
        if index.type == "pack":
            return QModelIndex()
        if index.isValid():
            index = QueueIndex(self)
            index.col, index.type = 0, "pack"
            for k, pack in enumerate(self.queue):
                if pack.getChildren()[index.row].getID() == index.id:
                    index.row, index.id = k, pack.getID()
                    if index.isValid():
                        return index
                    else:
                        break
    
    def rowCount(self, parent=QModelIndex()):
        if parent == QModelIndex():
            #return package count
            return len(self.queue)
        else:
            if parent.isVaild():
                #index is valid
                if parent.type == "pack":
                    #index points to a package
                    #return len of children
                    return len(self.queue[parent.row].getChildren())
            else:
                #index is invalid
                return False
        #files have no children
        return None
    
    def columnCount(self, parent=QModelIndex()):
        return self.cols
    
    def data(self, index, role=Qt.DisplayRole):
        if not parent.isValid() or parent.col != 0:
            return QVariant()
        if role == Qt.DisplayRole:
            if parent.type == "pack":
                return QVariant(self.queue[parent.row].data["package_name"])
            else:
                #TODO: return something!
                return QVariant()
        else:
            return QVariant()
    
    def fetchMore(self, parent):
        pass
    
    def canFetchMore(self, parent):
        return True

if __name__ == "__main__":
    app = main()
    app.loop()
