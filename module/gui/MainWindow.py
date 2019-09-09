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

import logging
import re

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from os.path import join, dirname
from datetime import datetime

from module.gui.PackageDock import *
from module.gui.LinkDock import *
from module.gui.CaptchaDialog import CaptchaDialog
from module.gui.SettingsWidget import SettingsWidget
from module.gui.Collector import CollectorView, Package, Link
from module.gui.Queue import QueueView
from module.gui.Overview import OverviewView
from module.gui.Accounts import AccountView
from module.gui.AccountEdit import AccountEdit
from module.gui.Tools import whatsThisFormat

from module.remote.thriftbackend.ThriftClient import DownloadStatus

class MainWindow(QMainWindow):
    
    def time_msec(self):
        return int((datetime.utcnow() - datetime(1970, 1, 1)).total_seconds() * 1000 - self.time_msec_init)
    
    def __init__(self, corePermissions, connector):
        """
            set up main window
        """
        self.time_msec_init = int((datetime.utcnow() - datetime(1970, 1, 1)).total_seconds() * 1000)
        QMainWindow.__init__(self)
        self.setEnabled(False)
        self.log = logging.getLogger("guilog")
        self.corePermissions = corePermissions
        self.connector = connector
        self.lastAddContainerDir = unicode("")
        
        #window stuff
        self.setWindowFlags(self.windowFlags() | Qt.WindowContextHelpButtonHint)
        self.setWindowTitle(_("pyLoad Client"))
        self.setWindowIcon(QIcon(join(pypath, "icons", "logo.png")))
        self.resize(100 ,100)
        self.move(200 ,200)
        self.initEventHooks()
        
        #layout version
        self.version = 3
        
        #init docks
        self.setDockOptions(QMainWindow.AnimatedDocks | QMainWindow.AllowTabbedDocks | QMainWindow.ForceTabbedDocks)
        self.setTabPosition(Qt.RightDockWidgetArea, QTabWidget.North)
        self.newPackDock = NewPackageDock()
        self.addDockWidget(Qt.RightDockWidgetArea, self.newPackDock)
        self.connect(self.newPackDock, SIGNAL("done"), self.slotAddPackage)
        self.connect(self.newPackDock, SIGNAL("parseUri"), self.slotParseUri)
        self.newLinkDock = NewLinkDock()
        self.addDockWidget(Qt.RightDockWidgetArea, self.newLinkDock)
        self.connect(self.newLinkDock, SIGNAL("done"), self.slotAddLinksToPackage)
        self.connect(self.newLinkDock, SIGNAL("parseUri"), self.slotParseUri)
        self.tabifyDockWidget(self.newPackDock, self.newLinkDock)
        self.captchaDialog = CaptchaDialog()
        
        #central widget, layout
        self.masterlayout = QVBoxLayout()
        lw = QWidget()
        lw.setLayout(self.masterlayout)
        self.setCentralWidget(lw)
        
        #status
        self.statusw = QFrame()
        self.statusw.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        self.statusw.setLineWidth(2)
        self.statusw.setLayout(QGridLayout())
        #palette = self.statusw.palette()
        #palette.setColor(QPalette.Window, QColor(255, 255, 255))
        #self.statusw.setPalette(palette)
        #self.statusw.setAutoFillBackground(True)
        l = self.statusw.layout()
        
        class BoldLabel(QLabel):
            def __init__(self, text):
                QLabel.__init__(self, text)
                f = self.font()
                f.setBold(True)
                self.setFont(f)
                self.setAlignment(Qt.AlignRight)
        
        #class Seperator(QFrame):
        #    def __init__(self):
        #        QFrame.__init__(self)
        #        self.setFrameShape(QFrame.VLine)
        #        self.setFrameShadow(QFrame.Sunken)
        
        class StwItem(QWidget):
            def __init__(self, lbl1, lbl2, wthis):
                QWidget.__init__(self)
                hbox = QHBoxLayout()
                hbox.setContentsMargins(0, 0, 0, 0)
                hbox.addStretch(1)
                hbox.addWidget(lbl1)
                hbox.addWidget(lbl2)
                hbox.addStretch(1)
                self.setLayout(hbox)
                self.setWhatsThis(wthis)
        
        packageCountBl = BoldLabel(_("Packages") + ":")
        self.packageCount = QLabel()
        sitem = StwItem(packageCountBl, self.packageCount, whatsThisFormat(_("Packages"), _("The number of packages in the Queue.")))
        l.addWidget(sitem, 0, 0, 1, 1)
        
        fileCountBl = BoldLabel(_("Links") + ":")
        self.fileCount = QLabel()
        sitem = StwItem(fileCountBl, self.fileCount, whatsThisFormat(_("Links"), _("The number of links in the Queue.")))
        l.addWidget(sitem, 0, 1, 1, 1)
        
        statusBl = BoldLabel(_("Status") + ":")
        self.status = QLabel()
        sitem = StwItem(statusBl, self.status, whatsThisFormat(_("Status"), _("It shows 'Running' or 'Paused'.")))
        l.addWidget(sitem, 0, 2, 1, 1)
        
        spaceBl = BoldLabel(_("Space") + ":")
        self.space = QLabel()
        sitem = StwItem(spaceBl, self.space, whatsThisFormat(_("Space"), _("The free space in the download folder.")))
        l.addWidget(sitem, 0, 3, 1, 1)
        
        speedBl = BoldLabel(_("Speed") + ":")
        self.speed = QLabel()
        sitem = StwItem(speedBl, self.speed, whatsThisFormat(_("Speed"), _("The actual download speed.")))
        l.addWidget(sitem, 0, 4, 1, 1)
        
        #l.addWidget(BoldLabel(_("Max. downloads:")), 0, 9)
        #l.addWidget(BoldLabel(_("Max. chunks:")), 1, 9)
        #self.maxDownloads = QSpinBox()
        #self.maxDownloads.setEnabled(False)
        #self.maxChunks = QSpinBox()
        #self.maxChunks.setEnabled(False)
        #l.addWidget(self.maxDownloads, 0, 10)
        #l.addWidget(self.maxChunks, 1, 10)

        #set menubar and statusbar
        self.menubar = self.menuBar()
        #self.statusbar = self.statusBar()
        #self.connect(self.statusbar, SIGNAL("showMsg"), self.statusbar.showMessage)
        #self.serverStatus = QLabel(_("Status: Not Connected"))
        #self.statusbar.addPermanentWidget(self.serverStatus)
        
        #menu
        self.menus = {"file": self.menubar.addMenu(_("File")),
                      "options": self.menubar.addMenu(_("Options")),
                      "view": self.menubar.addMenu(_("View")),
                      "help": self.menubar.addMenu(_("Help"))}

        #menu actions
        self.mactions = {"manager": QAction(_("Connection Manager"), self.menus["file"]),
                         "coreperms": QAction(_("Server Permissions"), self.menus["file"]),
                         "quitcore": QAction(_("Quit pyLoad Server"), self.menus["file"]),
                         "restartcore": QAction(_("Restart pyLoad Server"), self.menus["file"]),
                         "exit": QAction(_("Exit"), self.menus["file"]),
                         "notifications": QAction(_("Desktop Notifications"), self.menus["options"]),
                         "logging": QAction(_("Client Log"), self.menus["options"]),
                         "cnlfwding": QAction(_("ClickNLoad Forwarding"), self.menus["options"]),
                         "autoreloading": QAction(_("Automatic Reloading"), self.menus["options"]),
                         "captcha": QAction(_("Captchas"), self.menus["options"]),
                         "fonts": QAction(_("Fonts"), self.menus["options"]),
                         "tray": QAction(_("Tray Icon"), self.menus["options"]),
                         "whatsthis": QAction(_("What's This"), self.menus["options"]),
                         "other": QAction(_("Other"), self.menus["options"]),
                         "language": QAction(_("Language"), self.menus["options"]),
                         "reload": QAction(_("Reload"), self.menus["view"]),
                         "showcaptcha": QAction(_("Show Captcha"), self.menus["view"]),
                         "showtoolbar": QAction(_("Show Toolbar"), self.menus["view"]),
                         "showspeedlimit": QAction(_("Show Speed Limit"), self.menus["view"]),
                         "whatsthismode": QAction("What's This?", self.menus["help"]),
                         "about": QAction(_("About pyLoad Client"), self.menus["help"])}
        
        self.mactions["showtoolbar"].setCheckable(True)
        self.mactions["showspeedlimit"].setCheckable(True)
        self.mactions["showspeedlimit"].setChecked(True)

        #add menu actions
        self.menus["file"].addAction(self.mactions["manager"])
        self.menus["file"].addAction(self.mactions["coreperms"])
        self.menus["file"].addSeparator()
        self.menus["file"].addAction(self.mactions["quitcore"])
        self.menus["file"].addAction(self.mactions["restartcore"])
        self.menus["file"].addSeparator()
        self.menus["file"].addAction(self.mactions["exit"])
        self.menus["options"].addAction(self.mactions["notifications"])
        self.menus["options"].addAction(self.mactions["logging"])
        self.menus["options"].addAction(self.mactions["cnlfwding"])
        self.menus["options"].addAction(self.mactions["autoreloading"])
        self.menus["options"].addAction(self.mactions["captcha"])
        self.menus["options"].addAction(self.mactions["fonts"])
        self.menus["options"].addAction(self.mactions["tray"])
        self.menus["options"].addAction(self.mactions["whatsthis"])
        self.menus["options"].addAction(self.mactions["other"])
        self.menus["options"].addSeparator()
        self.menus["options"].addAction(self.mactions["language"])
        self.menus["view"].addAction(self.mactions["reload"])
        self.menus["view"].addAction(self.mactions["showcaptcha"])
        self.menus["view"].addSeparator()
        self.menus["view"].addAction(self.mactions["showtoolbar"])
        self.menus["view"].addAction(self.mactions["showspeedlimit"])
        self.menus["help"].addAction(self.mactions["whatsthismode"])
        self.menus["help"].addSeparator()
        self.menus["help"].addAction(self.mactions["about"])
        
        #toolbar
        self.actions = {}
        self.init_toolbar()
        
        #tabs
        self.tabw = QTabWidget()
        self.tabs = {"overview": {"w": QWidget()},
                     "queue": {"w": QWidget()},
                     "collector": {"w": QWidget()},
                     "accounts": {"w": QWidget()},
                     "settings": {}}
        #self.tabs["settings"]["s"] = QScrollArea()
        self.tabs["settings"]["w"] = SettingsWidget(self.corePermissions)
        #self.tabs["settings"]["s"].setWidgetResizable(True)
        #self.tabs["settings"]["s"].setWidget(self.tabs["settings"]["w"])
        self.tabs["guilog"] = {"w":QWidget()}
        self.tabs["corelog"] = {"w":QWidget()}
        self.tabw.addTab(self.tabs["overview"]["w"], _("Overview"))
        self.tabw.addTab(self.tabs["queue"]["w"], _("Queue"))
        self.tabw.addTab(self.tabs["collector"]["w"], _("Collector"))
        self.tabw.addTab(self.tabs["accounts"]["w"], _("Accounts"))
        self.tabw.addTab(self.tabs["guilog"]["w"], _("Log"))
        self.tabw.addTab(self.tabs["settings"]["w"], _("Server Settings"))
        self.tabw.addTab(self.tabs["corelog"]["w"], _("Server Log"))
        
        #init tabs
        self.init_tabs(self.connector)
        
        #context menus
        self.init_context()
        
        #layout
        self.masterlayout.addWidget(self.tabw)
        self.masterlayout.addWidget(self.statusw)
        
        #signals..
        self.connect(self.mactions["notifications"], SIGNAL("triggered()"), self.slotShowNotificationOptions)
        self.connect(self.mactions["logging"], SIGNAL("triggered()"), self.slotShowLoggingOptions)
        self.connect(self.mactions["cnlfwding"], SIGNAL("triggered()"), self.slotShowClickNLoadForwarderOptions)
        self.connect(self.mactions["autoreloading"], SIGNAL("triggered()"), self.slotShowAutomaticReloadingOptions)
        self.connect(self.mactions["captcha"], SIGNAL("triggered()"), self.slotShowCaptchaOptions)
        self.connect(self.mactions["fonts"], SIGNAL("triggered()"), self.slotShowFontOptions)
        self.connect(self.mactions["tray"], SIGNAL("triggered()"), self.slotShowTrayOptions)
        self.connect(self.mactions["whatsthis"], SIGNAL("triggered()"), self.slotShowWhatsThisOptions)
        self.connect(self.mactions["other"], SIGNAL("triggered()"), self.slotShowOtherOptions)
        self.connect(self.mactions["language"], SIGNAL("triggered()"), self.slotShowLanguageOptions)
        self.connect(self.mactions["manager"], SIGNAL("triggered()"), self.slotShowConnector)
        self.connect(self.mactions["coreperms"], SIGNAL("triggered()"), self.slotShowCorePermissions)
        self.connect(self.mactions["quitcore"], SIGNAL("triggered()"), self.slotQuitCore)
        self.connect(self.mactions["restartcore"], SIGNAL("triggered()"), self.slotRestartCore)
        self.connect(self.mactions["reload"], SIGNAL("triggered()"), self.slotReload)
        self.connect(self.mactions["showcaptcha"], SIGNAL("triggered()"), self.slotShowCaptcha)
        self.connect(self.mactions["showtoolbar"], SIGNAL("toggled(bool)"), self.slotToggleToolbar)
        self.connect(self.mactions["showspeedlimit"], SIGNAL("toggled(bool)"), self.slotToggleSpeedLimitVisibility)
        self.connect(self.mactions["whatsthismode"], SIGNAL("triggered()"), QWhatsThis.enterWhatsThisMode)
        self.connect(self.mactions["about"], SIGNAL("triggered()"), self.slotShowAbout)
        
        self.connect(self.tabs["queue"]["view"], SIGNAL('customContextMenuRequested(const QPoint &)'), self.slotQueueContextMenu)
        self.connect(self.tabs["collector"]["view"], SIGNAL('customContextMenuRequested(const QPoint &)'), self.slotCollectorContextMenu)
        self.connect(self.tabs["accounts"]["view"], SIGNAL('customContextMenuRequested(const QPoint &)'), self.slotAccountContextMenu)
        
        self.connect(self.tabw, SIGNAL("currentChanged(int)"), self.slotTabChanged)
    
    def setCorePermissions(self, corePermissions):
        self.corePermissions = corePermissions
        
        self.tabs["queue"]["view"].setCorePermissions(corePermissions)
        self.tabs["queue"]["w"].setEnabled(corePermissions["LIST"])
        self.tabs["overview"]["w"].setEnabled(corePermissions["LIST"])
        self.tabs["collector"]["view"].setCorePermissions(corePermissions)
        self.tabs["collector"]["w"].setEnabled(corePermissions["LIST"])
        self.mactions["reload"].setEnabled(corePermissions["LIST"])         # main menu entry: View -> Reload
        self.mactions["autoreloading"].setEnabled(corePermissions["LIST"])  # main menu entry: Options -> Automatic Reloading
        
        self.tabs["queue"]["b"].setEnabled(corePermissions["MODIFY"])
        self.tabs["collector"]["b"].setEnabled(corePermissions["MODIFY"])
        self.actions["restart_failed"].setEnabled(corePermissions["MODIFY"])
        # Api.setPackageData
        self.newPackDock.widget.passwordLabel.setEnabled(corePermissions["MODIFY"])
        self.newPackDock.widget.passwordInput.setEnabled(corePermissions["MODIFY"])
        
        # Api.addFiles
        self.newLinkDock.widget.setEnabled(corePermissions["ADD"])
        self.actions["add_links"].setEnabled(corePermissions["ADD"])
        # Api.addPackage
        self.newPackDock.widget.setEnabled(corePermissions["ADD"])
        self.actions["add_package"].setEnabled(corePermissions["ADD"])
        if not corePermissions["ADD"]:
            self.actions["clipboard"].setChecked(False)
            self.actions["clipboard"].setEnabled(False)
        # Api.uploadContainer
        self.actions["add_container"].setEnabled(corePermissions["ADD"])
        # Context menu 'Add' entry
        self.queueContext.buttons["add"].setEnabled(corePermissions["ADD"])
        self.collectorContext.buttons["add"].setEnabled(corePermissions["ADD"])
        
        # Api.deleteFinished
        self.actions["remove_finished"].setEnabled(corePermissions["DELETE"])
        
        # Api.pauseServer and Api.unpauseServer
        self.actions["toggle_status"].setEnabled(corePermissions["STATUS"])
        
        # Api.getCaptchaTask, Api.getCaptchaTaskStatus, Api.isCaptchaWaiting and Api.setCaptchaResult
        self.mactions["captcha"].setEnabled(corePermissions["STATUS"])  # main menu entry: Options -> Captcha
        self.captchaDialog.setEnabled(corePermissions["STATUS"])
        
        # 'Abort All' toolbar button
        if not corePermissions["MODIFY"]:
            self.actions["status_stop"].setEnabled(False)
        elif not corePermissions["STATUS"]:
            self.actions["status_stop"].setIcon(self.statusStopIconNoPause)
            self.actions["status_stop"].setToolTip(_("Cannot set pause mode!"))
        
        # Speed Limit in toolbar
        if not corePermissions["SETTINGS"]:
            self.actions["speedlimit_enabled"].setEnabled(False)
            self.actions["speedlimit_rate"].setEnabled(False)
        
        # Server Settings Tab
        self.tabs["settings"]["w"].setCorePermissions(corePermissions)
        self.tabs["settings"]["w"].setEnabled(corePermissions["SETTINGS"])
        
        # Server Log
        if corePermissions["LOGS"]:
            self.tabs["corelog"]["text"].setText("")
        else:
            self.tabs["corelog"]["text"].setText(_("Insufficient server permissions."))
        self.tabs["corelog"]["text"].setEnabled(corePermissions["LOGS"])
        
        # Accounts Tab
        self.tabs["accounts"]["view"].setCorePermissions(corePermissions)
        self.tabs["accounts"]["w"].setEnabled(corePermissions["ACCOUNTS"])
        self.actions["add_account"].setEnabled(corePermissions["ACCOUNTS"])
        
        # Disable toolbar 'Add' button when all popup-menu entries are disabled
        disableAdd = True
        for act in self.addMenu.actions():
            if act.isSeparator():
                continue
            disableAdd = disableAdd and not act.isEnabled()
        self.actions["add"].setDisabled(disableAdd)
        
        # admin permissions
        if not corePermissions["admin"]:
            self.mactions["quitcore"].setEnabled(False)      # main menu entry: File -> Quit pyLoad Server
            self.mactions["restartcore"].setEnabled(False)   # main menu entry: File -> Restart pyLoad Server
    
    @classmethod
    def createPopupMenu(self):
        """
            disables default popup menu
        """
        return
    
    def init_toolbar(self):
        """
            create toolbar
        """
        self.toolbar = self.addToolBar("toolbar")
        self.connect(self.toolbar, SIGNAL("visibilityChanged(bool)"), self.slotToolbarVisibilityChanged)
        self.toolbar.setObjectName("Main Toolbar")
        self.toolbar.setIconSize(QSize(30,30))
        self.toolbar.setMovable(False)
        self.actions["toggle_status"] = self.toolbar.addAction("")
        self.actions["toggle_status"].setWhatsThis(whatsThisFormat(_("Toggle Pause"), _("When the server is in pause mode, no further downloads will be started. Ongoing downloads continue.")))
        self.toggleStatusIconPause = QIcon(join(pypath, "icons", "toolbar_pause.png"))
        self.toggleStatusIconStart = QIcon(join(pypath, "icons", "toolbar_start.png"))
        self.actions["toggle_status"].setIcon(self.toggleStatusIconStart)
        self.actions["toggle_status"].setCheckable(True)
        self.actions["toggle_status"].setChecked(False)
        self.actions["status_stop"] = self.toolbar.addAction("")
        self.actions["status_stop"].setWhatsThis(whatsThisFormat(_("Abort All"), _("Aborts all ongoing downloads and sets the server to pause mode.")))
        self.statusStopIcon = QIcon(join(pypath, "icons", "toolbar_stop.png"))
        self.statusStopIconNoPause = QIcon(join(pypath, "icons", "toolbar_stop_nopause.png"))
        self.actions["status_stop"].setIcon(self.statusStopIcon)
        self.toolbar.addSeparator()
        self.actions["add"] = self.toolbar.addAction(QIcon(join(pypath, "icons", "toolbar_add.png")), "")
        self.actions["add"].setWhatsThis(whatsThisFormat(_("Add"), _("- Create a new package<br>- Add links to an existing package<br>- Add a container file to the Queue<br>- Add an account")))
        self.toolbar.addSeparator()
        self.actions["clipboard"] = self.toolbar.addAction(QIcon(join(pypath, "icons", "clipboard.png")), "")
        self.actions["clipboard"].setWhatsThis(whatsThisFormat(_("Check Clipboard"), _("Watches the clipboard, extracts URLs from copied text and creates a package with the URLs in the Collector.")))
        self.actions["clipboard"].setCheckable(True)
        stretch1 = QWidget()
        stretch1.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.toolbar.addWidget(stretch1)
        whatsThis = (_("Download Speed Limit in kb/s"), _("This is just a shortcut to:") + "<br>" + _("Server Settings") + " -> General -> Download")
        self.toolbar_speedLimit_enabled = QCheckBox(_("Speed"))
        self.toolbar_speedLimit_enabled.setWhatsThis(whatsThisFormat(*whatsThis))
        self.toolbar_speedLimit_rate = SpinBox()
        self.toolbar_speedLimit_rate.setWhatsThis(whatsThisFormat(*whatsThis))
        self.toolbar_speedLimit_rate.setMinimum(0)
        self.toolbar_speedLimit_rate.setMaximum(999999)
        self.actions["speedlimit_enabled"] = self.toolbar.addWidget(self.toolbar_speedLimit_enabled)
        self.actions["speedlimit_rate"] = self.toolbar.addWidget(self.toolbar_speedLimit_rate)
        self.actions["speedlimit_rate"].setEnabled(False)
        self.actions["speedlimit_enabled"].setEnabled(False)
        stretch2 = QWidget()
        stretch2.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.toolbar.addWidget(stretch2)
        whatsThis = (_("Captcha Button"), _("Indicates that a captcha is waiting to be solved. Click on the button to show the input dialog (if supported)."))
        self.toolbar_captcha = QPushButton()
        self.toolbar_captcha.setWhatsThis(whatsThisFormat(*whatsThis))
        f = self.font()
        f.setBold(True)
        self.toolbar_captcha.setFont(f)
        self.toolbar_captcha.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.actions["captcha"] = self.toolbar.addWidget(self.toolbar_captcha)
        self.actions["captcha"].setVisible(False)
        stretch3 = QWidget()
        stretch3.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.toolbar.addWidget(stretch3)
        self.actions["restart_failed"] = self.toolbar.addAction(QIcon(join(pypath, "icons", "toolbar_refresh.png")), "")
        self.actions["restart_failed"].setWhatsThis(whatsThisFormat(_("Restart Failed"), _("Restarts (resumes if supported) all failed, aborted and temporary offline downloads.")))
        self.actions["remove_finished"] = self.toolbar.addAction(QIcon(join(pypath, "icons", "toolbar_remove.png")), "")
        self.actions["remove_finished"].setWhatsThis(whatsThisFormat(_("Remove Finished"), _("Removes all finished downloads from the Queue and the Collector.")))
        self.connect(self.actions["toggle_status"], SIGNAL("toggled(bool)"), self.slotToggleStatus)
        self.connect(self.actions["clipboard"], SIGNAL("toggled(bool)"), self.slotToggleClipboard)
        self.connect(self.toolbar_speedLimit_enabled, SIGNAL("toggled(bool)"), self.slotSpeedLimitStatus)
        self.connect(self.toolbar_speedLimit_rate, SIGNAL("editingFinished()"), self.slotSpeedLimitRate)
        self.connect(self.toolbar_captcha, SIGNAL("clicked()"), self.slotCaptchaStatusButton)
        self.connect(self.actions["status_stop"], SIGNAL("triggered()"), self.slotStatusStop)
        self.connect(self.actions["restart_failed"], SIGNAL("triggered()"), self.slotRestartFailed)
        self.connect(self.actions["remove_finished"], SIGNAL("triggered()"), self.slotRemoveFinished)
        
        self.addMenu = QMenu()
        self.actions["add_package"] = self.addMenu.addAction(_("Package"))
        self.actions["add_links"] = self.addMenu.addAction(_("Links"))
        self.actions["add_container"] = self.addMenu.addAction(_("Container"))
        self.addMenu.addSeparator()
        self.actions["add_account"] = self.addMenu.addAction(_("Account"))
        self.connect(self.actions["add"], SIGNAL("triggered()"), self.slotAdd)
        self.connect(self.actions["add_package"], SIGNAL("triggered()"), self.slotShowAddPackage)
        self.connect(self.actions["add_links"], SIGNAL("triggered()"), self.slotShowAddLinks)
        self.connect(self.actions["add_container"], SIGNAL("triggered()"), self.slotShowAddContainer)
        self.connect(self.actions["add_account"], SIGNAL("triggered()"), self.slotNewAccount)
    
    def init_tabs(self, connector):
        """
            create tabs
        """
        #queue
        self.tabs["queue"]["b"] = QPushButton(_("Pull Out Selected Packages"))
        self.tabs["queue"]["b"].setIcon(QIcon(join(pypath, "icons", "pull_small.png")))
        self.tabs["queue"]["m"] = QLabel("<b>" + _("To drop the items in the order they were selected, hold the ALT key when releasing the mouse button!") + "</b>")
        lsp = self.tabs["queue"]["m"].sizePolicy()
        lsp.setHorizontalPolicy(QSizePolicy.Ignored)
        self.tabs["queue"]["m"].setSizePolicy(lsp)
        self.tabs["queue"]["l"] = QGridLayout()
        self.tabs["queue"]["w"].setLayout(self.tabs["queue"]["l"])
        self.tabs["queue"]["view"] = QueueView(self.corePermissions, connector)
        self.tabs["queue"]["l"].addWidget(self.tabs["queue"]["view"], 0, 0)
        self.tabs["queue"]["l"].addWidget(self.tabs["queue"]["b"], 1, 0)
        self.tabs["queue"]["l"].addWidget(self.tabs["queue"]["m"], 1, 0)
        self.tabs["queue"]["w"].adjustSize()
        self.tabs["queue"]["m"].setFixedHeight(self.tabs["queue"]["b"].height())
        self.tabs["queue"]["m"].hide()
        self.connect(self.tabs["queue"]["b"], SIGNAL("clicked()"), self.slotPullOutPackages)
        self.connect(self.tabs["queue"]["view"], SIGNAL("queueMsgShow"), self.slotQueueMsgShow)
        self.connect(self.tabs["queue"]["view"], SIGNAL("queueMsgHide"), self.slotQueueMsgHide)
        self.tabs["queue"]["view"].setContextMenuPolicy(Qt.CustomContextMenu)
        
        #overview
        self.tabs["overview"]["l"] = QGridLayout()
        self.tabs["overview"]["w"].setLayout(self.tabs["overview"]["l"])
        self.tabs["overview"]["view"] = OverviewView(self.tabs["queue"]["view"].model)
        self.tabs["overview"]["l"].addWidget(self.tabs["overview"]["view"])
        
        #collector
        self.tabs["collector"]["b"] = QPushButton(_("Push Selected Packages to Queue"))
        self.tabs["collector"]["b"].setIcon(QIcon(join(pypath, "icons", "push_small.png")))
        self.tabs["collector"]["m"] = QLabel("<b>" + _("To drop the items in the order they were selected, hold the ALT key when releasing the mouse button!") + "</b>")
        lsp = self.tabs["collector"]["m"].sizePolicy()
        lsp.setHorizontalPolicy(QSizePolicy.Ignored)
        self.tabs["collector"]["m"].setSizePolicy(lsp)
        self.tabs["collector"]["l"] = QGridLayout()
        self.tabs["collector"]["w"].setLayout(self.tabs["collector"]["l"])
        self.tabs["collector"]["view"] = CollectorView(self.corePermissions, connector)
        self.tabs["collector"]["l"].addWidget(self.tabs["collector"]["view"], 0, 0)
        self.tabs["collector"]["l"].addWidget(self.tabs["collector"]["b"], 1, 0)
        self.tabs["collector"]["l"].addWidget(self.tabs["collector"]["m"], 1, 0)
        self.tabs["collector"]["w"].adjustSize()
        self.tabs["collector"]["m"].setFixedHeight(self.tabs["collector"]["b"].height())
        self.tabs["collector"]["m"].hide()
        self.connect(self.tabs["collector"]["b"], SIGNAL("clicked()"), self.slotPushPackagesToQueue)
        self.connect(self.tabs["collector"]["view"], SIGNAL("collectorMsgShow"), self.slotCollectorMsgShow)
        self.connect(self.tabs["collector"]["view"], SIGNAL("collectorMsgHide"), self.slotCollectorMsgHide)
        self.tabs["collector"]["view"].setContextMenuPolicy(Qt.CustomContextMenu)
        
        #gui log
        self.tabs["guilog"]["l"] = QGridLayout()
        self.tabs["guilog"]["w"].setLayout(self.tabs["guilog"]["l"])
        self.tabs["guilog"]["text"] = QTextEdit()
        self.tabs["guilog"]["text"].setLineWrapMode(QTextEdit.NoWrap)
        self.tabs["guilog"]["text"].logOffset = 0
        self.tabs["guilog"]["text"].setReadOnly(True)
        self.connect(self.tabs["guilog"]["text"], SIGNAL("append(QString)"), self.tabs["guilog"]["text"].append)
        self.tabs["guilog"]["l"].addWidget(self.tabs["guilog"]["text"])
        
        #core log
        self.tabs["corelog"]["l"] = QGridLayout()
        self.tabs["corelog"]["w"].setLayout(self.tabs["corelog"]["l"])
        self.tabs["corelog"]["text"] = QTextEdit()
        self.tabs["corelog"]["text"].setLineWrapMode(QTextEdit.NoWrap)
        self.tabs["corelog"]["text"].logOffset = 0
        self.tabs["corelog"]["text"].setReadOnly(True)
        self.connect(self.tabs["corelog"]["text"], SIGNAL("append(QString)"), self.tabs["corelog"]["text"].append)
        self.tabs["corelog"]["l"].addWidget(self.tabs["corelog"]["text"])
        
        #accounts
        self.tabs["accounts"]["view"] = AccountView(self.corePermissions, connector)
        self.tabs["accounts"]["w"].setLayout(QVBoxLayout())
        self.tabs["accounts"]["w"].layout().addWidget(self.tabs["accounts"]["view"])
        self.tabs["accounts"]["b"] = QPushButton(_("New Account"))
        self.tabs["accounts"]["w"].layout().addWidget(self.tabs["accounts"]["b"])
        self.connect(self.tabs["accounts"]["b"], SIGNAL("clicked()"), self.slotNewAccount)
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
        self.queueContext.buttons["pull"] = QAction(QIcon(join(pypath, "icons", "pull_small.png")), _("Pull Out"), self.queueContext)
        self.queueContext.buttons["edit"] = QAction(QIcon(join(pypath, "icons", "edit_small.png")), _("Edit"), self.queueContext)
        self.queueContext.buttons["abort"] = QAction(QIcon(join(pypath, "icons", "abort_small.png")), _("Abort"), self.queueContext)
        self.queueContext.buttons["restart"] = QAction(QIcon(join(pypath, "icons", "refresh_small.png")), _("Restart"), self.queueContext)
        self.queueContext.buttons["remove"] = QAction(QIcon(join(pypath, "icons", "remove_small.png")), _("Remove"), self.queueContext)
        self.queueContext.buttons["selectallpacks"] = QAction(_("Select All Packages"), self.queueContext)
        self.queueContext.buttons["deselectall"] = QAction(_("Deselect All"), self.queueContext)
        self.queueContext.buttons["expand"] = QAction(self.style().standardIcon(QStyle.SP_ToolBarHorizontalExtensionButton), _("Expand All"), self.queueContext)
        self.queueContext.buttons["collapse"] = QAction(self.style().standardIcon(QStyle.SP_ToolBarVerticalExtensionButton), _("Collapse All"), self.queueContext)
        self.queueContext.addAction(self.queueContext.buttons["pull"])
        self.queueContext.addSeparator()
        self.queueContext.buttons["add"] = self.queueContext.addMenu(QIcon(join(pypath, "icons", "add_small.png")), _("Add"))
        self.queueContext.buttons["add_package"] = self.queueContext.buttons["add"].addAction(_("Package"))
        self.queueContext.buttons["add_links"] = self.queueContext.buttons["add"].addAction(_("Links"))
        self.queueContext.buttons["add_container"] = self.queueContext.buttons["add"].addAction(_("Container"))
        self.queueContext.addAction(self.queueContext.buttons["edit"])
        self.queueContext.addAction(self.queueContext.buttons["abort"])
        self.queueContext.addAction(self.queueContext.buttons["restart"])
        self.queueContext.addSeparator()
        self.queueContext.addAction(self.queueContext.buttons["remove"])
        self.queueContext.addSeparator()
        self.queueContext.addAction(self.queueContext.buttons["selectallpacks"])
        self.queueContext.addAction(self.queueContext.buttons["deselectall"])
        self.queueContext.addSeparator()
        self.queueContext.addAction(self.queueContext.buttons["expand"])
        self.queueContext.addAction(self.queueContext.buttons["collapse"])
        self.connect(self.queueContext.buttons["pull"], SIGNAL("triggered()"), self.slotPullOutPackages)
        self.connect(self.queueContext.buttons["add_package"], SIGNAL("triggered()"), self.slotShowAddPackage)
        self.connect(self.queueContext.buttons["add_links"], SIGNAL("triggered()"), self.slotShowAddLinks)
        self.connect(self.queueContext.buttons["add_container"], SIGNAL("triggered()"), self.slotShowAddContainer)
        self.connect(self.queueContext.buttons["edit"], SIGNAL("triggered()"), self.slotEditPackages)
        self.connect(self.queueContext.buttons["abort"], SIGNAL("triggered()"), self.slotAbortDownloads)
        self.connect(self.queueContext.buttons["restart"], SIGNAL("triggered()"), self.slotRestartDownloads)
        self.connect(self.queueContext.buttons["remove"], SIGNAL("triggered()"), self.slotRemoveDownloads)
        self.connect(self.queueContext.buttons["selectallpacks"], SIGNAL("triggered()"), self.slotSelectAllPackages)
        self.connect(self.queueContext.buttons["deselectall"], SIGNAL("triggered()"), self.slotDeselectAll)
        self.connect(self.queueContext.buttons["expand"], SIGNAL("triggered()"), self.slotExpandAll)
        self.connect(self.queueContext.buttons["collapse"], SIGNAL("triggered()"), self.slotCollapseAll)
        
        #collector
        self.collectorContext = QMenu()
        self.collectorContext.buttons = {}
        self.collectorContext.item = (None, None)
        self.collectorContext.buttons["push"] = QAction(QIcon(join(pypath, "icons", "push_small.png")), _("Push to Queue"), self.collectorContext)
        self.collectorContext.buttons["edit"] = QAction(QIcon(join(pypath, "icons", "edit_small.png")), _("Edit"), self.collectorContext)
        self.collectorContext.buttons["abort"] = QAction(QIcon(join(pypath, "icons", "abort_small.png")), _("Abort"), self.collectorContext)
        self.collectorContext.buttons["restart"] = QAction(QIcon(join(pypath, "icons", "refresh_small.png")), _("Restart"), self.collectorContext)
        self.collectorContext.buttons["remove"] = QAction(QIcon(join(pypath, "icons", "remove_small.png")), _("Remove"), self.collectorContext)
        self.collectorContext.buttons["selectallpacks"] = QAction(_("Select All Packages"), self.collectorContext)
        self.collectorContext.buttons["deselectall"] = QAction(_("Deselect All"), self.collectorContext)
        self.collectorContext.buttons["expand"] = QAction(self.style().standardIcon(QStyle.SP_ToolBarHorizontalExtensionButton), _("Expand All"), self.collectorContext)
        self.collectorContext.buttons["collapse"] = QAction(self.style().standardIcon(QStyle.SP_ToolBarVerticalExtensionButton), _("Collapse All"), self.collectorContext)
        self.collectorContext.addAction(self.collectorContext.buttons["push"])
        self.collectorContext.addSeparator()
        self.collectorContext.buttons["add"] = self.collectorContext.addMenu(QIcon(join(pypath, "icons", "add_small.png")), _("Add"))
        self.collectorContext.buttons["add_package"] = self.collectorContext.buttons["add"].addAction(_("Package"))
        self.collectorContext.buttons["add_links"] = self.collectorContext.buttons["add"].addAction(_("Links"))
        self.collectorContext.addAction(self.collectorContext.buttons["edit"])
        self.collectorContext.addAction(self.collectorContext.buttons["abort"])
        self.collectorContext.addAction(self.collectorContext.buttons["restart"])
        self.collectorContext.addSeparator()
        self.collectorContext.addAction(self.collectorContext.buttons["remove"])
        self.collectorContext.addSeparator()
        self.collectorContext.addAction(self.collectorContext.buttons["selectallpacks"])
        self.collectorContext.addAction(self.collectorContext.buttons["deselectall"])
        self.collectorContext.addSeparator()
        self.collectorContext.addAction(self.collectorContext.buttons["expand"])
        self.collectorContext.addAction(self.collectorContext.buttons["collapse"])
        self.connect(self.collectorContext.buttons["push"], SIGNAL("triggered()"), self.slotPushPackagesToQueue)
        self.connect(self.collectorContext.buttons["add_package"], SIGNAL("triggered()"), self.slotShowAddPackage)
        self.connect(self.collectorContext.buttons["add_links"], SIGNAL("triggered()"), self.slotShowAddLinks)
        self.connect(self.collectorContext.buttons["edit"], SIGNAL("triggered()"), self.slotEditPackages)
        self.connect(self.collectorContext.buttons["abort"], SIGNAL("triggered()"), self.slotAbortDownloads)
        self.connect(self.collectorContext.buttons["restart"], SIGNAL("triggered()"), self.slotRestartDownloads)
        self.connect(self.collectorContext.buttons["remove"], SIGNAL("triggered()"), self.slotRemoveDownloads)
        self.connect(self.collectorContext.buttons["selectallpacks"], SIGNAL("triggered()"), self.slotSelectAllPackages)
        self.connect(self.collectorContext.buttons["deselectall"], SIGNAL("triggered()"), self.slotDeselectAll)
        self.connect(self.collectorContext.buttons["expand"], SIGNAL("triggered()"), self.slotExpandAll)
        self.connect(self.collectorContext.buttons["collapse"], SIGNAL("triggered()"), self.slotCollapseAll)
        
        #accounts
        self.accountContext = QMenu()
        self.accountContext.buttons = {}
        self.accountContext.buttons["add"] = QAction(QIcon(join(pypath, "icons", "add_small.png")), _("Add"), self.accountContext)
        self.accountContext.buttons["edit"] = QAction(QIcon(join(pypath, "icons", "edit_small.png")), _("Edit"), self.accountContext)
        self.accountContext.buttons["remove"] = QAction(QIcon(join(pypath, "icons", "remove_small.png")), _("Remove"), self.accountContext)
        self.accountContext.addAction(self.accountContext.buttons["add"])
        self.accountContext.addAction(self.accountContext.buttons["edit"])
        self.accountContext.addAction(self.accountContext.buttons["remove"])
        self.connect(self.accountContext.buttons["add"], SIGNAL("triggered()"), self.slotNewAccount)
        self.connect(self.accountContext.buttons["edit"], SIGNAL("triggered()"), self.slotEditAccount)
        self.connect(self.accountContext.buttons["remove"], SIGNAL("triggered()"), self.slotRemoveAccount)
    
    def initEventHooks(self):
        self.eD = {}
        self.eD["pCount"] = int(0)
        self.eD["lastGeo"] = QRect(10000000, 10000000, 10000000, 10000000)
        self.eD["lastNormPos"] = self.eD["lastNormSize"] = self.eD["2ndLastNormPos"] = self.eD["2ndLastNormSize"] = None
        self.eD["pLastMax"] = self.eD["pSignal"] = self.eD["pStateSig"] = False
    
    def paintEvent(self, event):
        if self.eD["pStateSig"]:
            self.emit(SIGNAL("mainWindowState"))
        self.eD["pCount"] += 1
        self.log.debug3("MainWindow.paintEvent:  at %08d msec   cnt: %04d   rect: x:%04d y:%04d w:%04d h:%04d" % (self.time_msec(), self.eD["pCount"], event.rect().x(), event.rect().y(), event.rect().width(), event.rect().height()))
        maximized = bool(self.windowState() & Qt.WindowMaximized)
        minimized = bool(self.windowState() & Qt.WindowMinimized)
        if not (maximized or minimized):
            pos = self.pos()
            if pos != self.eD["lastNormPos"]:
                self.eD["2ndLastNormPos"] = self.eD["lastNormPos"]
                self.eD["lastNormPos"] = pos
            size = self.size()
            if size != self.eD["lastNormSize"]:
                self.eD["2ndLastNormSize"] = self.eD["lastNormSize"]
                self.eD["lastNormSize"] = size
        if self.eD["pSignal"]:
            self.eD["pSignal"] = False
            self.emit(SIGNAL("mainWindowPaintEvent"))
        geo = self.geometry()
        if (geo.topLeft() != self.moveEventPos) or (geo.size() != self.resizeEventSize):
            self.log.debug3("MainWindow.paintEvent: Bad geometry")
            return
        if (geo.topLeft() == self.eD["lastGeo"].topLeft()) or (geo.size() == self.eD["lastGeo"].size()):
            return
        # got new geometry, size and position
        if maximized == self.eD["pLastMax"]:
            return
        # got maximize flag toggled
        if maximized:
            if self.log.isEnabledFor(logging.DEBUG3):
                self.log.debug3("MainWindow.paintEvent: maximized\t\t(%04d, %04d)\t\t\t(%04d, %04d)\t\t[geo]" % (geo.topLeft().x(), geo.topLeft().y(), geo.size().width(), geo.size().height()))
                mrogeo = QRect(self.moveEventOldPos, self.resizeEventOldSize)
                self.log.debug3("MainWindow.paintEvent:          \t\t(%04d, %04d)\t\t\t(%04d, %04d)\t\t[mrogeo]" % (mrogeo.topLeft().x(), mrogeo.topLeft().y(), mrogeo.size().width(), mrogeo.size().height()))
        else:
            self.log.debug3("MainWindow.paintEvent: unmaximized\t(%04d, %04d)\t\t\t(%04d, %04d)\t\t[geo]" % (geo.topLeft().x(), geo.topLeft().y(), geo.size().width(), geo.size().height()))
        self.eD["lastGeo"] = geo
        self.eD["pLastMax"] = maximized
    
    def moveEvent(self, event):
        self.moveEventOldPos = event.oldPos()
        self.moveEventPos = event.pos()
        self.log.debug3("MainWindow.moveEvent:   at %08d msec \t\t(%04d, %04d) -> (%04d, %04d)\t----------------------------" % (self.time_msec(), event.oldPos().x(), event.oldPos().y(), event.pos().x(), event.pos().y()))
        maximized = bool(self.windowState() & Qt.WindowMaximized)
        minimized = bool(self.windowState() & Qt.WindowMinimized)
        if not (maximized or minimized):
            pos = self.pos()
            if pos != self.eD["lastNormPos"]:
                self.eD["2ndLastNormPos"] = self.eD["lastNormPos"]
                self.eD["lastNormPos"] = pos
    
    def resizeEvent(self, event):
        self.resizeEventOldSize = event.oldSize()
        self.resizeEventSize = event.size()
        self.log.debug3("MainWindow.resizeEvent: at %08d msec \t\t----------------------------\t(%04d, %04d) -> (%04d, %04d)\t" % (self.time_msec(), event.oldSize().width(), event.oldSize().height(), event.size().width(), event.size().height()))
    
    def changeEvent(self, event):
        if (event.type() == QEvent.WindowStateChange):
            if (self.windowState() & Qt.WindowMinimized):
                if not (event.oldState() & Qt.WindowMinimized):
                    self.emit(SIGNAL("minimizeToggled"), True)
            elif (event.oldState() & Qt.WindowMinimized):
                self.emit(SIGNAL("minimizeToggled"), False)
            if (self.windowState() & Qt.WindowMaximized):
                if not (event.oldState() & Qt.WindowMaximized):
                    self.emit(SIGNAL("maximizeToggled"), True)
            elif (event.oldState() & Qt.WindowMaximized):
                self.emit(SIGNAL("maximizeToggled"), False)
    
    def closeEvent(self, event):
        """
            somebody wants to close me!
        """
        event.ignore()
        self.emit(SIGNAL("mainWindowClose"))
    
    def urlFilter(self, text):
        pattern = re.compile(ur'(?i)\b(((?:ht|f)tps?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:\'".,<>?\xab\xbb\u201c\u201d\u2018\u2019]))')
        text += " "
        lines = text.split()
        urlList = []
        for line in lines:
            urls = [ match[0] for match in pattern.findall(line) ]
            if urls:
                for u in urls:
                    s = u.strip(" ")
                    if not s in urlList:
                        urlList.append(s)
        return urlList
    
    def slotShowAbout(self):
        """
            show the about-box
        """
        self.emit(SIGNAL("showAbout"))
    
    def slotQueueMsgShow(self):
        """
            emitted from queue view, show message label instead of pull button
        """
        self.tabs["queue"]["m"].setFixedHeight(self.tabs["queue"]["b"].height())
        self.tabs["queue"]["m"].show()
        self.tabs["queue"]["b"].hide()
    
    def slotQueueMsgHide(self):
        """
            emitted from queue view, show pull button
        """
        self.tabs["queue"]["m"].hide()
        self.tabs["queue"]["b"].show()
    
    def slotCollectorMsgShow(self):
        """
            emitted from collector view, show message label instead of push button
        """
        self.tabs["collector"]["m"].setFixedHeight(self.tabs["collector"]["b"].height())
        self.tabs["collector"]["m"].show()
        self.tabs["collector"]["b"].hide()
    
    def slotCollectorMsgHide(self):
        """
            emitted from collector view, show push button
        """
        self.tabs["collector"]["m"].hide()
        self.tabs["collector"]["b"].show()
    
    def slotToolbarVisibilityChanged(self, visible):
        """
            set the toolbar checkbox in view-menu (mainmenu)
        """
        self.mactions["showtoolbar"].setChecked(visible)
        self.mactions["showspeedlimit"].setEnabled(visible) # disable/greyout menu entry
    
    def slotToggleToolbar(self, checked):
        """
            toggle from view-menu (mainmenu)
            show/hide toolbar
        """
        self.toolbar.setVisible(checked)
    
    def slotToggleSpeedLimitVisibility(self, checked):
        """
            toggle from view-menu (mainmenu)
            show/hide download speed limit
        """
        self.log.debug9("slotToggleSpeedLimitVisibility: toggled: %s" % str(checked))
        self.actions["speedlimit_enabled"].setEnabled(False)
        self.actions["speedlimit_enabled"].setVisible(checked)
        self.actions["speedlimit_rate"].setEnabled(False)
        self.actions["speedlimit_rate"].setVisible(checked)
    
    def slotReload(self):
        """
            from view-menu (mainmenu)
            force reload queue and collector tab
        """
        self.emit(SIGNAL("reloadQueue"))
        self.emit(SIGNAL("reloadCollector"))
    
    def slotShowCaptcha(self):
        """
            from view-menu (mainmenu)
            show captcha
        """
        self.emit(SIGNAL("showCaptcha"))
    
    def slotToggleStatus(self, status):
        """
            pause/start toggle (toolbar)
        """
        if status:
            self.actions["toggle_status"].setIcon(self.toggleStatusIconPause)
        else:
            self.actions["toggle_status"].setIcon(self.toggleStatusIconStart)
        self.emit(SIGNAL("setDownloadStatus"), status)
    
    def slotStatusStop(self):
        """
            stop button (toolbar)
        """
        self.emit(SIGNAL("stopAllDownloads"))
    
    def slotRestartFailed(self):
        """
            restart failed button (toolbar)
            let main to the stuff
        """
        self.emit(SIGNAL("restartFailed"))
    
    def slotRemoveFinished(self):
        """
            remove finished button (toolbar)
            let main to the stuff
        """
        self.emit(SIGNAL("deleteFinished"))
    
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
        self.emit(SIGNAL("showAddPackage"))
    
    def slotShowAddLinks(self):
        """
            action from add-menu
            show new-links dock
        """
        self.emit(SIGNAL("showAddLinks"))
    
    def slotShowConnector(self):
        """
            connection manager action triggered
            let main to the stuff
        """
        self.emit(SIGNAL("connector"))
    
    def slotShowCorePermissions(self):
        """
            core permissions action triggered
            let main to the stuff
        """
        self.emit(SIGNAL("showCorePermissions"))
    
    def slotQuitCore(self):
        """
            quit core action triggered
            let main to the stuff
        """
        self.emit(SIGNAL("quitCore"))
    
    def slotRestartCore(self):
        """
            restart core action triggered
            let main to the stuff
        """
        self.emit(SIGNAL("restartCore"))
    
    def slotParseUri(self, caller, text):
        """
            URI parser
            filters URIs out of text
        """
        urls = self.urlFilter(text)
        result = unicode("")
        for u in urls:
            result += u + "\n"
        if caller == "packagedock":
            self.newPackDock.parseUriResult(result)
        elif caller == "linkdock":
            self.newLinkDock.parseUriResult(result)
    
    def slotAddPackage(self, name, links, queue, password=None):
        """
            new package
            let main to the stuff
        """
        self.emit(SIGNAL("addPackage"), name, links, queue, password)
        
    def slotAddLinksToPackage(self, links, queue):
        """
            adds links to currently selected package
            let main to the stuff
        """
        self.emit(SIGNAL("addLinksToPackage"), links, queue)
    
    def slotShowAddContainer(self):
        """
            action from add-menu
            show file selector, emit upload
        """
        # native file dialog defined by OS, so better don't use language translating in typeStr
        typeStr = ";;".join([
            "All Container Types (%s)" % "*.dlc *.ccf *.rsdf *.txt",
            "DLC (%s)" % "*.dlc",
            "CCF (%s)" % "*.ccf",
            "RSDF (%s)" % "*.rsdf",
            "Text Files (%s)" % "*.txt"
        ])
        fileNames = QFileDialog.getOpenFileNames(self, "Open Container", self.lastAddContainerDir, typeStr)
        for name in fileNames:
            self.emit(SIGNAL("addContainer"), unicode(name))
        if not fileNames.isEmpty():
            self.lastAddContainerDir = unicode(dirname(unicode(name)))
    
    def slotPushPackagesToQueue(self):
        """
            push selected collector packages to queue
            let main do it
        """
        self.emit(SIGNAL("pushPackagesToQueue"))
    
    def slotQueueContextMenu(self, pos):
        """
            custom context menu in queue view requested
        """
        i = self.tabs["queue"]["view"].indexAt(pos)
        if not i:
            return
        item = i.internalPointer()
        menuPos = QCursor.pos()
        menuPos.setX(menuPos.x()+2)
        self.activeMenu = self.queueContext
        showAbort = False
        if isinstance(item, Link) and item.data["downloading"]:
            showAbort = self.corePermissions["MODIFY"]
        elif isinstance(item, Package):
            for child in item.children:
                if child.data["downloading"]:
                    showAbort = self.corePermissions["MODIFY"]
                    break
        if isinstance(item, Package):
            self.queueContext.index = i
            self.queueContext.buttons["pull"].setEnabled(self.corePermissions["MODIFY"])
            self.queueContext.buttons["add_links"].setEnabled(self.corePermissions["ADD"])
            self.queueContext.buttons["edit"].setEnabled(self.corePermissions["MODIFY"])
            self.queueContext.buttons["restart"].setEnabled(self.corePermissions["MODIFY"])
            self.queueContext.buttons["remove"].setEnabled(self.corePermissions["DELETE"])
        elif isinstance(item, Link):
            self.queueContext.index = i
            self.queueContext.buttons["pull"].setEnabled(False)
            self.queueContext.buttons["add_links"].setEnabled(False)
            self.queueContext.buttons["edit"].setEnabled(False)
            self.queueContext.buttons["restart"].setEnabled(self.corePermissions["MODIFY"])
            self.queueContext.buttons["remove"].setEnabled(self.corePermissions["DELETE"])
        else:
            self.queueContext.index = None
            self.queueContext.buttons["pull"].setEnabled(False)
            self.queueContext.buttons["add_links"].setEnabled(False)
            self.queueContext.buttons["edit"].setEnabled(False)
            self.queueContext.buttons["restart"].setEnabled(False)
            self.queueContext.buttons["remove"].setEnabled(False)
        self.queueContext.buttons["abort"].setEnabled(showAbort)
        self.queueContext.exec_(menuPos)
    
    def slotCollectorContextMenu(self, pos):
        """
            custom context menu in package collector view requested
        """
        i = self.tabs["collector"]["view"].indexAt(pos)
        if not i:
            return
        item = i.internalPointer()
        menuPos = QCursor.pos()
        menuPos.setX(menuPos.x()+2)
        self.activeMenu = self.collectorContext
        showAbort = False
        if isinstance(item, Link) and (item.data["status"] == DownloadStatus.Downloading):
            showAbort = self.corePermissions["MODIFY"]
        elif isinstance(item, Package):
            for child in item.children:
                if child.data["status"] == DownloadStatus.Downloading:
                    showAbort = self.corePermissions["MODIFY"]
                    break
        if isinstance(item, Package):
            self.collectorContext.index = i
            self.collectorContext.buttons["push"].setEnabled(self.corePermissions["MODIFY"])
            self.collectorContext.buttons["add_links"].setEnabled(self.corePermissions["ADD"])
            self.collectorContext.buttons["edit"].setEnabled(self.corePermissions["MODIFY"])
            self.collectorContext.buttons["restart"].setEnabled(self.corePermissions["MODIFY"])
            self.collectorContext.buttons["remove"].setEnabled(self.corePermissions["DELETE"])
        elif isinstance(item, Link):
            self.collectorContext.index = i
            self.collectorContext.buttons["push"].setEnabled(False)
            self.collectorContext.buttons["add_links"].setEnabled(False)
            self.collectorContext.buttons["edit"].setEnabled(False)
            self.collectorContext.buttons["restart"].setEnabled(self.corePermissions["MODIFY"])
            self.collectorContext.buttons["remove"].setEnabled(self.corePermissions["DELETE"])
        else:
            self.collectorContext.index = None
            self.collectorContext.buttons["push"].setEnabled(False)
            self.collectorContext.buttons["add_links"].setEnabled(False)
            self.collectorContext.buttons["edit"].setEnabled(False)
            self.collectorContext.buttons["restart"].setEnabled(False)
            self.collectorContext.buttons["remove"].setEnabled(False)
        self.collectorContext.buttons["abort"].setEnabled(showAbort)
        self.collectorContext.exec_(menuPos)
    
    def slotLinkCollectorContextMenu(self, pos):
        """
            custom context menu in link collector view requested
        """
        pass
    
    def slotRestartDownloads(self):
        """
            restart download action is triggered
        """
        self.emit(SIGNAL("restartDownloads"), self.activeMenu == self.queueContext)
    
    def slotRemoveDownloads(self):
        """
            remove download action is triggered
        """
        self.emit(SIGNAL("removeDownloads"), self.activeMenu == self.queueContext)
    
    def slotToggleClipboard(self, status):
        """
            check clipboard (toolbar)
        """
        self.emit(SIGNAL("setClipboardStatus"), status)
   
    def slotSpeedLimitStatus(self, status):
        """
            speed limit enable/disable checkbox (toolbar)
        """
        self.emit(SIGNAL("toolbarSpeedLimitEdited"))
    
    def slotSpeedLimitRate(self):
        """
            speed limit rate spinbox (toolbar)
        """
        self.toolbar_speedLimit_rate.lineEdit().deselect() # deselect any selected text
        self.emit(SIGNAL("toolbarSpeedLimitEdited"))
    
    def slotCaptchaStatusButton(self):
        """
            captcha status button (toolbar)
        """
        self.emit(SIGNAL("captchaStatusButton"))
    
    def slotEditPackages(self):
        """
            popup the package edit dialog
        """
        self.emit(SIGNAL("editPackages"), self.activeMenu == self.queueContext)
    
    def slotPullOutPackages(self):
        """
            pull selected packages out of the queue
            let main do it
        """
        self.emit(SIGNAL("pullOutPackages"))
    
    def slotAbortDownloads(self):
        """
            abort selected downloads
            let main do it
        """
        self.emit(SIGNAL("abortDownloads"), self.activeMenu == self.queueContext)
    
    def slotSelectAllPackages(self):
        """
            select all packages
            let main to the stuff
        """
        self.emit(SIGNAL("selectAllPackages"))
    
    def slotDeselectAll(self):
        """
            clear the selection
        """
        if self.activeMenu == self.queueContext:
            view = self.tabs["queue"]["view"]
        else:
            view = self.tabs["collector"]["view"]
        view.clearSelection()
        view.setCurrentIndex(QModelIndex())
    
    def slotExpandAll(self):
        """
            expand all tree view items
            let main to the stuff
        """
        self.emit(SIGNAL("expandAll"))
    
    def slotCollapseAll(self):
        """
            collapse all tree view items
            let main to the stuff
        """
        self.emit(SIGNAL("collapseAll"))
    
    def slotTabChanged(self, index):
        # currentIndex
        if index == 3:
            self.tabs["accounts"]["view"].model.reloadData()
            self.tabs["accounts"]["view"].model.timer.start(2000)
        else:
            self.tabs["accounts"]["view"].model.timer.stop()
        if index == 5:
            self.tabs["settings"]["w"].loadConfig()
        elif index == 1:
            if self.newPackDock.widget.destAutoSelect.isChecked():
                self.newPackDock.widget.destQueue.setChecked(True)
            if self.newLinkDock.widget.destAutoSelect.isChecked():
                self.newLinkDock.widget.destQueue.setChecked(True)
        elif index == 2:
            if self.newPackDock.widget.destAutoSelect.isChecked():
                self.newPackDock.widget.destCollector.setChecked(True)
            if self.newLinkDock.widget.destAutoSelect.isChecked():
                self.newLinkDock.widget.destCollector.setChecked(True)
    
    def slotNewAccount(self):
        if not self.corePermissions["ACCOUNTS"]:
            return
        
        types = self.connector.proxy.getAccountTypes()
        types = sorted(types, key=lambda p: p)
        self.accountEdit = AccountEdit.newAccount(self, types)
        
        #TODO make more easy n1, n2, n3 
        def save(data):
            if data["password"]:
                self.accountEdit.close()
                n1 = data["acctype"]
                n2 = data["login"]
                n3 = data["password"]
                self.connector.proxy.updateAccount(n1, n2, n3, None)
        
        self.accountEdit.connect(self.accountEdit, SIGNAL("done"), save)
        self.tabw.setCurrentIndex(3)
        self.accountEdit.exec_()

    def slotEditAccount(self):
        if not self.corePermissions["ACCOUNTS"]:
            return
        
        types = self.connector.proxy.getAccountTypes()
        types = sorted(types, key=lambda p: p)
        
        data = self.tabs["accounts"]["view"].model.getSelectedIndexes()
        if len(data) < 1:
            return
        
        data = data[0].internalPointer()
        
        self.accountEdit = AccountEdit.editAccount(self, types, data)
        
        #TODO make more easy n1, n2, n3
        #TODO reload accounts tab after insert of edit account
        #TODO if account does not exist give error
        def save(data):
            self.accountEdit.close()
            n1 = data["acctype"]
            n2 = data["login"]
            n3 = data["password"]
            self.connector.proxy.updateAccount(n1, n2, n3, None)
        
        self.accountEdit.connect(self.accountEdit, SIGNAL("done"), save)
        self.accountEdit.exec_()
    
    def slotRemoveAccount(self):
        if not self.corePermissions["ACCOUNTS"]:
            return
        
        data = self.tabs["accounts"]["view"].model.getSelectedIndexes()
        if len(data) < 1:
            return
            
        data = data[0].internalPointer()
        
        self.connector.proxy.removeAccount(data.type, data.login)
    
    def slotAccountContextMenu(self, pos):
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
    
    def slotShowLoggingOptions(self):
        self.emit(SIGNAL("showLoggingOptions"))
    
    def slotShowClickNLoadForwarderOptions(self):
        self.emit(SIGNAL("showClickNLoadForwarderOptions"))
    
    def slotShowAutomaticReloadingOptions(self):
        self.emit(SIGNAL("showAutomaticReloadingOptions"))
    
    def slotShowCaptchaOptions(self):
        self.emit(SIGNAL("showCaptchaOptions"))
    
    def slotShowFontOptions(self):
        self.emit(SIGNAL("showFontOptions"))
    
    def slotShowNotificationOptions(self):
        self.emit(SIGNAL("showNotificationOptions"))
    
    def slotShowTrayOptions(self):
        self.emit(SIGNAL("showTrayOptions"))
    
    def slotShowWhatsThisOptions(self):
        self.emit(SIGNAL("showWhatsThisOptions"))
    
    def slotShowOtherOptions(self):
        self.emit(SIGNAL("showOtherOptions"))
    
    def slotShowLanguageOptions(self):
        self.emit(SIGNAL("showLanguageOptions"))

class SpinBox(QSpinBox):
    """
        a spinbox that supports 'escape' key and loses focus when the 'enter' key is pressed
        for the toolbar speed limit setting
    """
    def __init__(self):
        QSpinBox.__init__(self)
        self.log = logging.getLogger("guilog")
    
    def focusInEvent(self, event):
        self.lastValue = self.value()
        QAbstractSpinBox.focusInEvent(self, event)
    
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.setValue(self.lastValue)
            self.clearFocus()
        elif event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
                self.clearFocus()
        QAbstractSpinBox.keyPressEvent(self, event)


