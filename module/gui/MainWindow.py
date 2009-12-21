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

from module.gui.PackageDock import *
from module.gui.LinkDock import *

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
        
        #init docks
        self.newPackDock = NewPackageDock()
        self.addDockWidget(Qt.RightDockWidgetArea, self.newPackDock)
        self.newLinkDock = NewLinkDock()
        self.addDockWidget(Qt.RightDockWidgetArea, self.newLinkDock)
        self.connect(self.newLinkDock, SIGNAL("done"), self.slotAddLinks)
        
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
        self.tabs["collector"] = {"w":QWidget()}
        self.tabw.addTab(self.tabs["queue"]["w"], "Queue")
        self.tabw.addTab(self.tabs["collector"]["w"], "Collector")
        
        #init tabs
        self.init_tabs()
        
        #layout
        self.masterlayout.addWidget(self.tabw)
        
        self.connect(self.mactions["manager"], SIGNAL("triggered()"), self.slotShowConnector)
    
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
        self.addMenu = QMenu()
        packageAction = self.addMenu.addAction("Package")
        linkAction = self.addMenu.addAction("Links")
        self.connect(self.actions["add"], SIGNAL("triggered()"), self.slotAdd)
        self.connect(packageAction, SIGNAL("triggered()"), self.slotShowAddPackage)
        self.connect(linkAction, SIGNAL("triggered()"), self.slotShowAddLinks)
    
    def init_tabs(self):
        """
            create tabs
        """
        #queue
        self.tabs["queue"]["l"] = QGridLayout()
        self.tabs["queue"]["w"].setLayout(self.tabs["queue"]["l"])
        self.tabs["queue"]["view"] = QTreeWidget()
        self.tabs["queue"]["l"].addWidget(self.tabs["queue"]["view"])
        
        #collector
        groupPackage = QGroupBox("Packages")
        groupLinks = QGroupBox("Links")
        groupPackage.setLayout(QVBoxLayout())
        groupLinks.setLayout(QVBoxLayout())
        self.tabs["collector"]["l"] = QGridLayout()
        self.tabs["collector"]["w"].setLayout(self.tabs["collector"]["l"])
        self.tabs["collector"]["package_view"] = QTreeWidget()
        self.tabs["collector"]["link_view"] = QTreeWidget()
        groupPackage.layout().addWidget(self.tabs["collector"]["package_view"])
        groupLinks.layout().addWidget(self.tabs["collector"]["link_view"])
        self.tabs["collector"]["l"].addWidget(groupPackage, 0, 0)
        self.tabs["collector"]["l"].addWidget(groupLinks, 0, 1)
    
    def slotToggleStatus(self, status):
        print "toggle status", status
    
    def slotStatusStop(self):
        print "stop!"
    
    def slotAdd(self):
        self.addMenu.exec_(QCursor.pos())
    
    def slotShowAddPackage(self):
        self.tabw.setCurrentIndex(1)
        self.newPackDock.show()
    
    def slotShowAddLinks(self):
        self.tabw.setCurrentIndex(1)
        self.newLinkDock.show()
    
    def slotShowConnector(self):
        self.emit(SIGNAL("connector"))
    
    def slotAddLinks(self, links):
        self.emit(SIGNAL("addLinks"), links)
