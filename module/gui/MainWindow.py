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
        self.resize(850,500)
        
        #layout version
        self.version = 1
        
        #init docks
        self.newPackDock = NewPackageDock()
        self.addDockWidget(Qt.RightDockWidgetArea, self.newPackDock)
        self.newLinkDock = NewLinkDock()
        self.addDockWidget(Qt.RightDockWidgetArea, self.newLinkDock)
        self.connect(self.newLinkDock, SIGNAL("done"), self.slotAddLinks)
        self.connect(self.newPackDock, SIGNAL("done"), self.slotAddPackage)
        
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
        self.tabs["settings"] = {"w":QWidget()}
        self.tabs["log"] = {"w":QWidget()}
        self.tabw.addTab(self.tabs["queue"]["w"], "Queue")
        self.tabw.addTab(self.tabs["collector"]["w"], "Collector")
        self.tabw.addTab(self.tabs["settings"]["w"], "Settings")
        self.tabw.addTab(self.tabs["log"]["w"], "Log")
        self.tabw.setTabEnabled(2, False)
        
        #init tabs
        self.init_tabs()
        
        #context menus
        self.init_context()
        
        #layout
        self.masterlayout.addWidget(self.tabw)
        
        #signals..
        self.connect(self.mactions["manager"], SIGNAL("triggered()"), self.slotShowConnector)
        self.connect(self.mactions["exit"], SIGNAL("triggered()"), self.close)
        
        self.connect(self.tabs["queue"]["view"], SIGNAL('customContextMenuRequested(const QPoint &)'), self.slotQueueContextMenu)
        self.connect(self.tabs["collector"]["package_view"], SIGNAL('customContextMenuRequested(const QPoint &)'), self.slotPackageCollectorContextMenu)
        self.connect(self.tabs["collector"]["link_view"], SIGNAL('customContextMenuRequested(const QPoint &)'), self.slotLinkCollectorContextMenu)
    
    def init_toolbar(self):
        """
            create toolbar
        """
        self.toolbar = self.addToolBar("Main Toolbar")
        self.toolbar.setObjectName("Main Toolbar")
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
        containerAction = self.addMenu.addAction("Container")
        self.connect(self.actions["add"], SIGNAL("triggered()"), self.slotAdd)
        self.connect(packageAction, SIGNAL("triggered()"), self.slotShowAddPackage)
        self.connect(linkAction, SIGNAL("triggered()"), self.slotShowAddLinks)
        self.connect(containerAction, SIGNAL("triggered()"), self.slotShowAddContainer)
    
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
        toQueue = QPushButton("Push selected packages to queue")
        self.tabs["collector"]["l"] = QGridLayout()
        self.tabs["collector"]["w"].setLayout(self.tabs["collector"]["l"])
        self.tabs["collector"]["package_view"] = QTreeWidget()
        self.connect(self.tabs["collector"]["package_view"], SIGNAL("clear"), self.tabs["collector"]["package_view"].clear)
        self.tabs["collector"]["link_view"] = QTreeWidget()
        self.connect(self.tabs["collector"]["link_view"], SIGNAL("clear"), self.tabs["collector"]["link_view"].clear)
        groupPackage.layout().addWidget(self.tabs["collector"]["package_view"])
        groupPackage.layout().addWidget(toQueue)
        groupLinks.layout().addWidget(self.tabs["collector"]["link_view"])
        self.tabs["collector"]["l"].addWidget(groupPackage, 0, 0)
        self.tabs["collector"]["l"].addWidget(groupLinks, 0, 1)
        self.connect(toQueue, SIGNAL("clicked()"), self.slotPushPackageToQueue)
        self.tabs["collector"]["package_view"].setContextMenuPolicy(Qt.CustomContextMenu)
        self.tabs["collector"]["link_view"].setContextMenuPolicy(Qt.CustomContextMenu)
        self.tabs["queue"]["view"].setContextMenuPolicy(Qt.CustomContextMenu)
        
        #settings
        self.tabs["settings"]["l"] = QGridLayout()
        self.tabs["settings"]["w"].setLayout(self.tabs["settings"]["l"])
        #self.tabs["settings"]["view"] = QTreeWidget()
        #self.tabs["settings"]["l"].addWidget(self.tabs["settings"]["view"])
        
        #log
        self.tabs["log"]["l"] = QGridLayout()
        self.tabs["log"]["w"].setLayout(self.tabs["log"]["l"])
        self.tabs["log"]["text"] = QTextEdit()
        self.tabs["log"]["text"].logOffset = 0
        self.tabs["log"]["text"].setReadOnly(True)
        self.connect(self.tabs["log"]["text"], SIGNAL("append(QString)"), self.tabs["log"]["text"].append)
        self.tabs["log"]["l"].addWidget(self.tabs["log"]["text"])
    
    def init_context(self):
        """
            create context menus
        """
        self.queueContext = QMenu()
        self.queueContext.buttons = {}
        self.queueContext.item = (None, None)
        self.queueContext.buttons["remove"] = QAction(QIcon("icons/gui/remove_small.png"), "Remove", self.queueContext)
        self.queueContext.buttons["restart"] = QAction(QIcon("icons/gui/refresh_small.png"), "Restart", self.queueContext)
        self.queueContext.addAction(self.queueContext.buttons["remove"])
        self.queueContext.addAction(self.queueContext.buttons["restart"])
        self.connect(self.queueContext.buttons["remove"], SIGNAL("triggered()"), self.slotRemoveDownload)
        self.connect(self.queueContext.buttons["restart"], SIGNAL("triggered()"), self.slotRestartDownload)
    
    def slotToggleStatus(self, status):
        """
            pause/start toggle (toolbar)
        """
        self.emit(SIGNAL("setDownloadStatus"), status)
    
    def slotStatusStop(self):
        """
            stop button (toolbar)
        """
        self.emit(SIGNAL("stopAllDownloads"))
    
    def slotAdd(self):
        """
            add button (toolbar)
            show context menu (choice: links/package)
        """
        self.addMenu.exec_(QCursor.pos())
    
    def slotShowAddPackage(self):
        """
            action from add-menu
            show new-package dock
        """
        self.tabw.setCurrentIndex(1)
        self.newPackDock.show()
    
    def slotShowAddLinks(self):
        """
            action from add-menu
            show new-links dock
        """
        self.tabw.setCurrentIndex(1)
        self.newLinkDock.show()
    
    def slotShowConnector(self):
        """
            connectionmanager action triggered
            let main to the stuff
        """
        self.emit(SIGNAL("connector"))
    
    def slotAddLinks(self, links):
        """
            new links
            let main to the stuff
        """
        self.emit(SIGNAL("addLinks"), links)
    
    def slotAddPackage(self, name, ids):
        """
            new package
            let main to the stuff
        """
        self.emit(SIGNAL("addPackage"), name, ids)
    
    def slotShowAddContainer(self):
        """
            action from add-menu
            show file selector, emit upload
        """
        fileNames = QFileDialog.getOpenFileNames(self, "Container Öffnen", "", "All Container Types (*.dlc *.ccf *.rsdf *.txt);;DLC (*.dlc);;CCF (*.ccf);;RSDF (*.rsdf);;Text Files (*.txt)")
        for name in fileNames:
            self.emit(SIGNAL("addContainer"), str(name))
    
    def slotPushPackageToQueue(self):
        """
            push collector pack to queue
            get child ids
            let main to the rest
        """
        items = self.tabs["collector"]["package_view"].selectedItems()
        for item in items:
            id = item.data(0, Qt.UserRole).toPyObject()
            self.emit(SIGNAL("pushPackageToQueue"), id)
    
    def saveWindow(self):
        """
            get window state/geometry
            pass data to main
        """
        state_raw = self.saveState(self.version)
        geo_raw = self.saveGeometry()
        
        state = str(state_raw.toBase64())
        geo = str(geo_raw.toBase64())
        
        self.emit(SIGNAL("saveMainWindow"), state, geo)
    
    def closeEvent(self, event):
        """
            somebody wants to close me!
            let me first save my state
        """
        self.saveWindow()
        event.accept()
    
    def restoreWindow(self, state, geo):
        """
            restore window state/geometry
        """
        state = QByteArray(state)
        geo = QByteArray(geo)
        
        state_raw = QByteArray.fromBase64(state)
        geo_raw = QByteArray.fromBase64(geo)
        
        self.restoreState(state_raw, self.version)
        self.restoreGeometry(geo_raw)
    
    def slotQueueContextMenu(self, pos):
        """
            custom context menu in queue view requested
        """
        globalPos = self.tabs["queue"]["view"].mapToGlobal(pos)
        i = self.tabs["queue"]["view"].itemAt(pos)
        if not i:
            return
        i.setSelected(True)
        self.queueContext.item = (i.data(0, Qt.UserRole).toPyObject(), i.parent() == None)
        menuPos = QCursor.pos()
        menuPos.setX(menuPos.x()+2)
        self.queueContext.exec_(menuPos)
    
    def slotPackageCollectorContextMenu(self, pos):
        """
            custom context menu in package collector view requested
        """
        pass
    
    def slotLinkCollectorContextMenu(self, pos):
        """
            custom context menu in link collector view requested
        """
        pass
    
    def slotRestartDownload(self):
        """
            restart download action is triggered
        """
        id, isTopLevel = self.queueContext.item
        if not id == None:
            self.emit(SIGNAL("restartDownload"), id, isTopLevel)
    
    def slotRemoveDownload(self):
        """
            remove download action is triggered
        """
        id, isTopLevel = self.queueContext.item
        if not id == None:
            self.emit(SIGNAL("removeDownload"), id, isTopLevel)

