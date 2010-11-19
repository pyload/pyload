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

from module.gui.PackageDock import *
from module.gui.LinkDock import *
from module.gui.CaptchaDock import CaptchaDock
from module.gui.SettingsWidget import SettingsWidget

from module.gui.Collector import CollectorView, Package, Link
from module.gui.Queue import QueueView
from module.gui.Accounts import AccountView
from module.gui.AccountEdit import AccountEdit

class MainWindow(QMainWindow):
    def __init__(self, connector):
        """
            set up main window
        """
        QMainWindow.__init__(self)
        #window stuff
        self.setWindowTitle(_("pyLoad Client"))
        self.setWindowIcon(QIcon(join(pypath, "icons","logo.png")))
        self.resize(900,500)
        
        #layout version
        self.version = 3
        
        #init docks
        self.newPackDock = NewPackageDock()
        self.addDockWidget(Qt.RightDockWidgetArea, self.newPackDock)
        self.connect(self.newPackDock, SIGNAL("done"), self.slotAddPackage)
        self.captchaDock = CaptchaDock()
        self.addDockWidget(Qt.BottomDockWidgetArea, self.captchaDock)
        self.newLinkDock = NewLinkDock()
        self.addDockWidget(Qt.RightDockWidgetArea, self.newLinkDock)
        self.connect(self.newLinkDock, SIGNAL("done"), self.slotAddLinksToPackage)
        
        #central widget, layout
        self.masterlayout = QVBoxLayout()
        lw = QWidget()
        lw.setLayout(self.masterlayout)
        self.setCentralWidget(lw)
        
        #status
        #@TODO: build a fancy box
        
        #self.statusw = QFrame()
        #self.statusw.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        #self.statusw.setLineWidth(2)
        #self.statusw.setLayout(QGridLayout())
        #l = self.statusw.layout()
        #l.addWidget(QLabel("Status:"), 0, 0)
        #l.addWidget(QLabel("Speed:"), 0, 3)
        #l.addWidget(QLabel("Space:"), 0, 5)

        #set menubar and statusbar
        self.menubar = self.menuBar()
        self.statusbar = self.statusBar()
        self.connect(self.statusbar, SIGNAL("showMsg"), self.statusbar.showMessage)
        self.serverStatus = QLabel(_("Status: Not Connected"))
        self.statusbar.addPermanentWidget(self.serverStatus)
        
        #menu
        self.menus = {}
        self.menus["file"] = self.menubar.addMenu(_("File"))
        self.menus["connections"] = self.menubar.addMenu(_("Connections"))
        
        #menu actions
        self.mactions = {}
        self.mactions["exit"] = QAction(_("Exit"), self.menus["file"])
        self.mactions["manager"] = QAction(_("Connection manager"), self.menus["connections"])
        
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
        self.tabs["accounts"] = {"w":QWidget()}
        self.tabs["settings"] = {}
        #self.tabs["settings"]["s"] = QScrollArea()
        self.tabs["settings"]["w"] = SettingsWidget()
        #self.tabs["settings"]["s"].setWidgetResizable(True)
        #self.tabs["settings"]["s"].setWidget(self.tabs["settings"]["w"])
        self.tabs["log"] = {"w":QWidget()}
        self.tabw.addTab(self.tabs["queue"]["w"], _("Queue"))
        self.tabw.addTab(self.tabs["collector"]["w"], _("Collector"))
        self.tabw.addTab(self.tabs["accounts"]["w"], _("Accounts"))
        self.tabw.addTab(self.tabs["settings"]["w"], _("Settings"))
        self.tabw.addTab(self.tabs["log"]["w"], _("Log"))
        
        #init tabs
        self.init_tabs(connector)
        
        self.setPriority = Priority(self)
        
        #context menus
        self.init_context()
        
        #layout
        self.masterlayout.addWidget(self.tabw)
        #self.masterlayout.addWidget(self.statusw)
        
        #signals..
        self.connect(self.mactions["manager"], SIGNAL("triggered()"), self.slotShowConnector)
        
        self.connect(self.tabs["queue"]["view"], SIGNAL('customContextMenuRequested(const QPoint &)'), self.slotQueueContextMenu)
        self.connect(self.tabs["collector"]["package_view"], SIGNAL('customContextMenuRequested(const QPoint &)'), self.slotCollectorContextMenu)
        self.connect(self.tabs["accounts"]["view"], SIGNAL('customContextMenuRequested(const QPoint &)'), self.slotAccountContextMenu)
        
        self.connect(self.tabw, SIGNAL("currentChanged(int)"), self.slotTabChanged)
        
        self.lastAddedID = None
        
        self.connector = connector
    
    def init_toolbar(self):
        """
            create toolbar
        """
        self.toolbar = self.addToolBar(_("Main Toolbar"))
        self.toolbar.setObjectName("Main Toolbar")
        self.toolbar.setIconSize(QSize(40,40))
        self.actions["toggle_status"] = self.toolbar.addAction(_("Toggle Pause/Resume"))
        pricon = QIcon()
        pricon.addFile(join(pypath, "icons","toolbar_start.png"), QSize(), QIcon.Normal, QIcon.Off)
        pricon.addFile(join(pypath, "icons","toolbar_pause.png"), QSize(), QIcon.Normal, QIcon.On)
        self.actions["toggle_status"].setIcon(pricon)
        self.actions["toggle_status"].setCheckable(True)
        self.actions["status_stop"] = self.toolbar.addAction(QIcon(join(pypath, "icons","toolbar_stop.png")), _("Stop"))
        self.toolbar.addSeparator()
        self.actions["add"] = self.toolbar.addAction(QIcon(join(pypath, "icons","toolbar_add.png")), _("Add"))
        self.toolbar.addSeparator()
        self.actions["clipboard"] = self.toolbar.addAction(QIcon(join(pypath, "icons","clipboard.png")), _("Check Clipboard"))
        self.actions["clipboard"].setCheckable(True)
        
        self.connect(self.actions["toggle_status"], SIGNAL("toggled(bool)"), self.slotToggleStatus)
        self.connect(self.actions["clipboard"], SIGNAL("toggled(bool)"), self.slotToggleClipboard)
        self.connect(self.actions["status_stop"], SIGNAL("triggered()"), self.slotStatusStop)
        self.addMenu = QMenu()
        packageAction = self.addMenu.addAction(_("Package"))
        containerAction = self.addMenu.addAction(_("Container"))
        accountAction = self.addMenu.addAction(_("Account"))
        linksAction = self.addMenu.addAction(_("Links"))
        self.connect(self.actions["add"], SIGNAL("triggered()"), self.slotAdd)
        self.connect(packageAction, SIGNAL("triggered()"), self.slotShowAddPackage)
        self.connect(containerAction, SIGNAL("triggered()"), self.slotShowAddContainer)
        self.connect(accountAction, SIGNAL("triggered()"), self.slotNewAccount)
        self.connect(linksAction, SIGNAL("triggered()"), self.slotShowAddLinks)
    
    def init_tabs(self, connector):
        """
            create tabs
        """
        #queue
        self.tabs["queue"]["l"] = QGridLayout()
        self.tabs["queue"]["w"].setLayout(self.tabs["queue"]["l"])
        self.tabs["queue"]["view"] = QueueView(connector)
        self.tabs["queue"]["l"].addWidget(self.tabs["queue"]["view"])
        
        #collector
        toQueue = QPushButton(_("Push selected packages to queue"))
        self.tabs["collector"]["l"] = QGridLayout()
        self.tabs["collector"]["w"].setLayout(self.tabs["collector"]["l"])
        self.tabs["collector"]["package_view"] = CollectorView(connector)
        self.tabs["collector"]["l"].addWidget(self.tabs["collector"]["package_view"], 0, 0)
        self.tabs["collector"]["l"].addWidget(toQueue, 1, 0)
        self.connect(toQueue, SIGNAL("clicked()"), self.slotPushPackageToQueue)
        self.tabs["collector"]["package_view"].setContextMenuPolicy(Qt.CustomContextMenu)
        self.tabs["queue"]["view"].setContextMenuPolicy(Qt.CustomContextMenu)
        
        #log
        self.tabs["log"]["l"] = QGridLayout()
        self.tabs["log"]["w"].setLayout(self.tabs["log"]["l"])
        self.tabs["log"]["text"] = QTextEdit()
        self.tabs["log"]["text"].logOffset = 0
        self.tabs["log"]["text"].setReadOnly(True)
        self.connect(self.tabs["log"]["text"], SIGNAL("append(QString)"), self.tabs["log"]["text"].append)
        self.tabs["log"]["l"].addWidget(self.tabs["log"]["text"])
        
        #accounts
        self.tabs["accounts"]["view"] = AccountView(connector)
        self.tabs["accounts"]["w"].setLayout(QVBoxLayout())
        self.tabs["accounts"]["w"].layout().addWidget(self.tabs["accounts"]["view"])
        newbutton = QPushButton(_("New Account"))
        self.tabs["accounts"]["w"].layout().addWidget(newbutton)
        self.connect(newbutton, SIGNAL("clicked()"), self.slotNewAccount)
        self.tabs["accounts"]["view"].setContextMenuPolicy(Qt.CustomContextMenu)
    
    def init_context(self):
        """
            create context menus
        """
        self.activeMenu = None
        #queue
        self.queueContext = QMenu()
        self.queueContext.buttons = {}
        self.queueContext.item = (None, None)
        self.queueContext.buttons["remove"] = QAction(QIcon(join(pypath, "icons","remove_small.png")), _("Remove"), self.queueContext)
        self.queueContext.buttons["restart"] = QAction(QIcon(join(pypath, "icons","refresh_small.png")), _("Restart"), self.queueContext)
        self.queueContext.buttons["pull"] = QAction(QIcon(join(pypath, "icons","pull_small.png")), _("Pull out"), self.queueContext)
        self.queueContext.buttons["abort"] = QAction(QIcon(join(pypath, "icons","abort.png")), _("Abort"), self.queueContext)
        self.queueContext.buttons["edit"] = QAction(QIcon(join(pypath, "icons","edit_small.png")), _("Edit Name"), self.queueContext)
        self.queuePriorityMenu = QMenu(_("Priority"))
        self.queuePriorityMenu.actions = {}
        self.queuePriorityMenu.actions["veryhigh"] = QAction(_("very high"), self.queuePriorityMenu)
        self.queuePriorityMenu.addAction(self.queuePriorityMenu.actions["veryhigh"])
        self.queuePriorityMenu.actions["high"] = QAction(_("high"), self.queuePriorityMenu)
        self.queuePriorityMenu.addAction(self.queuePriorityMenu.actions["high"])
        self.queuePriorityMenu.actions["normal"] = QAction(_("normal"), self.queuePriorityMenu)
        self.queuePriorityMenu.addAction(self.queuePriorityMenu.actions["normal"])
        self.queuePriorityMenu.actions["low"] = QAction(_("low"), self.queuePriorityMenu)
        self.queuePriorityMenu.addAction(self.queuePriorityMenu.actions["low"])
        self.queuePriorityMenu.actions["verylow"] = QAction(_("very low"), self.queuePriorityMenu)
        self.queuePriorityMenu.addAction(self.queuePriorityMenu.actions["verylow"])
        self.queueContext.addAction(self.queueContext.buttons["pull"])
        self.queueContext.addAction(self.queueContext.buttons["edit"])
        self.queueContext.addAction(self.queueContext.buttons["remove"])
        self.queueContext.addAction(self.queueContext.buttons["restart"])
        self.queueContext.addAction(self.queueContext.buttons["abort"])
        self.queueContext.addMenu(self.queuePriorityMenu)
        self.connect(self.queueContext.buttons["remove"], SIGNAL("triggered()"), self.slotRemoveDownload)
        self.connect(self.queueContext.buttons["restart"], SIGNAL("triggered()"), self.slotRestartDownload)
        self.connect(self.queueContext.buttons["pull"], SIGNAL("triggered()"), self.slotPullOutPackage)
        self.connect(self.queueContext.buttons["abort"], SIGNAL("triggered()"), self.slotAbortDownload)
        self.connect(self.queueContext.buttons["edit"], SIGNAL("triggered()"), self.slotEditPackage)
        
        self.connect(self.queuePriorityMenu.actions["veryhigh"], SIGNAL("triggered()"), self.setPriority.veryHigh)
        self.connect(self.queuePriorityMenu.actions["high"], SIGNAL("triggered()"), self.setPriority.high)
        self.connect(self.queuePriorityMenu.actions["normal"], SIGNAL("triggered()"), self.setPriority.normal)
        self.connect(self.queuePriorityMenu.actions["low"], SIGNAL("triggered()"), self.setPriority.low)
        self.connect(self.queuePriorityMenu.actions["verylow"], SIGNAL("triggered()"), self.setPriority.veryLow)
        
        #collector
        self.collectorContext = QMenu()
        self.collectorContext.buttons = {}
        self.collectorContext.item = (None, None)
        self.collectorContext.buttons["remove"] = QAction(QIcon(join(pypath, "icons","remove_small.png")), _("Remove"), self.collectorContext)
        self.collectorContext.buttons["push"] = QAction(QIcon(join(pypath, "icons","push_small.png")), _("Push to queue"), self.collectorContext)
        self.collectorContext.buttons["edit"] = QAction(QIcon(join(pypath, "icons","edit_small.png")), _("Edit Name"), self.collectorContext)
        self.collectorContext.buttons["restart"] = QAction(QIcon(join(pypath, "icons","refresh_small.png")), _("Restart"), self.collectorContext)
        self.collectorContext.buttons["refresh"] = QAction(QIcon(join(pypath, "icons","refresh1_small.png")),_("Refresh Status"), self.collectorContext)
        self.collectorContext.addAction(self.collectorContext.buttons["push"])
        self.collectorContext.addSeparator()
        self.collectorContext.buttons["add"] = self.collectorContext.addMenu(QIcon(join(pypath, "icons","add_small.png")), _("Add"))
        self.collectorContext.addAction(self.collectorContext.buttons["edit"])
        self.collectorContext.addAction(self.collectorContext.buttons["remove"])
        self.collectorContext.addAction(self.collectorContext.buttons["restart"])
        self.collectorContext.addSeparator()
        self.collectorContext.addAction(self.collectorContext.buttons["refresh"])
        packageAction = self.collectorContext.buttons["add"].addAction(_("Package"))
        containerAction = self.collectorContext.buttons["add"].addAction(_("Container"))
        linkAction = self.collectorContext.buttons["add"].addAction(_("Links"))
        self.connect(self.collectorContext.buttons["remove"], SIGNAL("triggered()"), self.slotRemoveDownload)
        self.connect(self.collectorContext.buttons["push"], SIGNAL("triggered()"), self.slotPushPackageToQueue)
        self.connect(self.collectorContext.buttons["edit"], SIGNAL("triggered()"), self.slotEditPackage)
        self.connect(self.collectorContext.buttons["restart"], SIGNAL("triggered()"), self.slotRestartDownload)
        self.connect(self.collectorContext.buttons["refresh"], SIGNAL("triggered()"), self.slotRefreshPackage)
        self.connect(packageAction, SIGNAL("triggered()"), self.slotShowAddPackage)
        self.connect(containerAction, SIGNAL("triggered()"), self.slotShowAddContainer)
        self.connect(linkAction, SIGNAL("triggered()"), self.slotShowAddLinks)
        
        self.accountContext = QMenu()
        self.accountContext.buttons = {}
        self.accountContext.buttons["add"] = QAction(QIcon(join(pypath, "icons","add_small.png")), _("Add"), self.accountContext)
        self.accountContext.buttons["remove"] = QAction(QIcon(join(pypath, "icons","remove_small.png")), _("Remove"), self.accountContext)
        self.accountContext.buttons["edit"] = QAction(QIcon(join(pypath, "icons","edit_small.png")), _("Edit"), self.accountContext)
        self.accountContext.addAction(self.accountContext.buttons["add"])
        self.accountContext.addAction(self.accountContext.buttons["edit"])
        self.accountContext.addAction(self.accountContext.buttons["remove"])
        self.connect(self.accountContext.buttons["add"], SIGNAL("triggered()"), self.slotNewAccount)
        self.connect(self.accountContext.buttons["edit"], SIGNAL("triggered()"), self.slotEditAccount)
        self.connect(self.accountContext.buttons["remove"], SIGNAL("triggered()"), self.slotRemoveAccount)
    
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
    
    def slotAddPackage(self, name, links, password=None):
        """
            new package
            let main to the stuff
        """
        self.emit(SIGNAL("addPackage"), name, links, password)
        
    def slotAddLinksToPackage(self, links):
        """
            adds links to currently selected package
            only in collector
        """
        if self.tabw.currentIndex() != 1:
            return
        
        smodel = self.tabs["collector"]["package_view"].selectionModel()
        for index in smodel.selectedRows(0):
            item = index.internalPointer()
            if isinstance(item, Package):
                self.connector.proxy.add_files(item.id, links)
                break
    
    def slotShowAddContainer(self):
        """
            action from add-menu
            show file selector, emit upload
        """
        typeStr = ";;".join([
            _("All Container Types (%s)") % "*.dlc *.ccf *.rsdf *.txt",
            _("DLC (%s)") % "*.dlc",
            _("CCF (%s)") % "*.ccf",
            _("RSDF (%s)") % "*.rsdf",
            _("Text Files (%s)") % "*.txt"
        ])
        fileNames = QFileDialog.getOpenFileNames(self, _("Open container"), "", typeStr)
        for name in fileNames:
            self.emit(SIGNAL("addContainer"), str(name))
    
    def slotPushPackageToQueue(self):
        """
            push collector pack to queue
            get child ids
            let main to the rest
        """
        smodel = self.tabs["collector"]["package_view"].selectionModel()
        for index in smodel.selectedRows(0):
            item = index.internalPointer()
            if isinstance(item, Package):
                self.emit(SIGNAL("pushPackageToQueue"), item.id)
            else:
                self.emit(SIGNAL("pushPackageToQueue"), item.package.id)
    
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
        event.ignore()
        self.hide()
        self.emit(SIGNAL("hidden"))
    
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
        i = self.tabs["queue"]["view"].indexAt(pos)
        if not i:
            return
        item = i.internalPointer()
        menuPos = QCursor.pos()
        menuPos.setX(menuPos.x()+2)
        self.activeMenu = self.queueContext
        showAbort = False
        if isinstance(item, Link) and item.data["downloading"]:
            showAbort = True
        elif isinstance(item, Package):
            for child in item.children:
                if child.data["downloading"]:
                    showAbort = True
                    break
        if showAbort:
            self.queueContext.buttons["abort"].setEnabled(True)
        else:
            self.queueContext.buttons["abort"].setEnabled(False)
        if isinstance(item, Package):
            self.queueContext.index = i
            self.queueContext.buttons["remove"].setEnabled(True)
            self.queueContext.buttons["restart"].setEnabled(True)
            self.queueContext.buttons["pull"].setEnabled(True)
            self.queueContext.buttons["edit"].setEnabled(True)
            self.queuePriorityMenu.setEnabled(True)
        elif isinstance(item, Link):
            self.collectorContext.index = i
            self.collectorContext.buttons["edit"].setEnabled(False)
            self.collectorContext.buttons["remove"].setEnabled(True)
            self.collectorContext.buttons["push"].setEnabled(False)
            self.collectorContext.buttons["restart"].setEnabled(True)
        else:
            self.queueContext.index = None
            self.queueContext.buttons["remove"].setEnabled(False)
            self.queueContext.buttons["restart"].setEnabled(False)
            self.queueContext.buttons["pull"].setEnabled(False)
            self.queueContext.buttons["edit"].setEnabled(False)
            self.queuePriorityMenu.setEnabled(False)
        self.queueContext.exec_(menuPos)
    
    def slotCollectorContextMenu(self, pos):
        """
            custom context menu in package collector view requested
        """
        globalPos = self.tabs["collector"]["package_view"].mapToGlobal(pos)
        i = self.tabs["collector"]["package_view"].indexAt(pos)
        if not i:
            return
        item = i.internalPointer()
        menuPos = QCursor.pos()
        menuPos.setX(menuPos.x()+2)
        self.activeMenu = self.collectorContext
        if isinstance(item, Package):
            self.collectorContext.index = i
            self.collectorContext.buttons["edit"].setEnabled(True)
            self.collectorContext.buttons["remove"].setEnabled(True)
            self.collectorContext.buttons["push"].setEnabled(True)
            self.collectorContext.buttons["restart"].setEnabled(True)
        elif isinstance(item, Link):
            self.collectorContext.index = i
            self.collectorContext.buttons["edit"].setEnabled(False)
            self.collectorContext.buttons["remove"].setEnabled(True)
            self.collectorContext.buttons["push"].setEnabled(False)
            self.collectorContext.buttons["restart"].setEnabled(True)
        else:
            self.collectorContext.index = None
            self.collectorContext.buttons["edit"].setEnabled(False)
            self.collectorContext.buttons["remove"].setEnabled(False)
            self.collectorContext.buttons["push"].setEnabled(False)
            self.collectorContext.buttons["restart"].setEnabled(False)
        self.collectorContext.exec_(menuPos)
    
    def slotLinkCollectorContextMenu(self, pos):
        """
            custom context menu in link collector view requested
        """
        pass
    
    def slotRestartDownload(self):
        """
            restart download action is triggered
        """
        smodel = self.tabs["queue"]["view"].selectionModel()
        for index in smodel.selectedRows(0):
            item = index.internalPointer()
            self.emit(SIGNAL("restartDownload"), item.id, isinstance(item, Package))
    
    def slotRemoveDownload(self):
        """
            remove download action is triggered
        """
        if self.activeMenu == self.queueContext:
            view = self.tabs["queue"]["view"]
        else:
            view = self.tabs["collector"]["package_view"]
        smodel = view.selectionModel()
        for index in smodel.selectedRows(0):
            item = index.internalPointer()
            self.emit(SIGNAL("removeDownload"), item.id, isinstance(item, Package))
    
    def slotToggleClipboard(self, status):
        """
            check clipboard (toolbar)
        """
        self.emit(SIGNAL("setClipboardStatus"), status)
    
    def slotEditPackage(self):
        # in Queue, only edit name
        if self.activeMenu == self.queueContext:
            view = self.tabs["queue"]["view"]
        else:
            view = self.tabs["collector"]["package_view"]
        view.edit(self.activeMenu.index)

    def slotEditCommit(self, editor):
        self.emit(SIGNAL("changePackageName"), self.activeMenu.index.internalPointer().id, editor.text())
    
    def slotPullOutPackage(self):
        """
            pull package out of the queue
        """
        smodel = self.tabs["queue"]["view"].selectionModel()
        for index in smodel.selectedRows(0):
            item = index.internalPointer()
            if isinstance(item, Package):
                self.emit(SIGNAL("pullOutPackage"), item.id)
            else:
                self.emit(SIGNAL("pullOutPackage"), item.package.id)
    
    def slotAbortDownload(self):
        view = self.tabs["queue"]["view"]
        smodel = view.selectionModel()
        for index in smodel.selectedRows(0):
            item = index.internalPointer()
            self.emit(SIGNAL("abortDownload"), item.id, isinstance(item, Package))
    
    def changeEvent(self, e):
        if e.type() == QEvent.WindowStateChange and self.isMinimized():
            e.ignore()
            self.hide()
            self.emit(SIGNAL("hidden"))
        else:
            super(MainWindow, self).changeEvent(e)
    
    def slotTabChanged(self, index):
        if index == 2:
            self.emit(SIGNAL("reloadAccounts"))
        elif index == 3:
            self.tabs["settings"]["w"].loadConfig()
    
    def slotRefreshPackage(self):
        smodel = self.tabs["collector"]["package_view"].selectionModel()
        for index in smodel.selectedRows(0):
            item = index.internalPointer()
            pid = item.id
            if isinstance(item, Link):
                pid = item.package.id
            self.emit(SIGNAL("refreshStatus"), pid)
    
    def slotNewAccount(self):
        types = self.connector.proxy.get_accounts(False, False).keys()
        self.accountEdit = AccountEdit.newAccount(types)
        
        def save(data):
            if data["password"]:
                self.accountEdit.close()
                self.connector.proxy.update_account(data["acctype"], data["login"], data["password"])
            
        self.accountEdit.connect(self.accountEdit, SIGNAL("done"), save)
        self.accountEdit.show()
    
    def slotEditAccount(self):
        types = self.connector.proxy.get_accounts(False, False).keys()
        
        data = self.tabs["accounts"]["view"].selectedIndexes()
        if len(data) < 1:
            return
            
        data = data[0].internalPointer()
        
        self.accountEdit = AccountEdit.editAccount(types, data)
        
        def save(data):
            self.accountEdit.close()
            self.connector.proxy.update_account(data["acctype"], data["login"], data["password"] if data["password"] else None)
            
        self.accountEdit.connect(self.accountEdit, SIGNAL("done"), save)
        self.accountEdit.show()
    
    def slotRemoveAccount(self):
        data = self.tabs["accounts"]["view"].selectedIndexes()
        if len(data) < 1:
            return
            
        data = data[0].internalPointer()
        
        self.connector.proxy.remove_account(data["type"], data["login"])
    
    def slotAccountContextMenu(self, pos):
        globalPos = self.tabs["accounts"]["view"].mapToGlobal(pos)
        i = self.tabs["accounts"]["view"].indexAt(pos)
        if not i:
            return
            
        data = i.internalPointer()
        
        if data is None:
            self.accountContext.buttons["edit"].setEnabled(False)
            self.accountContext.buttons["remove"].setEnabled(False)
        else:
            self.accountContext.buttons["edit"].setEnabled(True)
            self.accountContext.buttons["remove"].setEnabled(True)
        
        menuPos = QCursor.pos()
        menuPos.setX(menuPos.x()+2)
        self.accountContext.exec_(menuPos)
    
class Priority():
    def __init__(self, win):
        self.w = win
    
    def setPriority(self, level):
        if self.w.activeMenu == self.w.queueContext:
            smodel = self.w.tabs["queue"]["view"].selectionModel()
        else:
            smodel = self.w.tabs["collector"]["package_view"].selectionModel()
        for index in smodel.selectedRows(0):
            item = index.internalPointer()
            pid = item.id if isinstance(item, Package) else item.package.id
            self.w.emit(SIGNAL("setPriority"), pid, level)
    
    def veryHigh(self): self.setPriority(2)
    def high(self): self.setPriority(1)
    def normal(self): self.setPriority(0)
    def low(self): self.setPriority(-1)
    def veryLow(self): self.setPriority(-2)
    
    
    
