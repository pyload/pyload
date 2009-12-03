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
            self.mainWindow.tabs["collector_packages"]["treewidget"].addTopLevelItem(item)
        
        #test for queue
        packs = self.connector.getPackageQueue()
        for data in packs:
            item = QTreeWidgetItem()
            item.setData(0, Qt.UserRole, QVariant(data))
            item.setData(0, Qt.DisplayRole, QVariant(data["package_name"]))
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
        self.tabw.addTab(self.tabs["collector_packages"]["w"], "Link collector")
        self.tabw.addTab(self.tabs["collector_links"]["w"], "Package collector")
        
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

if __name__ == "__main__":
    app = main()
    app.loop()
