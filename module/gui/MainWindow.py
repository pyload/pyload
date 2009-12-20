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

class MainWindow(QMainWindow):
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
        
        #toolbar
        self.actions = {}
        self.init_toolbar()
        
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
    
    def init_toolbar(self):
        self.toolbar = self.addToolBar("main")
        self.toolbar.setIconSize(QSize(40,40))
        self.actions["toggle_status"] = self.toolbar.addAction("Toggle Pause/Resume")
        pricon = QIcon()
        pricon.addFile("icons/gui/toolbar_start.png", QSize(), QIcon.Normal, QIcon.Off)
        pricon.addFile("icons/gui/toolbar_pause.png", QSize(), QIcon.Normal, QIcon.On)
        self.actions["toggle_status"].setIcon(pricon)
        self.actions["toggle_status"].setCheckable(True)
        self.actions["status_stop"] = self.toolbar.addAction(QIcon("icons/gui/toolbar_stop.png"), "Stop")
        self.toolbar.addSeparator()
        self.actions["add"] = self.toolbar.addAction(QIcon("icons/gui/toolbar_add.png"), "Add")
        #self.toolbar.addAction(QIcon("icons/gui/toolbar_remove.png"), "Remove")
        
        self.connect(self.actions["toggle_status"], SIGNAL("toggled(bool)"), self.slotToggleStatus)
        self.connect(self.actions["status_stop"], SIGNAL("triggered()"), self.slotStatusStop)
        self.connect(self.actions["add"], SIGNAL("triggered()"), self.slotAdd)
    
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
    
    def slotToggleStatus(self, status):
        print "toggle status", status
    
    def slotStatusStop(self):
        print "stop!"
    
    def slotAdd(self):
        print "add"
