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

from module.gui.PyQtVersion import USE_PYQT5
if USE_PYQT5:
    from PyQt5.QtCore import pyqtSignal, QEvent, QPoint, QRect, QSize, Qt
    from PyQt5.QtGui import QColor, QCursor, QIcon
    from PyQt5.QtWidgets import (QAction, QActionGroup, QCheckBox, QFileDialog, QFrame, QGridLayout,
                                 QHBoxLayout, QLabel, QMainWindow, QMenu, QPushButton, QSizePolicy, QStyle,
                                 QTabWidget, QTextEdit, QVBoxLayout, QWhatsThis, QWidget)
else:
    from PyQt4.QtCore import pyqtSignal, QEvent, QPoint, QRect, QSize, Qt
    from PyQt4.QtGui import (QAction, QActionGroup, QCheckBox, QColor, QCursor, QFileDialog, QFrame, QGridLayout,
                             QHBoxLayout, QIcon, QLabel, QMainWindow, QMenu, QPushButton, QSizePolicy, QStyle,
                             QTabWidget, QTextEdit, QVBoxLayout, QWhatsThis, QWidget)

from os.path import join, dirname
from datetime import datetime

from module.gui.PackageDock import NewPackageDock
from module.gui.LinkDock import NewLinkDock
from module.gui.CaptchaDialog import CaptchaDialog
from module.gui.SettingsWidget import SettingsWidget
from module.gui.Collector import CollectorView
from module.gui.Queue import QueueView
from module.gui.AdvancedSelect import AdvancedSelect
from module.gui.Overview import OverviewView
from module.gui.Accounts import AccountView
from module.gui.AccountEdit import AccountEdit
from module.gui.Tools import whatsThisFormat, SpinBox

class MainWindow(QMainWindow):
    mainWindowStateSGL                   = pyqtSignal()
    mainWindowPaintEventSGL              = pyqtSignal()
    minimizeToggledSGL                   = pyqtSignal(object)
    maximizeToggledSGL                   = pyqtSignal(object)
    mainWindowCloseSGL                   = pyqtSignal()
    showAboutSGL                         = pyqtSignal()
    advancedSelectSGL                    = pyqtSignal(object, object)
    removePackageDupesSGL                = pyqtSignal()
    removeLinkDupesSGL                   = pyqtSignal()
    removeFinishedPackagesSGL            = pyqtSignal()
    reloadQueueSGL                       = pyqtSignal()
    reloadCollectorSGL                   = pyqtSignal()
    reloadAccountsSGL                    = pyqtSignal(object)
    showCaptchaFromMenuSGL               = pyqtSignal()
    setDownloadStatusSGL                 = pyqtSignal(object)
    stopAllDownloadsSGL                  = pyqtSignal()
    restartFailedSGL                     = pyqtSignal()
    removeAllFinishedPackagesSGL         = pyqtSignal()
    showAddPackageSGL                    = pyqtSignal()
    showAddLinksSGL                      = pyqtSignal()
    showConnectorSGL                     = pyqtSignal()
    showCorePermissionsSGL               = pyqtSignal()
    quitCoreSGL                          = pyqtSignal()
    restartCoreSGL                       = pyqtSignal()
    addPackageSGL                        = pyqtSignal(object, object, object, object)
    addLinksToPackageSGL                 = pyqtSignal(object, object)
    addContainerSGL                      = pyqtSignal(object)
    pushPackagesToQueueSGL               = pyqtSignal()
    restartDownloadsSGL                  = pyqtSignal(object)
    removeDownloadsSGL                   = pyqtSignal(object)
    toolbarSpeedLimitEditedSGL           = pyqtSignal()
    toolbarMaxParallelDownloadsEditedSGL = pyqtSignal()
    captchaStatusButtonSGL               = pyqtSignal()
    editPackagesSGL                      = pyqtSignal(object)
    pullOutPackagesSGL                   = pyqtSignal()
    abortDownloadsSGL                    = pyqtSignal(object)
    selectAllSGL                         = pyqtSignal()
    deselectAllSGL                       = pyqtSignal()
    selectAllPackagesSGL                 = pyqtSignal()
    deselectAllPackagesSGL               = pyqtSignal()
    sortPackagesSGL                      = pyqtSignal()
    sortLinksSGL                         = pyqtSignal()
    expandAllSGL                         = pyqtSignal()
    collapseAllSGL                       = pyqtSignal()
    menuPluginNotFoundSGL                = pyqtSignal(object)
    showLoggingOptionsSGL                = pyqtSignal()
    showClickNLoadForwarderOptionsSGL    = pyqtSignal()
    showAutomaticReloadingOptionsSGL     = pyqtSignal()
    showCaptchaOptionsSGL                = pyqtSignal()
    showIconThemeOptionsSGL              = pyqtSignal()
    showFontOptionsSGL                   = pyqtSignal()
    showColorFixOptionsSGL               = pyqtSignal()
    showNotificationOptionsSGL           = pyqtSignal()
    showTrayOptionsSGL                   = pyqtSignal()
    showWhatsThisOptionsSGL              = pyqtSignal()
    showOtherOptionsSGL                  = pyqtSignal()
    showLanguageOptionsSGL               = pyqtSignal()
    showPyQtVersionOptionsSGL            = pyqtSignal()

    def time_msec(self):
        return int((datetime.utcnow() - datetime(1970, 1, 1)).total_seconds() * 1000 - self.time_msec_init)

    def __init__(self, corePermissions, appIconSet, connector):
        """
            set up main window
        """
        self.time_msec_init = int((datetime.utcnow() - datetime(1970, 1, 1)).total_seconds() * 1000)
        QMainWindow.__init__(self)
        self.setEnabled(False)
        self.log = logging.getLogger("guilog")
        self.corePermissions = corePermissions
        self.appIconSet = appIconSet
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
        self.newPackDock = NewPackageDock(self.appIconSet)
        self.addDockWidget(Qt.RightDockWidgetArea, self.newPackDock)
        self.newPackDock.addPackageDoneSGL.connect(self.slotAddPackageDone)
        self.newPackDock.parseUriSGL.connect(self.slotParseUri)
        self.newLinkDock = NewLinkDock(self.appIconSet)
        self.addDockWidget(Qt.RightDockWidgetArea, self.newLinkDock)
        self.newLinkDock.addLinksToPackageDoneSGL.connect(self.slotAddLinksToPackageDone)
        self.newLinkDock.parseUriSGL.connect(self.slotParseUri)
        self.tabifyDockWidget(self.newPackDock, self.newLinkDock)
        self.captchaDialog = CaptchaDialog()

        #central widget, layout
        self.masterlayout = QVBoxLayout()
        lw = QWidget()
        lw.setLayout(self.masterlayout)
        self.setCentralWidget(lw)

        #treeview advanced select
        self.advselectframe = QFrame()
        self.advselectframe.hide()
        self.advselectframeQueueIsVisible = self.advselectframeCollectorIsVisible = False
        self.advselectframe.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        l = QVBoxLayout()
        self.advselect = AdvancedSelect()
        l.addWidget(self.advselect)
        self.advselectframe.setLayout(l)
        self.advselect.selectBtn.clicked.connect(self.slotAdvSelectSelectButtonClicked)
        self.advselect.deselectBtn.clicked.connect(self.slotAdvSelectDeselectButtonClicked)
        self.advselect.hideBtn.clicked.connect(self.slotAdvSelectHide)

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
            def __init__(self, lbl1text, wthis):
                QWidget.__init__(self)
                self.lbl1 = BoldLabel(lbl1text)
                self.lbl2 = QLabel("----")
                hbox = QHBoxLayout()
                hbox.setContentsMargins(0, 0, 0, 0)
                hbox.addStretch(1)
                hbox.addWidget(self.lbl1)
                hbox.addWidget(self.lbl2)
                hbox.addStretch(1)
                self.setLayout(hbox)
                self.setWhatsThis(wthis)

        self.statuswItems = {}
        self.statuswItems["packages"] = StwItem(_("Packages") + ":", whatsThisFormat(_("Packages"), _("The number of packages in the Queue.")))
        l.addWidget(self.statuswItems["packages"], 0, 0, 1, 1)
        self.statuswItems["links"] = StwItem(_("Links") + ":", whatsThisFormat(_("Links"), _("The number of links in the Queue.")))
        l.addWidget(self.statuswItems["links"], 0, 1, 1, 1)
        self.statuswItems["status"] = StwItem(_("Status") + ":", whatsThisFormat(_("Status"), _("The server status, 'Running' or 'Paused'.")))
        l.addWidget(self.statuswItems["status"], 0, 2, 1, 1)
        self.statuswItems["space"] = StwItem(_("Space") + ":", whatsThisFormat(_("Space"), _("The free space in the download folder.")))
        l.addWidget(self.statuswItems["space"], 0, 3, 1, 1)
        self.statuswItems["speed"] = StwItem(_("Speed") + ":", whatsThisFormat(_("Speed"), _("The actual download speed.")))
        l.addWidget(self.statuswItems["speed"], 0, 4, 1, 1)

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
                      "plugins": self.menubar.addMenu(_("Plugins")),
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
                         "icontheme": QAction(_("Icon Theme"), self.menus["options"]),
                         "fonts": QAction(_("Fonts"), self.menus["options"]),
                         "colorfix": QAction(_("Color Fix"), self.menus["options"]),
                         "tray": QAction(_("Tray Icon"), self.menus["options"]),
                         "whatsthis": QAction(_("What's This"), self.menus["options"]),
                         "other": QAction(_("Other"), self.menus["options"]),
                         "language": QAction(_("Language"), self.menus["options"]),
                         "pyqtversion": QAction(_("PyQt"), self.menus["options"]),
                         "reload": QAction(_("Reload Queue And Collector Data From Server"), self.menus["view"]),
                         "showcaptcha": QAction(_("Show Captcha"), self.menus["view"]),
                         "showtoolbar": QAction(_("Show Toolbar"), self.menus["view"]),
                         "showspeedlimit": QAction(_("Show Speed Limit"), self.menus["view"]),
                         "showmaxpadls": QAction(_("Show Max Parallel Downloads"), self.menus["view"]),
                         "whatsthismode": QAction("What's This?", self.menus["help"]),
                         "about": QAction(_("About pyLoad Client"), self.menus["help"])}
        self.mactions["showtoolbar"].setCheckable(True)
        self.mactions["showspeedlimit"].setCheckable(True)
        self.mactions["showspeedlimit"].setChecked(True)
        self.mactions["showmaxpadls"].setCheckable(True)
        self.mactions["showmaxpadls"].setChecked(True)

        #plugins menu actions
        self.pmactions = {}

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
        self.menus["options"].addAction(self.mactions["icontheme"])
        self.menus["options"].addAction(self.mactions["fonts"])
        self.menus["options"].addAction(self.mactions["colorfix"])
        self.menus["options"].addAction(self.mactions["tray"])
        self.menus["options"].addAction(self.mactions["whatsthis"])
        self.menus["options"].addAction(self.mactions["other"])
        self.menus["options"].addSeparator()
        self.menus["options"].addAction(self.mactions["language"])
        self.menus["options"].addAction(self.mactions["pyqtversion"])
        self.menus["view"].addAction(self.mactions["reload"])
        self.menus["view"].addAction(self.mactions["showcaptcha"])
        self.menus["view"].addSeparator()
        self.menus["view"].addAction(self.mactions["showtoolbar"])
        self.menus["view"].addAction(self.mactions["showspeedlimit"])
        self.menus["view"].addAction(self.mactions["showmaxpadls"])
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
        self.masterlayout.addWidget(self.advselectframe)
        self.masterlayout.addWidget(self.statusw)

        #signals..
        self.mactions["notifications"].triggered.connect(self.slotShowNotificationOptions)
        self.mactions["logging"].triggered.connect(self.slotShowLoggingOptions)
        self.mactions["cnlfwding"].triggered.connect(self.slotShowClickNLoadForwarderOptions)
        self.mactions["autoreloading"].triggered.connect(self.slotShowAutomaticReloadingOptions)
        self.mactions["captcha"].triggered.connect(self.slotShowCaptchaOptions)
        self.mactions["icontheme"].triggered.connect(self.slotShowIconThemeOptions)
        self.mactions["fonts"].triggered.connect(self.slotShowFontOptions)
        self.mactions["colorfix"].triggered.connect(self.slotShowColorFixOptions)
        self.mactions["tray"].triggered.connect(self.slotShowTrayOptions)
        self.mactions["whatsthis"].triggered.connect(self.slotShowWhatsThisOptions)
        self.mactions["other"].triggered.connect(self.slotShowOtherOptions)
        self.mactions["language"].triggered.connect(self.slotShowLanguageOptions)
        self.mactions["pyqtversion"].triggered.connect(self.slotShowPyQtVersionOptions)
        self.mactions["manager"].triggered.connect(self.slotShowConnector)
        self.mactions["coreperms"].triggered.connect(self.slotShowCorePermissions)
        self.mactions["quitcore"].triggered.connect(self.slotQuitCore)
        self.mactions["restartcore"].triggered.connect(self.slotRestartCore)
        self.mactions["reload"].triggered.connect(self.slotReload)
        self.mactions["showcaptcha"].triggered.connect(self.slotShowCaptchaFromMenu)
        self.mactions["showtoolbar"].toggled[bool].connect(self.slotToggleToolbar)
        self.mactions["showspeedlimit"].toggled[bool].connect(self.slotToggleSpeedLimitVisibility)
        self.mactions["showmaxpadls"].toggled[bool].connect(self.slotToggleMaxPaDlsVisibility)
        self.mactions["whatsthismode"].triggered.connect(QWhatsThis.enterWhatsThisMode)
        self.mactions["about"].triggered.connect(self.slotShowAbout)

        self.tabs["queue"]["view"].customContextMenuRequested[QPoint].connect(self.slotQueueContextMenu)
        self.tabs["collector"]["view"].customContextMenuRequested[QPoint].connect(self.slotCollectorContextMenu)
        self.tabs["accounts"]["view"].customContextMenuRequested[QPoint].connect(self.slotAccountContextMenu)
        self.tabs["settings"]["w"].setupPluginsMenuSGL.connect(self.slotSetupPluginsMenu)

        self.tabw.currentChanged[int].connect(self.slotTabChanged)

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
            self.actions["clipboard_queue"].setChecked(False)
            self.actions["clipboard_collector"].setChecked(False)
            self.actions["clipboard_packDock"].setChecked(False)
            self.actions["clipboard"].setChecked(False)
            self.actions["clipboard"].setEnabled(False)
        # Api.uploadContainer
        self.actions["add_container"].setEnabled(corePermissions["ADD"])
        # Context menu 'Add' entry
        self.queueContext.buttons["add"].setEnabled(corePermissions["ADD"])
        self.collectorContext.buttons["add"].setEnabled(corePermissions["ADD"])

        # Api.deletePackages
        self.actions["remove_finished_packages"].setEnabled(corePermissions["DELETE"])

        # Api.pauseServer and Api.unpauseServer
        self.actions["status_start"].setEnabled(corePermissions["STATUS"])
        self.actions["status_pause"].setEnabled(corePermissions["STATUS"])
        self.actions["status_start"].setCheckable(corePermissions["LIST"])
        self.actions["status_pause"].setCheckable(corePermissions["LIST"])

        # Api.getCaptchaTask, Api.getCaptchaTaskStatus, Api.isCaptchaWaiting and Api.setCaptchaResult
        self.mactions["captcha"].setEnabled(corePermissions["STATUS"])  # main menu entry: Options -> Captcha
        self.captchaDialog.setEnabled(corePermissions["STATUS"])

        # 'Abort All' toolbar button
        if not corePermissions["MODIFY"]:
            self.actions["status_stop"].setEnabled(False)
        elif not corePermissions["STATUS"]:
            self.actions["status_stop"].setIcon(self.statusStopIconNoPause)
            self.actions["status_stop"].setToolTip(_("Cannot set server status to 'Paused'"))

        # Speed Limit and Max Files in toolbar
        if not corePermissions["SETTINGS"]:
            self.actions["speedlimit_enabled"].setEnabled(False)
            self.actions["speedlimit_rate"].setEnabled(False)
            self.actions["maxparalleldownloads_label"].setEnabled(False)
            self.actions["maxparalleldownloads_value"].setEnabled(False)

        # Server Settings
        self.tabs["settings"]["w"].setCorePermissions(corePermissions)
        self.tabs["settings"]["w"].setEnabled(corePermissions["SETTINGS"])
        self.menus["plugins"].setEnabled(corePermissions["SETTINGS"])

        # Status bar
        self.statuswItems["packages"].setEnabled(corePermissions["LIST"])
        self.statuswItems["links"].setEnabled(corePermissions["LIST"])
        self.statuswItems["status"].setEnabled(corePermissions["LIST"])
        self.statuswItems["space"].setEnabled(corePermissions["STATUS"])
        self.statuswItems["speed"].setEnabled(corePermissions["LIST"])

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
        self.toolbar.visibilityChanged[bool].connect(self.slotToolbarVisibilityChanged)
        self.toolbar.setObjectName("Main Toolbar")
        self.toolbar.setIconSize(QSize(30,30))
        self.toolbar.setMovable(False)
        self.actions["status_start"] = self.toolbar.addAction(self.appIconSet["start"], "")
        wt = _("Resumes downloading the Queue.<br><br>Sets the server status to 'Running'.")
        self.actions["status_start"].setWhatsThis(whatsThisFormat(_("Resume Queue"), wt))
        self.actions["status_pause"] = self.toolbar.addAction(self.appIconSet["pause"], "")
        wt = _("Proceeds with ongoing downloads.<br>Starts no further downloads.<br><br>Sets the server status to 'Paused'.")
        self.actions["status_pause"].setWhatsThis(whatsThisFormat(_("Pause Queue"), wt))
        self.actions["status_stop"] = self.toolbar.addAction("")
        wt = _("Aborts all ongoing downloads.<br>Starts no further downloads.<br><br>Sets the server status to 'Paused'.")
        self.actions["status_stop"].setWhatsThis(whatsThisFormat(_("Abort Downloads"), wt))
        self.statusStopIcon = self.appIconSet["stop"]
        self.statusStopIconNoPause = self.appIconSet["stop_nopause"]
        self.actions["status_stop"].setIcon(self.statusStopIcon)
        self.startPauseActGrp = QActionGroup(self.toolbar)
        self.startPauseActGrp.addAction(self.actions["status_start"])
        self.startPauseActGrp.addAction(self.actions["status_pause"])
        self.toolbar.addSeparator()
        self.actions["add"] = self.toolbar.addAction(self.appIconSet["add"], "")
        wt = _("- Create a new package<br>- Add links to an existing package<br>- Add a container file to the Queue<br>- Add an account")
        self.actions["add"].setWhatsThis(whatsThisFormat(_("Add"), wt))
        self.toolbar.addSeparator()
        self.actions["clipboard"] = self.toolbar.addAction(self.appIconSet["clipboard"], "")
        wt = _("Watches the clipboard, extracts URLs from copied text and creates a package with the URLs or adds the URLs to the New Package Window.")
        self.actions["clipboard"].setWhatsThis(whatsThisFormat(_("Clipboard Watcher"), wt))
        self.actions["clipboard"].setCheckable(True)
        stretch1 = QWidget()
        stretch1.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.toolbar.addWidget(stretch1)
        whatsThis = (_("Limit Download Speed") + "<br>" + _("Max Download Speed in kb/s"),
                     _("This is just a shortcut to:") + "<br>" + _("Server Settings") + " -> General -> Download")
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
        stretch1b = QWidget()
        stretch1b.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.toolbar.addWidget(stretch1b)
        whatsThis = (_("Max Parallel Downloads"), _("This is just a shortcut to:") + "<br>" + _("Server Settings") + " -> General -> Download")
        self.toolbar_maxParallelDownloads_label = QLabel(_("MaxPaDls"))
        self.toolbar_maxParallelDownloads_label.setFocusPolicy(Qt.ClickFocus)
        self.toolbar_maxParallelDownloads_label.setWhatsThis(whatsThisFormat(*whatsThis))
        self.toolbar_maxParallelDownloads_value = SpinBox()
        self.toolbar_maxParallelDownloads_value.setWhatsThis(whatsThisFormat(*whatsThis))
        self.toolbar_maxParallelDownloads_value.setMinimum(0)
        self.toolbar_maxParallelDownloads_value.setMaximum(999999)
        self.actions["maxparalleldownloads_label"] = self.toolbar.addWidget(self.toolbar_maxParallelDownloads_label)
        self.actions["maxparalleldownloads_value"] = self.toolbar.addWidget(self.toolbar_maxParallelDownloads_value)
        self.actions["maxparalleldownloads_label"].setEnabled(False)
        self.actions["maxparalleldownloads_value"].setEnabled(False)
        stretch2 = QWidget()
        stretch2.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.toolbar.addWidget(stretch2)
        whatsThis = (_("Captcha Button"), _("Indicates that a captcha is waiting to be solved. Click on the button to show the input dialog (if supported)."))
        self.toolbar_captcha = QPushButton(_("No Captchas"))
        self.toolbar_captcha.setWhatsThis(whatsThisFormat(*whatsThis))
        f = self.font()
        f.setBold(True)
        self.toolbar_captcha.setFont(f)
        self.toolbar_captcha.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.actions["captcha"] = self.toolbar.addWidget(self.toolbar_captcha)
        self.actions["captcha"].setVisible(False)
        self.actions["captcha"].setEnabled(False)
        stretch3 = QWidget()
        stretch3.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.toolbar.addWidget(stretch3)
        self.actions["restart_failed"] = self.toolbar.addAction(self.appIconSet["restart"], "")
        wt = _("Restarts (resumes if supported) all failed, aborted and temporary offline downloads.")
        self.actions["restart_failed"].setWhatsThis(whatsThisFormat(_("Restart Failed"), wt))
        self.actions["remove_finished_packages"] = self.toolbar.addAction(self.appIconSet["remove"], "")
        wt = _("Removes all finished packages from the Queue and the Collector.")
        self.actions["remove_finished_packages"].setWhatsThis(whatsThisFormat(_("Remove Finished Packages"), wt))
        self.toolbar_speedLimit_enabled.toggled[bool].connect(self.slotSpeedLimitStatus)
        self.toolbar_speedLimit_rate.editingFinished.connect(self.slotSpeedLimitRate)
        self.toolbar_maxParallelDownloads_value.editingFinished.connect(self.slotMaxParallelDownloadsValue)
        self.toolbar_captcha.clicked.connect(self.slotCaptchaStatusButton)
        self.actions["status_start"].triggered[bool].connect(self.slotStatusStart)
        self.actions["status_pause"].triggered[bool].connect(self.slotStatusPause)
        self.actions["status_stop"].triggered.connect(self.slotStatusStop)
        self.actions["restart_failed"].triggered.connect(self.slotRestartFailed)
        self.actions["remove_finished_packages"].triggered.connect(self.slotRemoveAllFinishedPackages)

        self.addMenu = QMenu()
        self.actions["add_package"] = self.addMenu.addAction(_("Package"))
        self.actions["add_links"] = self.addMenu.addAction(_("Links"))
        self.actions["add_container"] = self.addMenu.addAction(_("Container"))
        self.addMenu.addSeparator()
        self.actions["add_account"] = self.addMenu.addAction(_("Account"))
        self.actions["add"].triggered.connect(self.slotAdd)
        self.actions["add_package"].triggered.connect(self.slotShowAddPackage)
        self.actions["add_links"].triggered.connect(self.slotShowAddLinks)
        self.actions["add_container"].triggered.connect(self.slotShowAddContainer)
        self.actions["add_account"].triggered.connect(self.slotNewAccount)

        self.clipboardMenu = QMenu()
        self.actions["clipboard_queue"] = self.clipboardMenu.addAction(_("Create New Packages In Queue"))
        self.actions["clipboard_queue"].setCheckable(True)
        self.actions["clipboard_collector"] = self.clipboardMenu.addAction(_("Create New Packages In Collector"))
        self.actions["clipboard_collector"].setCheckable(True)
        self.actions["clipboard_packDock"] = self.clipboardMenu.addAction(_("Add To New Package Window"))
        self.actions["clipboard_packDock"].setCheckable(True)
        self.actions["clipboard"].triggered.connect(self.slotClipboard)
        self.actions["clipboard_queue"].toggled[bool].connect(self.slotClipboardQueueToggled)
        self.actions["clipboard_collector"].toggled[bool].connect(self.slotClipboardCollectorToggled)
        self.actions["clipboard_packDock"].toggled[bool].connect(self.slotClipboardPackDockToggled)

    def init_tabs(self, connector):
        """
            create tabs
        """
        #queue
        self.tabs["queue"]["b"] = QPushButton(_("Pull Out Selected Packages"))
        self.tabs["queue"]["b"].setIcon(self.appIconSet["pull_small"])
        self.tabs["queue"]["m"] = QLabel()
        self.tabs["queue"]["m_defaultStyleSheet"] = self.tabs["queue"]["m"].styleSheet()
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
        self.tabs["queue"]["b"].clicked.connect(self.slotPullOutPackages)
        self.tabs["queue"]["view"].queueMsgShowSGL.connect(self.slotQueueMsgShow)
        self.tabs["queue"]["view"].queueMsgHideSGL.connect(self.slotQueueMsgHide)
        self.tabs["queue"]["view"].setContextMenuPolicy(Qt.CustomContextMenu)

        #overview
        self.tabs["overview"]["l"] = QGridLayout()
        self.tabs["overview"]["w"].setLayout(self.tabs["overview"]["l"])
        self.tabs["overview"]["view"] = OverviewView(self.tabs["queue"]["view"].model)
        self.tabs["overview"]["l"].addWidget(self.tabs["overview"]["view"])

        #collector
        self.tabs["collector"]["b"] = QPushButton(_("Push Selected Packages To Queue"))
        self.tabs["collector"]["b"].setIcon(self.appIconSet["push_small"])
        self.tabs["collector"]["m"] = QLabel()
        self.tabs["collector"]["m_defaultStyleSheet"] = self.tabs["collector"]["m"].styleSheet()
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
        self.tabs["collector"]["b"].clicked.connect(self.slotPushPackagesToQueue)
        self.tabs["collector"]["view"].collectorMsgShowSGL.connect(self.slotCollectorMsgShow)
        self.tabs["collector"]["view"].collectorMsgHideSGL.connect(self.slotCollectorMsgHide)
        self.tabs["collector"]["view"].setContextMenuPolicy(Qt.CustomContextMenu)

        #gui log
        self.tabs["guilog"]["cb"] = QCheckBox(_("Auto-scroll"))
        self.tabs["guilog"]["cb"].setChecked(True)
        self.tabs["guilog"]["l"] = QGridLayout()
        self.tabs["guilog"]["w"].setLayout(self.tabs["guilog"]["l"])
        self.tabs["guilog"]["text"] = QTextEdit()
        self.tabs["guilog"]["text"].setLineWrapMode(QTextEdit.NoWrap)
        self.tabs["guilog"]["text"].setTextInteractionFlags(self.tabs["guilog"]["text"].textInteractionFlags() & ~Qt.TextEditable)
        self.tabs["guilog"]["l"].addWidget(self.tabs["guilog"]["text"])
        self.tabs["guilog"]["l"].addWidget(self.tabs["guilog"]["cb"])
        self.tabs["guilog"]["text"].logOffset = 0

        #core log
        self.tabs["corelog"]["cb"] = QCheckBox(_("Auto-scroll"))
        self.tabs["corelog"]["cb"].setChecked(True)
        self.tabs["corelog"]["l"] = QGridLayout()
        self.tabs["corelog"]["w"].setLayout(self.tabs["corelog"]["l"])
        self.tabs["corelog"]["text"] = QTextEdit()
        self.tabs["corelog"]["text"].setLineWrapMode(QTextEdit.NoWrap)
        self.tabs["corelog"]["text"].setTextInteractionFlags(self.tabs["corelog"]["text"].textInteractionFlags() & ~Qt.TextEditable)
        self.tabs["corelog"]["l"].addWidget(self.tabs["corelog"]["text"])
        self.tabs["corelog"]["l"].addWidget(self.tabs["corelog"]["cb"])
        self.tabs["corelog"]["text"].logOffset = 0

        #accounts
        self.tabs["accounts"]["view"] = AccountView(self.corePermissions, connector)
        self.tabs["accounts"]["w"].setLayout(QVBoxLayout())
        self.tabs["accounts"]["w"].layout().addWidget(self.tabs["accounts"]["view"])
        self.tabs["accounts"]["b"] = QPushButton(_("New Account"))
        self.tabs["accounts"]["w"].layout().addWidget(self.tabs["accounts"]["b"])
        self.tabs["accounts"]["b"].clicked.connect(self.slotNewAccount)
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
        self.queueContext.buttons["pull"] = QAction(self.appIconSet["pull_small"], _("Pull Out"), self.queueContext)
        self.queueContext.buttons["edit"] = QAction(self.appIconSet["edit_small"], _("Edit Packages"), self.queueContext)
        self.queueContext.buttons["abort"] = QAction(self.appIconSet["abort_small"], _("Abort"), self.queueContext)
        self.queueContext.buttons["restart"] = QAction(self.appIconSet["restart_small"], _("Restart"), self.queueContext)
        self.queueContext.buttons["remove"] = QAction(self.appIconSet["remove_small"], _("Remove"), self.queueContext)
        self.queueContext.buttons["selectall"] = QAction(_("Select All"), self.queueContext)
        self.queueContext.buttons["deselectall"] = QAction(_("Deselect All"), self.queueContext)
        self.queueContext.buttons["removepackagedupes"] = QAction(self.appIconSet["remove_small"], _("Remove Duplicate Packages"), self.queueContext)
        self.queueContext.buttons["removelinkdupes"] = QAction(self.appIconSet["remove_small"], _("Remove Duplicate Links"), self.queueContext)
        self.queueContext.buttons["removefinishedpackages"] = QAction(self.appIconSet["remove_small"],
                                                                       _("Remove Finished Packages"), self.queueContext)
        self.queueContext.buttons["expand"] = QAction(self.style().standardIcon(QStyle.SP_ToolBarHorizontalExtensionButton),
                                                      _("Expand All"), self.queueContext)
        self.queueContext.buttons["collapse"] = QAction(self.style().standardIcon(QStyle.SP_ToolBarVerticalExtensionButton),
                                                        _("Collapse All"), self.queueContext)
        self.queueContext.addAction(self.queueContext.buttons["pull"])
        self.queueContext.addSeparator()
        self.queueContext.buttons["add"] = self.queueContext.addMenu(self.appIconSet["add_small"], _("Add"))
        self.queueContext.buttons["add_package"] = self.queueContext.buttons["add"].addAction(_("Package"))
        self.queueContext.buttons["add_links"] = self.queueContext.buttons["add"].addAction(_("Links"))
        self.queueContext.buttons["add_container"] = self.queueContext.buttons["add"].addAction(_("Container"))
        self.queueContext.addAction(self.queueContext.buttons["edit"])
        self.queueContext.addAction(self.queueContext.buttons["abort"])
        self.queueContext.addAction(self.queueContext.buttons["restart"])
        self.queueContext.addSeparator()
        self.queueContext.addAction(self.queueContext.buttons["remove"])
        self.queueContext.addSeparator()
        self.queueContext.addAction(self.queueContext.buttons["selectall"])
        self.queueContext.addAction(self.queueContext.buttons["deselectall"])
        self.queueContext.buttons["select"] = self.queueContext.addMenu(QIcon(), _("Select"))
        self.queueContext.buttons["advancedselect"] = self.queueContext.buttons["select"].addAction(_("Advanced Select/Deselect"))
        self.queueContext.buttons["select"].addSeparator()
        self.queueContext.buttons["selectallpacks"] = self.queueContext.buttons["select"].addAction(_("Select All Packages"))
        self.queueContext.buttons["deselectallpacks"] = self.queueContext.buttons["select"].addAction(_("Deselect All Packages"))
        self.queueContext.addSeparator()
        self.queueContext.addAction(self.queueContext.buttons["removepackagedupes"])
        self.queueContext.addAction(self.queueContext.buttons["removelinkdupes"])
        self.queueContext.addAction(self.queueContext.buttons["removefinishedpackages"])
        self.queueContext.addSeparator()
        self.queueContext.buttons["sort"] = self.queueContext.addMenu(QIcon(), _("Sort"))
        self.queueContext.buttons["sort_packages"] = self.queueContext.buttons["sort"].addAction(_("Packages"))
        self.queueContext.buttons["sort_links"] = self.queueContext.buttons["sort"].addAction(_("Links"))
        self.queueContext.addSeparator()
        self.queueContext.addAction(self.queueContext.buttons["expand"])
        self.queueContext.addAction(self.queueContext.buttons["collapse"])
        self.queueContext.buttons["pull"].triggered.connect(self.slotPullOutPackages)
        self.queueContext.buttons["add_package"].triggered.connect(self.slotShowAddPackage)
        self.queueContext.buttons["add_links"].triggered.connect(self.slotShowAddLinks)
        self.queueContext.buttons["add_container"].triggered.connect(self.slotShowAddContainer)
        self.queueContext.buttons["edit"].triggered.connect(self.slotEditPackages)
        self.queueContext.buttons["abort"].triggered.connect(self.slotAbortDownloads)
        self.queueContext.buttons["restart"].triggered.connect(self.slotRestartDownloads)
        self.queueContext.buttons["remove"].triggered.connect(self.slotRemoveDownloads)
        self.queueContext.buttons["selectall"].triggered.connect(self.slotSelectAll)
        self.queueContext.buttons["deselectall"].triggered.connect(self.slotDeselectAll)
        self.queueContext.buttons["selectallpacks"].triggered.connect(self.slotSelectAllPackages)
        self.queueContext.buttons["deselectallpacks"].triggered.connect(self.slotDeselectAllPackages)
        self.queueContext.buttons["advancedselect"].triggered.connect(self.slotAdvSelectShow)
        self.queueContext.buttons["removepackagedupes"].triggered.connect(self.slotRemovePackageDupes)
        self.queueContext.buttons["removelinkdupes"].triggered.connect(self.slotRemoveLinkDupes)
        self.queueContext.buttons["removefinishedpackages"].triggered.connect(self.slotRemoveFinishedPackages)
        self.queueContext.buttons["sort_packages"].triggered.connect(self.slotSortPackages)
        self.queueContext.buttons["sort_links"].triggered.connect(self.slotSortLinks)
        self.queueContext.buttons["expand"].triggered.connect(self.slotExpandAll)
        self.queueContext.buttons["collapse"].triggered.connect(self.slotCollapseAll)

        #collector
        self.collectorContext = QMenu()
        self.collectorContext.buttons = {}
        self.collectorContext.item = (None, None)
        self.collectorContext.buttons["push"] = QAction(self.appIconSet["push_small"], _("Push To Queue"), self.collectorContext)
        self.collectorContext.buttons["edit"] = QAction(self.appIconSet["edit_small"], _("Edit Packages"), self.collectorContext)
        self.collectorContext.buttons["abort"] = QAction(self.appIconSet["abort_small"], _("Abort"), self.collectorContext)
        self.collectorContext.buttons["restart"] = QAction(self.appIconSet["restart_small"], _("Restart"), self.collectorContext)
        self.collectorContext.buttons["remove"] = QAction(self.appIconSet["remove_small"], _("Remove"), self.collectorContext)
        self.collectorContext.buttons["selectall"] = QAction(_("Select All"), self.collectorContext)
        self.collectorContext.buttons["deselectall"] = QAction(_("Deselect All"), self.collectorContext)
        self.collectorContext.buttons["removepackagedupes"] = QAction(self.appIconSet["remove_small"], _("Remove Duplicate Packages"), self.collectorContext)
        self.collectorContext.buttons["removelinkdupes"] = QAction(self.appIconSet["remove_small"], _("Remove Duplicate Links"), self.collectorContext)
        self.collectorContext.buttons["removefinishedpackages"] = QAction(self.appIconSet["remove_small"],
                                                                           _("Remove Finished Packages"), self.collectorContext)
        self.collectorContext.buttons["expand"] = QAction(self.style().standardIcon(QStyle.SP_ToolBarHorizontalExtensionButton),
                                                          _("Expand All"), self.collectorContext)
        self.collectorContext.buttons["collapse"] = QAction(self.style().standardIcon(QStyle.SP_ToolBarVerticalExtensionButton),
                                                            _("Collapse All"), self.collectorContext)
        self.collectorContext.addAction(self.collectorContext.buttons["push"])
        self.collectorContext.addSeparator()
        self.collectorContext.buttons["add"] = self.collectorContext.addMenu(self.appIconSet["add_small"], _("Add"))
        self.collectorContext.buttons["add_package"] = self.collectorContext.buttons["add"].addAction(_("Package"))
        self.collectorContext.buttons["add_links"] = self.collectorContext.buttons["add"].addAction(_("Links"))
        self.collectorContext.addAction(self.collectorContext.buttons["edit"])
        self.collectorContext.addAction(self.collectorContext.buttons["abort"])
        self.collectorContext.addAction(self.collectorContext.buttons["restart"])
        self.collectorContext.addSeparator()
        self.collectorContext.addAction(self.collectorContext.buttons["remove"])
        self.collectorContext.addSeparator()
        self.collectorContext.addAction(self.collectorContext.buttons["selectall"])
        self.collectorContext.addAction(self.collectorContext.buttons["deselectall"])
        self.collectorContext.buttons["select"] = self.collectorContext.addMenu(QIcon(), _("Select"))
        self.collectorContext.buttons["advancedselect"] = self.collectorContext.buttons["select"].addAction(_("Advanced Select/Deselect"))
        self.collectorContext.buttons["select"].addSeparator()
        self.collectorContext.buttons["selectallpacks"] = self.collectorContext.buttons["select"].addAction(_("Select All Packages"))
        self.collectorContext.buttons["deselectallpacks"] = self.collectorContext.buttons["select"].addAction(_("Deselect All Packages"))
        self.collectorContext.addSeparator()
        self.collectorContext.addAction(self.collectorContext.buttons["removepackagedupes"])
        self.collectorContext.addAction(self.collectorContext.buttons["removelinkdupes"])
        self.collectorContext.addAction(self.collectorContext.buttons["removefinishedpackages"])
        self.collectorContext.addSeparator()
        self.collectorContext.buttons["sort"] = self.collectorContext.addMenu(QIcon(), _("Sort"))
        self.collectorContext.buttons["sort_packages"] = self.collectorContext.buttons["sort"].addAction(_("Packages"))
        self.collectorContext.buttons["sort_links"] = self.collectorContext.buttons["sort"].addAction(_("Links"))
        self.collectorContext.addSeparator()
        self.collectorContext.addAction(self.collectorContext.buttons["expand"])
        self.collectorContext.addAction(self.collectorContext.buttons["collapse"])
        self.collectorContext.buttons["push"].triggered.connect(self.slotPushPackagesToQueue)
        self.collectorContext.buttons["add_package"].triggered.connect(self.slotShowAddPackage)
        self.collectorContext.buttons["add_links"].triggered.connect(self.slotShowAddLinks)
        self.collectorContext.buttons["edit"].triggered.connect(self.slotEditPackages)
        self.collectorContext.buttons["abort"].triggered.connect(self.slotAbortDownloads)
        self.collectorContext.buttons["restart"].triggered.connect(self.slotRestartDownloads)
        self.collectorContext.buttons["remove"].triggered.connect(self.slotRemoveDownloads)
        self.collectorContext.buttons["selectallpacks"].triggered.connect(self.slotSelectAllPackages)
        self.collectorContext.buttons["deselectallpacks"].triggered.connect(self.slotDeselectAllPackages)
        self.collectorContext.buttons["selectall"].triggered.connect(self.slotSelectAll)
        self.collectorContext.buttons["deselectall"].triggered.connect(self.slotDeselectAll)
        self.collectorContext.buttons["advancedselect"].triggered.connect(self.slotAdvSelectShow)
        self.collectorContext.buttons["removepackagedupes"].triggered.connect(self.slotRemovePackageDupes)
        self.collectorContext.buttons["removelinkdupes"].triggered.connect(self.slotRemoveLinkDupes)
        self.collectorContext.buttons["removefinishedpackages"].triggered.connect(self.slotRemoveFinishedPackages)
        self.collectorContext.buttons["sort_packages"].triggered.connect(self.slotSortPackages)
        self.collectorContext.buttons["sort_links"].triggered.connect(self.slotSortLinks)
        self.collectorContext.buttons["expand"].triggered.connect(self.slotExpandAll)
        self.collectorContext.buttons["collapse"].triggered.connect(self.slotCollapseAll)

        #accounts
        self.accountContext = QMenu()
        self.accountContext.buttons = {}
        self.accountContext.buttons["add"] = QAction(self.appIconSet["add_small"], _("Add"), self.accountContext)
        self.accountContext.buttons["edit"] = QAction(self.appIconSet["edit_small"], _("Edit"), self.accountContext)
        self.accountContext.buttons["remove"] = QAction(self.appIconSet["remove_small"], _("Remove"), self.accountContext)
        self.accountContext.addAction(self.accountContext.buttons["add"])
        self.accountContext.addAction(self.accountContext.buttons["edit"])
        self.accountContext.addAction(self.accountContext.buttons["remove"])
        self.accountContext.buttons["add"].triggered.connect(self.slotNewAccount)
        self.accountContext.buttons["edit"].triggered.connect(self.slotEditAccount)
        self.accountContext.buttons["remove"].triggered.connect(self.slotRemoveAccount)

    def initEventHooks(self):
        self.eD = {}
        self.eD["pCount"] = int(0)
        self.eD["lastGeo"] = QRect(10000000, 10000000, 10000000, 10000000)
        self.eD["lastNormPos"] = self.eD["lastNormSize"] = self.eD["2ndLastNormPos"] = self.eD["2ndLastNormSize"] = None
        self.eD["pLastMax"] = self.eD["pSignal"] = self.eD["pStateSig"] = False

    def paintEvent(self, event):
        if self.eD["pStateSig"]:
            self.mainWindowStateSGL.emit()
        self.eD["pCount"] += 1
        self.log.debug3("MainWindow.paintEvent:  at %08d msec   cnt: %04d   rect: x:%04d y:%04d w:%04d h:%04d" %
                        (self.time_msec(), self.eD["pCount"], event.rect().x(), event.rect().y(), event.rect().width(), event.rect().height()))
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
            self.mainWindowPaintEventSGL.emit()
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
                self.log.debug3("MainWindow.paintEvent: maximized\t\t(%04d, %04d)\t\t\t(%04d, %04d)\t\t[geo]" %
                                (geo.topLeft().x(), geo.topLeft().y(), geo.size().width(), geo.size().height()))
                mrogeo = QRect(self.moveEventOldPos, self.resizeEventOldSize)
                self.log.debug3("MainWindow.paintEvent:          \t\t(%04d, %04d)\t\t\t(%04d, %04d)\t\t[mrogeo]" %
                                (mrogeo.topLeft().x(), mrogeo.topLeft().y(), mrogeo.size().width(), mrogeo.size().height()))
        else:
            self.log.debug3("MainWindow.paintEvent: unmaximized\t(%04d, %04d)\t\t\t(%04d, %04d)\t\t[geo]" %
                            (geo.topLeft().x(), geo.topLeft().y(), geo.size().width(), geo.size().height()))
        self.eD["lastGeo"] = geo
        self.eD["pLastMax"] = maximized

    def moveEvent(self, event):
        self.moveEventOldPos = event.oldPos()
        self.moveEventPos = event.pos()
        self.log.debug3("MainWindow.moveEvent:   at %08d msec \t\t(%04d, %04d) -> (%04d, %04d)\t----------------------------" %
                        (self.time_msec(), event.oldPos().x(), event.oldPos().y(), event.pos().x(), event.pos().y()))
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
        self.log.debug3("MainWindow.resizeEvent: at %08d msec \t\t----------------------------\t(%04d, %04d) -> (%04d, %04d)\t" %
                        (self.time_msec(), event.oldSize().width(), event.oldSize().height(), event.size().width(), event.size().height()))

    def changeEvent(self, event):
        if (event.type() == QEvent.WindowStateChange):
            if (self.windowState() & Qt.WindowMinimized):
                if not (event.oldState() & Qt.WindowMinimized):
                    self.minimizeToggledSGL.emit(True)
            elif (event.oldState() & Qt.WindowMinimized):
                self.minimizeToggledSGL.emit(False)
            if (self.windowState() & Qt.WindowMaximized):
                if not (event.oldState() & Qt.WindowMaximized):
                    self.maximizeToggledSGL.emit(True)
            elif (event.oldState() & Qt.WindowMaximized):
                self.maximizeToggledSGL.emit(False)

    def closeEvent(self, event):
        """
            somebody wants to close me!
        """
        event.ignore()
        self.mainWindowCloseSGL.emit()

    @classmethod
    def urlFilter(self, text):
        p = (ur'(?i)\b(((?:ht|f)tps?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]|\(([^\s()<>]+|(\([^\s()<>]+'
             ur'\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:\'".,<>?\xab\xbb\u201c\u201d\u2018\u2019]))')
        pattern = re.compile(p)
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
        self.showAboutSGL.emit()

    def slotQueueMsgShow(self, msg, error):
        """
            emitted from queue view, show message label instead of pull button
        """
        if error:
            s = "QWidget { color: crimson; background-color: %s }" % QColor(Qt.gray).name()     # red text color on gray background
            self.tabs["queue"]["m"].setStyleSheet(s)
            self.tabs["queue"]["m"].setText("<b>" + "&nbsp;" + "&nbsp;" + msg + "</b>")         # bold text with leading whitespace
        else:
            self.tabs["queue"]["m"].setStyleSheet(self.tabs["queue"]["m_defaultStyleSheet"])    # default text and background colors
            self.tabs["queue"]["m"].setText("<b>" + msg + "</b>")                               # bold text
        self.tabs["queue"]["m"].setFixedHeight(self.tabs["queue"]["b"].height())
        self.tabs["queue"]["m"].show()
        self.tabs["queue"]["b"].hide()

    def slotQueueMsgHide(self):
        """
            emitted from queue view, show pull button
        """
        self.tabs["queue"]["m"].hide()
        self.tabs["queue"]["b"].show()

    def slotCollectorMsgShow(self, msg, error):
        """
            emitted from collector view, show message label instead of push button
        """
        if error:
            s = "QWidget { color: crimson; background-color: %s }" % QColor(Qt.gray).name()         # red text color on gray background
            self.tabs["collector"]["m"].setStyleSheet(s)
            self.tabs["collector"]["m"].setText("<b>" + "&nbsp;" + "&nbsp;" + msg + "</b>")         # bold text with leading whitespace
        else:
            self.tabs["collector"]["m"].setStyleSheet(self.tabs["queue"]["m_defaultStyleSheet"])    # default text and background colors
            self.tabs["collector"]["m"].setText("<b>" + msg + "</b>")                               # bold text
        self.tabs["collector"]["m"].setFixedHeight(self.tabs["collector"]["b"].height())
        self.tabs["collector"]["m"].show()
        self.tabs["collector"]["b"].hide()

    def slotCollectorMsgHide(self):
        """
            emitted from collector view, show push button
        """
        self.tabs["collector"]["m"].hide()
        self.tabs["collector"]["b"].show()

    def slotAdvSelectShow(self):
        """
            triggered from collector and queue context menues
            show advanced link/package select box
        """
        self.advselectframe.show()
        if self.tabw.currentIndex() == 1:
            self.advselectframeQueueIsVisible = True
        else:
            self.advselectframeCollectorIsVisible = True

    def slotAdvSelectHide(self):
        """
            triggered from collector and queue context menues
            hide advanced link/package select box
        """
        self.advselectframe.hide()
        if self.tabw.currentIndex() == 1:
            self.advselectframeQueueIsVisible = False
        else:
            self.advselectframeCollectorIsVisible = False

    def slotAdvSelectSelectButtonClicked(self):
        """
            triggered from advanced link/package select box
        """
        queue = True if self.tabw.currentIndex() == 1 else False
        self.advancedSelectSGL.emit(queue, False)

    def slotAdvSelectDeselectButtonClicked(self):
        """
            triggered from advanced link/package select box
        """
        queue = True if self.tabw.currentIndex() == 1 else False
        self.advancedSelectSGL.emit(queue, True)

    def slotRemovePackageDupes(self):
        """
            remove duplicate packages
            let main to the stuff
        """
        self.removePackageDupesSGL.emit()

    def slotRemoveLinkDupes(self):
        """
            remove duplicate links
            let main to the stuff
        """
        self.removeLinkDupesSGL.emit()

    def slotRemoveFinishedPackages(self):
        """
            remove finished packages
            let main to the stuff
        """
        self.removeFinishedPackagesSGL.emit()

    def slotToolbarVisibilityChanged(self, visible):
        """
            set the toolbar checkbox in view-menu (mainmenu)
        """
        self.mactions["showtoolbar"].setChecked(visible)
        self.mactions["showspeedlimit"].setEnabled(visible) # disable/greyout menu entry
        self.mactions["showmaxpadls"].setEnabled(visible)   # disable/greyout menu entry

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
        self.log.debug8("slotToggleSpeedLimitVisibility: toggled: %s" % str(checked))
        self.actions["speedlimit_enabled"].setEnabled(False)
        self.actions["speedlimit_enabled"].setVisible(checked)
        self.actions["speedlimit_rate"].setEnabled(False)
        self.actions["speedlimit_rate"].setVisible(checked)

    def slotToggleMaxPaDlsVisibility(self, checked):
        """
            toggle from view-menu (mainmenu)
            show/hide max parallel downloads
        """
        self.log.debug8("slotToggleMaxPaDlsVisibility: toggled: %s" % str(checked))
        self.actions["maxparalleldownloads_label"].setEnabled(False)
        self.actions["maxparalleldownloads_label"].setVisible(checked)
        self.actions["maxparalleldownloads_value"].setEnabled(False)
        self.actions["maxparalleldownloads_value"].setVisible(checked)

    def slotReload(self):
        """
            from view-menu (mainmenu)
            force reload queue and collector tab
        """
        self.reloadQueueSGL.emit()
        self.reloadCollectorSGL.emit()

    def slotShowCaptchaFromMenu(self):
        """
            from view-menu (mainmenu)
            show captcha
        """
        self.showCaptchaFromMenuSGL.emit()

    def slotStatusStart(self):
        """
            run button (toolbar)
        """
        self.setDownloadStatusSGL.emit(True)

    def slotStatusPause(self):
        """
            pause button (toolbar)
        """
        self.setDownloadStatusSGL.emit(False)

    def slotStatusStop(self):
        """
            stop button (toolbar)
        """
        self.stopAllDownloadsSGL.emit()

    def slotRestartFailed(self):
        """
            restart failed button (toolbar)
            let main to the stuff
        """
        self.restartFailedSGL.emit()

    def slotRemoveAllFinishedPackages(self):
        """
            remove finished packages from queue and collector button (toolbar)
            let main to the stuff
        """
        self.removeAllFinishedPackagesSGL.emit()

    def slotAdd(self):
        """
            add button (toolbar)
            show context menu
        """
        self.addMenu.exec_(QCursor.pos())

    def slotShowAddPackage(self):
        """
            action from add-menu
            show new-package dock
        """
        self.showAddPackageSGL.emit()

    def slotShowAddLinks(self):
        """
            action from add-menu
            show new-links dock
        """
        self.showAddLinksSGL.emit()

    def slotClipboard(self):
        """
            clipboard watcher button (toolbar)
            show context menu
        """
        self.actions["clipboard"].setChecked(not self.actions["clipboard"].isChecked())
        self.clipboardMenu.exec_(QCursor.pos())

    def slotClipboardQueueToggled(self, status):
        if status:
            self.actions["clipboard_collector"].setChecked(False)
            self.actions["clipboard_packDock"].setChecked(False)
        self.actions["clipboard"].setChecked(status)

    def slotClipboardCollectorToggled(self, status):
        if status:
            self.actions["clipboard_queue"].setChecked(False)
            self.actions["clipboard_packDock"].setChecked(False)
        self.actions["clipboard"].setChecked(status)

    def slotClipboardPackDockToggled(self, status):
        if status:
            self.actions["clipboard_queue"].setChecked(False)
            self.actions["clipboard_collector"].setChecked(False)
        self.actions["clipboard"].setChecked(status)

    def slotShowConnector(self):
        """
            connection manager action triggered
            let main to the stuff
        """
        self.showConnectorSGL.emit()

    def slotShowCorePermissions(self):
        """
            core permissions action triggered
            let main to the stuff
        """
        self.showCorePermissionsSGL.emit()

    def slotQuitCore(self):
        """
            quit core action triggered
            let main to the stuff
        """
        self.quitCoreSGL.emit()

    def slotRestartCore(self):
        """
            restart core action triggered
            let main to the stuff
        """
        self.restartCoreSGL.emit()

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

    def slotAddPackageDone(self, name, links, queue, password=None):
        """
            new package
            let main to the stuff
        """
        self.addPackageSGL.emit(name, links, queue, password)

    def slotAddLinksToPackageDone(self, links, queue):
        """
            adds links to currently selected package
            let main to the stuff
        """
        self.addLinksToPackageSGL.emit(links, queue)

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
        if USE_PYQT5:
            (fileNames, dummy) = QFileDialog.getOpenFileNames(self, "Open Container", self.lastAddContainerDir, typeStr)
        else:
            fileNames = QFileDialog.getOpenFileNames(self, "Open Container", self.lastAddContainerDir, typeStr)
            fileNames = [ unicode(name) for name in fileNames ]
        for name in fileNames:
            self.addContainerSGL.emit(name)
        if fileNames:
            self.lastAddContainerDir =  dirname(name)

    def slotPushPackagesToQueue(self):
        """
            push selected collector packages to queue
            let main do it
        """
        self.pushPackagesToQueueSGL.emit()

    def slotQueueContextMenu(self, pos):
        """
            custom context menu in queue view requested
        """
        menuPos = QCursor.pos()
        menuPos.setX(menuPos.x() + 2)
        (packsCnt, linksCnt, downloading, allPacksCnt) = self.tabs["queue"]["view"].model.getSelectionInfo()
        self.queueContext.buttons["pull"]                  .setEnabled(self.corePermissions["MODIFY"] and packsCnt > 0                    )
        self.queueContext.buttons["add_links"]             .setEnabled(self.corePermissions["ADD"   ] and packsCnt == 1                   )
        self.queueContext.buttons["edit"]                  .setEnabled(self.corePermissions["MODIFY"] and packsCnt > 0                    )
        self.queueContext.buttons["abort"]                 .setEnabled(self.corePermissions["MODIFY"] and downloading                     )
        self.queueContext.buttons["restart"]               .setEnabled(self.corePermissions["MODIFY"] and (packsCnt > 0 or linksCnt > 0)  )
        self.queueContext.buttons["remove"]                .setEnabled(self.corePermissions["DELETE"] and (packsCnt > 0 or linksCnt > 0)  )
        self.queueContext.buttons["removepackagedupes"]    .setEnabled(self.corePermissions["DELETE"] and allPacksCnt > 1                 )
        self.queueContext.buttons["removelinkdupes"]       .setEnabled(self.corePermissions["DELETE"] and packsCnt == 1                   )
        self.queueContext.buttons["removefinishedpackages"].setEnabled(self.corePermissions["DELETE"] and allPacksCnt > 0                 )
        self.queueContext.buttons["sort"]                  .setEnabled(self.corePermissions["MODIFY"]                                     )
        self.queueContext.buttons["sort_packages"]         .setEnabled(self.corePermissions["MODIFY"]                                     )
        self.queueContext.buttons["sort_links"]            .setEnabled(self.corePermissions["MODIFY"] and packsCnt == 1                   )
        self.activeMenu = self.queueContext
        self.queueContext.exec_(menuPos)

    def slotCollectorContextMenu(self, pos):
        """
            custom context menu in package collector view requested
        """
        menuPos = QCursor.pos()
        menuPos.setX(menuPos.x() + 2)
        (packsCnt, linksCnt, dummy, allPacksCnt) = self.tabs["collector"]["view"].model.getSelectionInfo()
        self.collectorContext.buttons["push"]                  .setEnabled(self.corePermissions["MODIFY"] and packsCnt > 0                    )
        self.collectorContext.buttons["add_links"]             .setEnabled(self.corePermissions["ADD"   ] and packsCnt == 1                   )
        self.collectorContext.buttons["edit"]                  .setEnabled(self.corePermissions["MODIFY"] and packsCnt > 0                    )
        self.collectorContext.buttons["abort"]                 .setEnabled(self.corePermissions["MODIFY"] and (packsCnt > 0 or linksCnt > 0)  )
        self.collectorContext.buttons["restart"]               .setEnabled(self.corePermissions["MODIFY"] and (packsCnt > 0 or linksCnt > 0)  )
        self.collectorContext.buttons["remove"]                .setEnabled(self.corePermissions["DELETE"] and (packsCnt > 0 or linksCnt > 0)  )
        self.collectorContext.buttons["removepackagedupes"]    .setEnabled(self.corePermissions["DELETE"] and allPacksCnt > 1                 )
        self.collectorContext.buttons["removelinkdupes"]       .setEnabled(self.corePermissions["DELETE"] and packsCnt == 1                   )
        self.collectorContext.buttons["removefinishedpackages"].setEnabled(self.corePermissions["DELETE"] and allPacksCnt > 0                 )
        self.collectorContext.buttons["sort"]                  .setEnabled(self.corePermissions["MODIFY"]                                     )
        self.collectorContext.buttons["sort_packages"]         .setEnabled(self.corePermissions["MODIFY"]                                     )
        self.collectorContext.buttons["sort_links"]            .setEnabled(self.corePermissions["MODIFY"] and packsCnt == 1                   )
        self.activeMenu = self.collectorContext
        self.collectorContext.exec_(menuPos)

    def slotRestartDownloads(self):
        """
            restart download action is triggered
        """
        self.restartDownloadsSGL.emit(self.activeMenu == self.queueContext)

    def slotRemoveDownloads(self):
        """
            remove download action is triggered
        """
        self.removeDownloadsSGL.emit(self.activeMenu == self.queueContext)

    def slotSpeedLimitStatus(self, status):
        """
            speed limit enable/disable checkbox (toolbar)
        """
        self.toolbarSpeedLimitEditedSGL.emit()

    def slotSpeedLimitRate(self):
        """
            speed limit rate spinbox (toolbar)
        """
        self.toolbar_speedLimit_rate.lineEdit().deselect() # deselect any selected text
        self.toolbarSpeedLimitEditedSGL.emit()

    def slotMaxParallelDownloadsValue(self):
        """
            max parallel downloads spinbox (toolbar)
        """
        self.toolbar_maxParallelDownloads_value.lineEdit().deselect() # deselect any selected text
        self.toolbarMaxParallelDownloadsEditedSGL.emit()

    def slotCaptchaStatusButton(self):
        """
            captcha status button (toolbar)
        """
        self.captchaStatusButtonSGL.emit()

    def slotEditPackages(self):
        """
            popup the package edit dialog
        """
        self.editPackagesSGL.emit(self.activeMenu == self.queueContext)

    def slotPullOutPackages(self):
        """
            pull selected packages out of the queue
            let main do it
        """
        self.pullOutPackagesSGL.emit()

    def slotAbortDownloads(self):
        """
            abort selected downloads
            let main do it
        """
        self.abortDownloadsSGL.emit(self.activeMenu == self.queueContext)

    def slotSelectAllPackages(self):
        """
            select all packages
            let main to the stuff
        """
        self.selectAllPackagesSGL.emit()

    def slotDeselectAllPackages(self):
        """
            deselect all packages
            let main to the stuff
        """
        self.deselectAllPackagesSGL.emit()

    def slotSelectAll(self):
        """
            select all items
            let main to the stuff
        """
        self.selectAllSGL.emit()

    def slotDeselectAll(self):
        """
            deselect all items
            let main to the stuff
        """
        self.deselectAllSGL.emit()

    def slotSortPackages(self):
        """
            sort packages
            let main to the stuff
        """
        self.sortPackagesSGL.emit()

    def slotSortLinks(self):
        """
            sort links
            let main to the stuff
        """
        self.sortLinksSGL.emit()

    def slotExpandAll(self):
        """
            expand all tree view items
            let main to the stuff
        """
        self.expandAllSGL.emit()

    def slotCollapseAll(self):
        """
            collapse all tree view items
            let main to the stuff
        """
        self.collapseAllSGL.emit()

    def slotTabChanged(self, index):
        # currentIndex
        if index == 3:
            self.tabs["accounts"]["view"].model.slotReloadData()
            self.tabs["accounts"]["view"].model.timer.start(2000)
        else:
            self.tabs["accounts"]["view"].model.timer.stop()
        if index == 5:
            self.tabs["settings"]["w"].slotLoadConfig()
        if index == 1:
            if self.newPackDock.widget.destAutoSelect.isChecked():
                self.newPackDock.widget.destQueue.setChecked(True)
            if self.newLinkDock.widget.destAutoSelect.isChecked():
                self.newLinkDock.widget.destQueue.setChecked(True)
            self.advselectframe.setVisible(self.advselectframeQueueIsVisible)
        elif index == 2:
            if self.newPackDock.widget.destAutoSelect.isChecked():
                self.newPackDock.widget.destCollector.setChecked(True)
            if self.newLinkDock.widget.destAutoSelect.isChecked():
                self.newLinkDock.widget.destCollector.setChecked(True)
            self.advselectframe.setVisible(self.advselectframeCollectorIsVisible)
        else:
            self.advselectframe.hide()

    def slotNewAccount(self):
        if not self.corePermissions["ACCOUNTS"]:
            return

        types = self.connector.proxy.getAccountTypes()
        types = sorted(types, key=lambda p: p)
        self.accountEdit = AccountEdit.newAccount(self, types)

        #TODO make more easy n1, n2, n3
        def slotSave(data):
            if data["password"]:
                self.accountEdit.close()
                n1 = data["acctype"]
                n2 = data["login"]
                n3 = data["password"]
                self.connector.proxy.updateAccount(n1, n2, n3, None)

        self.accountEdit.accountEditSaveSGL.connect(slotSave)
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
        def slotSave(data):
            self.accountEdit.close()
            n1 = data["acctype"]
            n2 = data["login"]
            n3 = data["password"]
            self.connector.proxy.updateAccount(n1, n2, n3, None)

        self.accountEdit.accountEditSaveSGL.connect(slotSave)
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
        menuPos = QCursor.pos()
        menuPos.setX(menuPos.x() + 2)
        view = self.tabs["accounts"]["view"]
        index = view.indexAt(pos)
        if index.isValid():
            vr = view.visualRect(index)
            indent = vr.x() - view.visualRect(view.rootIndex()).x()
            if pos.x() < indent:
                clickOnItem = False     # indent area clicked
            else:
                clickOnItem = True
        else:
            clickOnItem = False         # empty bottom area clicked
        if clickOnItem:
            self.accountContext.buttons["edit"].setEnabled(True)
            self.accountContext.buttons["remove"].setEnabled(True)
        else:
            self.accountContext.buttons["edit"].setEnabled(False)
            self.accountContext.buttons["remove"].setEnabled(False)
        self.accountContext.exec_(menuPos)

    def slotSetupPluginsMenu(self):
        """
            create the plugins menu entries
        """
        for name in self.pmactions:
            self.pmactions[name].triggered.disconnect()
        self.pmactions = {}
        self.menus["plugins"].clear()

        for name in self.tabs["settings"]["w"].menuPlugins:
            self.pmactions[name] = QAction(name, self.menus["plugins"])
            self.menus["plugins"].addAction(self.pmactions[name])
            self.pmactions[name].triggered.connect(lambda checked, name=name: self.slotPluginsMenu(name))
        if not self.pmactions:
            self.menus["plugins"].addAction(_("no plugins added")).setEnabled(False)

    def slotPluginsMenu(self, name):
        """
            a plugins menu entry was clicked
            show the config page for the plugin
        """
        self.tabw.setCurrentIndex(5)                                            # Server Settings Tab
        self.tabs["settings"]["w"].tab.setCurrentIndex(1)                       # Plugins Tab

        index = self.tabs["settings"]["w"].pluginsComboBox.findText(name)
        if index != -1:
            self.tabs["settings"]["w"].pluginsComboBox.setCurrentIndex(index)   # ComboBox
            self.tabs["settings"]["w"].slotPluginsComboBoxActivated(index)      # Page
        else:
            self.menuPluginNotFoundSGL.emit(name)

    def slotShowLoggingOptions(self):
        self.showLoggingOptionsSGL.emit()

    def slotShowClickNLoadForwarderOptions(self):
        self.showClickNLoadForwarderOptionsSGL.emit()

    def slotShowAutomaticReloadingOptions(self):
        self.showAutomaticReloadingOptionsSGL.emit()

    def slotShowCaptchaOptions(self):
        self.showCaptchaOptionsSGL.emit()

    def slotShowIconThemeOptions(self):
        self.showIconThemeOptionsSGL.emit()

    def slotShowFontOptions(self):
        self.showFontOptionsSGL.emit()

    def slotShowColorFixOptions(self):
        self.showColorFixOptionsSGL.emit()

    def slotShowNotificationOptions(self):
        self.showNotificationOptionsSGL.emit()

    def slotShowTrayOptions(self):
        self.showTrayOptionsSGL.emit()

    def slotShowWhatsThisOptions(self):
        self.showWhatsThisOptionsSGL.emit()

    def slotShowOtherOptions(self):
        self.showOtherOptionsSGL.emit()

    def slotShowLanguageOptions(self):
        self.showLanguageOptionsSGL.emit()

    def slotShowPyQtVersionOptions(self):
        self.showPyQtVersionOptionsSGL.emit()


