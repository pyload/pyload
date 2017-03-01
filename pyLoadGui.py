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
"""
CURRENT_VERSION = '0.4.9'
CURRENT_INTERNAL_VERSION = '2016-12-24'         # YYYY-MM-DD, append a lowercase letter for a new version on the same day  

import gtk
import sys

from sys import argv
from getopt import getopt, GetoptError
from module.gui import LoggingLevels
from module.gui.Tools import LineView
import logging.handlers
from os import getcwd, makedirs, sep

from uuid import uuid4 as uuid # should be above PyQt imports
from time import sleep, time

from base64 import b64decode

from PyQt4.QtCore import *
from PyQt4.QtGui import *

import re
import copy
import traceback
import module.common.pylgettext as gettext
import socket
import errno
import thread
import os
from os.path import abspath
from os.path import join
from os.path import basename
from os.path import commonprefix
from os.path import exists

from module import InitHomeDir
from module.gui.ConnectionManager import *
from module.gui.connector import Connector
from module.gui.MainWindow import *
from module.gui.Queue import *
from module.gui.Overview import *
from module.gui.Collector import *
from module.gui.XMLParser import *
from module.gui.CoreConfigParser import ConfigParser
from module.gui.Tools import MessageBox

from module.lib.rename_process import renameProcess
from module.utils import formatSize, formatSpeed

from module.remote.thriftbackend.ThriftClient import DownloadStatus
from module.Api import has_permission, PERMS, ROLE

try:
    import pynotify
except ImportError:
    print "pynotify not installed, falling back to qt tray notification"

class main(QObject):
    def pyLoadGuiExcepthook(self, type, value, tback):
        self.log.error("***Exception***\n" + "".join(traceback.format_exception(type, value, tback)))

    def setExcepthook(self, logging):
        if logging:
            sys.excepthook = self.pyLoadGuiExcepthook
        else:
            sys.excepthook = sys.__excepthook__

    def __init__(self):
        """
            main setup
        """
        QObject.__init__(self)
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)
        self.defAppFont = QApplication.font()
        self.path = pypath
        self.homedir = abspath("")

        self.cmdLineConnection = None
        self.configdir = ""
        self.pidfile = "pyloadgui.pid"
        self.debugLogLevel = None
        if len(argv) > 1:
            try:
                options, args = getopt(argv[1:], 'vc:p:hd:',
                    ["configdir=", "version", "connection=",
                      "pidfile=", "help", "debug="])
                for option, argument in options:
                    if option in ("-v", "--version"):
                        print "pyLoad Client", CURRENT_VERSION
                        exit()
                    elif option in ("-c", "--connection"):
                        self.cmdLineConnection = argument
                    elif option in ("--configdir"):
                        self.configdir = argument
                    elif option in ("-p", "--pidfile"):
                        self.pidfile = argument
                        print "Error: The pidfile option is not implemented"
                        exit()
                    elif option in ("-h", "--help"):
                        self.print_help()
                        exit()
                    elif option in ("-d", "--debug"):
                        try:
                            lvl = int(argument)
                        except ValueError:
                            print "Error: Invalid debug level"
                            exit()
                        if lvl < 0 or lvl > 9:
                            print "Error: Invalid debug level"
                            exit()
                        self.debugLogLevel = lvl

            except GetoptError:
                print 'Error: Unknown Argument(s) "%s"' % " ".join(argv[1:])
                self.print_help()
                exit()

        self.fileLogIsEnabled = None
        if not self.checkConfigFiles():
            exit()
        self.init(True)

    def print_help(self):
        print ""
        print "pyLoad Client v%s     2008-2016 the pyLoad Team" % CURRENT_VERSION
        print ""
        if sys.argv[0].endswith(".py"):
            print "Usage: python pyLoadGui.py [options]"
        else:
            print "Usage: pyLoadGui [options]"
        print ""
        print "<Options>"
        print "  -v, --version", " " * 10, "Print version to terminal"
        print "  -d, --debug=<level>", " " * 4, "Enable debug messages"
        print "                               possible levels: 0 to 9"
        print "  --configdir=<dir>", " " * 6, "Run with <dir> as config directory"
        print "  -c, --connection=<name>", " " * 0, "Use connection <name>"
        print "                               of the Connection Manager"
        #print "  -p, --pidfile=<file>", " " * 3, "Set pidfile to <file>"
        print "  -h, --help", " " * 13, "Display this help screen"
        print ""

    def checkConfigFiles(self):
        if self.configdir:
            guiFile = self.homedir + sep + "gui.xml"
        else:
            guiFile = abspath("gui.xml")
        guiFileFound = os.path.isfile(guiFile) and os.access(guiFile, os.R_OK)
        defaultGuiFile = join(self.path, "module", "config", "gui_default.xml")
        defaultGuiFileFound = os.path.isfile(defaultGuiFile) and os.access(defaultGuiFile, os.R_OK)
        if not guiFileFound:
            text  = "Cannot find the configuration file:"
            text += "\n" + guiFile
            text += "\n\nDo you want to create a new one?"
            msgb = MessageBox(None, text, "W", "YES_NO", True)
            if not msgb.exec_():
                return False
            if not defaultGuiFileFound:
                text  = "Cannot create the configuration file!"
                text += "\n\nBecause the default configuration file neither can be found:"
                text += "\n" + defaultGuiFile
                msgb = MessageBox(None, text, "C", "OK", True)
                msgb.exec_()
                return False
        return True

    def init(self, first=False):
        """
            set main things up
        """
        self.tray = None
        self.guiLogMutex = QMutex()

        self.parser = XMLParser(join(self.homedir, "gui.xml"), join(self.path, "module", "config", "gui_default.xml"))
        self.lang = self.parser.xml.elementsByTagName("language").item(0).toElement().text()
        if not self.lang:
            parser = XMLParser(join(self.path, "module", "config", "gui_default.xml"))
            self.lang = parser.xml.elementsByTagName("language").item(0).toElement().text()

        gettext.setpaths([join(os.sep, "usr", "share", "pyload", "locale"), None])
        translation = gettext.translation("pyLoadGui", join(pypath, "locale"), languages=[str(self.lang), "en"], fallback=True)
        try:
            translation.install(unicode=(True if sys.stdout.encoding.lower().startswith("utf") else False))
        except:
            translation.install(unicode=False)

        self.loggingOptions = LoggingOptions()
        optlog = self.parser.xml.elementsByTagName("optionsLogging").item(0).toElement().text()
        if optlog:
            self.loggingOptions.settings = eval(str(QByteArray.fromBase64(str(optlog))))
            self.loggingOptions.dict2dialogState()
        self.initLogging(first)

        self.log.info("====================================================================================================")
        if first:
            self.log.info("Starting pyLoad Client %s" % CURRENT_VERSION)
        else:
            self.log.info("Reinitializing pyLoad Client %s" % CURRENT_VERSION)
        self.log.info("Using home directory: %s" % self.homedir)
        #self.log.info("Using pid file: %s" % self.pidfile)
        if self.debugLogLevel != None:
            self.log.info("Debug messages at level %d and higher" % self.debugLogLevel)

        self.initCorePermissions()
        self.connector = Connector(first)
        self.inSlotToolbarSpeedLimitEdited = False
        self.mainWindow = MainWindow(self.corePermissions, self.connector)
        self.initMaxiUnmaxiWait()
        self.loggingOptions.setParent(self.mainWindow, self.loggingOptions.windowFlags())
        self.packageEdit = PackageEdit(self.mainWindow)
        self.setupGuiLogTab(self.loggingOptions.settings["file_log"])
        self.fontOptions = FontOptions(self.defAppFont, self.mainWindow)
        self.clickNLoadForwarderOptions = ClickNLoadForwarderOptions(self.mainWindow)
        self.automaticReloadingOptions = AutomaticReloadingOptions(self.mainWindow)
        self.languageOptions = LanguageOptions(self.mainWindow)
        self.captchaOptions = CaptchaOptions(self.mainWindow)
        self.connWindow = ConnectionManager()
        self.clickNLoadForwarder = ClickNLoadForwarder()
        self.mainloop = self.Loop(self)
        self.connectSignals()

        self.checkClipboard = False
        conn = self.refreshConnections(self.cmdLineConnection)
        self.connData = None
        self.serverStatus = {"freespace":0}

        self.core = None # pyLoadCore if started
        self.connectionLost = False

        if not first:
            self.connWindow.emit(SIGNAL("setCurrentItem"), self.lastConnection)
            self.connWindow.show()
        else:
            if conn:
                self.log.debug9("main.init: Using startup connection: '%s'" % conn["name"])
            else:
                self.log.debug9("main.init: No startup connection set")
            self.connWindow.edit.setData(conn)
            data = self.connWindow.edit.getData()
            self.slotConnect(data)

    def initLogging(self, first=False):
        # create the folder if it does not exist
        if self.loggingOptions.settings["file_log"]:
            folder = self.loggingOptions.settings["log_folder"]
            if not exists(folder):
                folder = folder.replace("/", sep)
                makedirs(folder)
        if not first:
            self.setExcepthook(False)
            self.removeLogger()
        if self.debugLogLevel != None:
            exec("lvl = logging.DEBUG" + str(self.debugLogLevel))
            self.init_logger(lvl)               # logging level
        else:
            self.init_logger(logging.INFO)      # logging level
        self.setExcepthook(self.loggingOptions.settings["exception"])

    def init_logger(self, level):
        console = logging.StreamHandler(sys.stdout)
        frm = logging.Formatter("%(asctime)s %(levelname)-8s  %(message)s", "%d.%m.%Y %H:%M:%S")
        console.setFormatter(frm)
        self.log = logging.getLogger("guilog")

        lo = self.loggingOptions
        if lo.settings["file_log"]:
            if lo.settings["log_rotate"]:
                file_handler = logging.handlers.RotatingFileHandler(join(lo.settings["log_folder"], "guilog.txt"), maxBytes=lo.settings["log_size"]*1024, backupCount=lo.settings["log_count"], encoding="utf8")
            else:
                file_handler = logging.FileHandler(join(lo.settings["log_folder"], "guilog.txt"), encoding="utf8")
            file_handler.setFormatter(frm)
            self.log.addHandler(file_handler)

        self.log.addHandler(console) #if console logging
        self.log.setLevel(level)

    def removeLogger(self):
        for h in list(self.log.handlers):
            self.log.removeHandler(h)
            h.close()

    def setupGuiLogTab(self, enabled):
        if enabled:
            self.mainWindow.tabs["guilog"]["text"].setText("")
        else:
            self.mainWindow.tabs["guilog"]["text"].setText(_("File Log is disabled"))
        self.mainWindow.tabs["guilog"]["text"].setEnabled(enabled)
        self.mainWindow.tabs["guilog"]["text"].logOffset = 0
        self.fileLogIsEnabled = enabled

    def initClickNLoadForwarder(self):
        if self.mainWindow.mactions["cnlfwding"].isEnabled():
            settings = self.clickNLoadForwarderOptions.settings
            if settings["enabled"]:
                if settings["getPort"]:
                    port = self.getClickNLoadPortFromCoreSettings()
                    if port == -1:
                        return
                    settings["toPort"] = port
                self.clickNLoadForwarder.start(settings["fromIP"], settings["fromPort"], settings["toIP"], settings["toPort"])

    def getClickNLoadPortFromCoreSettings(self):
        port = -1
        if not self.corePermissions["SETTINGS"]:
            self.messageBox_07()
            return port
        pcfg = self.connector.proxy.getPluginConfig()
        for k, section in pcfg.iteritems():
            if section.name == "ClickNLoad":
                for item in section.items:
                    if item.name == "port":
                        port = int(item.value)
                        break
                break
        return port

    def messageBox_07(self):
        self.slotMsgBoxError(_("Failed to start ClickNLoad port forwarding.\nInsufficient server permissions for 'Get Remote Port from Server Settings'."))

    def startMain(self):
        """
            start all refresh threads and show main window
        """
        self.loadOptionsFromConfig()
        if not self.connector.connectProxy():
            self.init()
            return
        self.connect(self.connector, SIGNAL("connectionLost"), self.slotConnectionLost)
        self.corePermissions = self.getCorePermissions(True)
        self.setCorePermissions()
        self.initClickNLoadForwarder()
        if self.connector.isSSLConnection():
            self.mainWindow.setWindowTitle(self.mainWindow.windowTitle() + " SSL")
        self.mainWindow.newPackDock.hide()
        self.mainWindow.newLinkDock.hide()
        self.mainWindow.newPackDock.setFloating(False)
        self.mainWindow.newLinkDock.setFloating(False)
        self.mainWindow.show()
        self.loadWindowFromConfig() # geometry/state
        if self.geoMaximizeConfig:
            self.mainWindow.showMaximized()
        self.initQueue()
        self.initCollector()
        self.clipboard = self.app.clipboard()
        self.connect(self.clipboard, SIGNAL('dataChanged()'), self.slotClipboardChange)
        self.mainWindow.actions["clipboard"].setChecked(self.checkClipboard)
        self.mainWindow.tabs["settings"]["w"].setConnector(self.connector)
        self.mainWindow.tabs["settings"]["w"].loadConfig()
        self.createTrayIcon()
        if self.mainWindow.trayOptions.settings["EnableTray"]:
            self.tray.show()
        else:
            self.tray.hide()
        self.mainloop.start()
        self.allowUserActions(True)
        self.mainWindow.raise_()
        self.mainWindow.activateWindow()
        self.mainWindow.tabw.setFocus(Qt.OtherFocusReason)

    def stopMain(self):
        """
            stop all refresh threads, save and hide main window
        """
        self.allowUserActions(False)
        self.disconnect(self.clipboard, SIGNAL('dataChanged()'), self.slotClipboardChange)
        self.disconnect(self.connector, SIGNAL("connectionLost"), self.slotConnectionLost)
        self.clickNLoadForwarder.stop()
        self.mainloop.stop()
        self.queue.stop()
        self.prepareForSaveOptionsAndWindow(self.stopMain_continue)

    def stopMain_continue(self):
        self.saveOptionsAndWindowToConfig()
        self.connector.disconnectProxy()
        if self.connectionLost:
            self.log.error("main.stopMain_continue: Lost connection to the server")
            self.messageBox_08()
        self.deleteTrayIcon()
        self.init()

    def messageBox_08(self):
        msg = _("Lost connection to the server!")
        self.msgBoxOk(msg, "C")

    def allowUserActions(self, enabled):
        """
            enable/disable mainWindow, tray icon click and tray icon menu except 'Exit'
        """
        self.mainWindow.setEnabled(enabled)
        self.tray.showAction.setEnabled(enabled)
        if enabled and not self.mainWindow.captchaDialog.isFree():
            self.tray.captchaAction.setEnabled(True)
        else:
            self.tray.captchaAction.setEnabled(False)
        if enabled and self.trayState["hiddenInTray"]:
            self.tray.contextAddMenu.setEnabled(self.corePermissions["ADD"])
        else:
            self.tray.contextAddMenu.setEnabled(False)

    def initCorePermissions(self):
        """
            init permissions dict
        """
        self.corePermissions = {}
        self.corePermissions["admin"] = False
        permkeys = [k for k in dir(PERMS) if not k.startswith("_") and k != "ALL"]
        for k in permkeys:
            self.corePermissions[k] = False

    def getCorePermissions(self, warn):
        """
            returns a dict about our permissions on the core
        """
        perms = {}
        userdata = None
        if self.lastConnection["type"] not in ("local", "internal"):
            userdata = self.connector.getOurUserData()
            if userdata.permission != None:
                perms["admin"] = (userdata.role == ROLE.ADMIN)
            else:
                if warn:
                    self.messageBox_09()
                perms["admin"] = True
        else:
            perms["admin"] = True

        permkeys = [k for k in dir(PERMS) if not k.startswith("_") and k != "ALL"]
        if perms["admin"]:
            for k in permkeys:
                perms[k] = True
        else:
            for k in permkeys:
                perms[k] = has_permission(userdata.permission, getattr(PERMS, k))
        self.log.debug9("Server permissions:")
        self.log.debug9("    admin %s" % perms["admin"])
        self.log.debug9("    ACCOUNTS %s" % perms["ACCOUNTS"])
        self.log.debug9("    ADD      %s" % perms["ADD"])
        self.log.debug9("    DELETE   %s" % perms["DELETE"])
        self.log.debug9("    DOWNLOAD %s" % perms["DOWNLOAD"])
        self.log.debug9("    LIST     %s" % perms["LIST"])
        self.log.debug9("    LOGS     %s" % perms["LOGS"])
        self.log.debug9("    MODIFY   %s" % perms["MODIFY"])
        self.log.debug9("    SETTINGS %s" % perms["SETTINGS"])
        self.log.debug9("    STATUS   %s" % perms["STATUS"])
        return perms

    def messageBox_09(self):
        text = _(
        "Could not get information about our permissions for this remote login!\n\n"
        "This happens when the server is running on the localhost\n"
        "with 'No authentication on local connections' enabled\n"
        "and you try to login with invalid username/password.\n\n"
        "Let us assume we have administrator permissions,\n"
        "since we were allowed to login."
        )
        self.msgBoxOk(text, "W")

    def setCorePermissions(self):
        self.mainWindow.setCorePermissions(self.corePermissions)

    def connectSignals(self):
        """
            signal and slot stuff, yay!
        """
        self.connect(self.connector,           SIGNAL("msgBoxError"), self.slotMsgBoxError)
        self.connect(self.clickNLoadForwarder, SIGNAL("msgBoxError"), self.slotMsgBoxError)
        self.connect(self.connWindow,          SIGNAL("saveConnection"), self.slotSaveConnection)
        self.connect(self.connWindow,          SIGNAL("saveAllConnections"), self.slotSaveAllConnections)
        self.connect(self.connWindow,          SIGNAL("removeConnection"), self.slotRemoveConnection)
        self.connect(self.connWindow,          SIGNAL("connect"), self.slotConnect)
        self.connect(self.connWindow,          SIGNAL("quitConnWindow"), self.slotQuitConnWindow)
        self.connect(self.mainWindow,          SIGNAL("connector"), self.slotShowConnector)
        self.connect(self.mainWindow,          SIGNAL("showCorePermissions"), self.slotShowCorePermissions)
        self.connect(self.mainWindow,          SIGNAL("quitCore"), self.slotQuitCore)
        self.connect(self.mainWindow,          SIGNAL("restartCore"), self.slotRestartCore)
        self.connect(self.mainWindow,          SIGNAL("showLoggingOptions"), self.slotShowLoggingOptions)
        self.connect(self.mainWindow,          SIGNAL("showClickNLoadForwarderOptions"), self.slotShowClickNLoadForwarderOptions)
        self.connect(self.mainWindow,          SIGNAL("showAutomaticReloadingOptions"), self.slotShowAutomaticReloadingOptions)
        self.connect(self.mainWindow,          SIGNAL("showCaptchaOptions"), self.slotShowCaptchaOptions)
        self.connect(self.mainWindow,          SIGNAL("showCaptcha"), self.slotShowCaptcha)
        self.connect(self.mainWindow,          SIGNAL("showFontOptions"), self.slotShowFontOptions)
        self.connect(self.mainWindow,          SIGNAL("showLanguageOptions"), self.slotShowLanguageOptions)
        self.connect(self.mainWindow,          SIGNAL("reloadQueue"), self.slotReloadQueue)
        self.connect(self.mainWindow,          SIGNAL("reloadCollector"), self.slotReloadCollector)
        self.connect(self.mainWindow,          SIGNAL("addPackage"), self.slotAddPackage)
        self.connect(self.mainWindow,          SIGNAL("addLinksToPackage"), self.slotAddLinksToPackage)
        self.connect(self.mainWindow,          SIGNAL("setDownloadStatus"), self.slotSetDownloadStatus)
        self.connect(self.mainWindow,          SIGNAL("pushPackagesToQueue"), self.slotPushPackagesToQueue)
        self.connect(self.mainWindow,          SIGNAL("restartDownloads"), self.slotRestartDownloads)
        self.connect(self.mainWindow,          SIGNAL("removeDownloads"), self.slotRemoveDownloads)
        self.connect(self.mainWindow,          SIGNAL("editPackages"), self.slotEditPackages)
        self.connect(self.mainWindow,          SIGNAL("abortDownloads"), self.slotAbortDownloads)
        self.connect(self.mainWindow,          SIGNAL("selectAllPackages"), self.slotSelectAllPackages)
        self.connect(self.mainWindow,          SIGNAL("expandAll"), self.slotExpandAll)
        self.connect(self.mainWindow,          SIGNAL("collapseAll"), self.slotCollapseAll)
        self.connect(self.mainWindow,          SIGNAL("addContainer"), self.slotAddContainer)
        self.connect(self.mainWindow,          SIGNAL("stopAllDownloads"), self.slotStopAllDownloads)
        self.connect(self.mainWindow,          SIGNAL("setClipboardStatus"), self.slotSetClipboardStatus)
        self.connect(self.mainWindow,          SIGNAL("restartFailed"), self.slotRestartFailed)
        self.connect(self.mainWindow,          SIGNAL("deleteFinished"), self.slotDeleteFinished)
        self.connect(self.mainWindow,          SIGNAL("pullOutPackages"), self.slotPullOutPackages)
        self.connect(self.mainWindow,          SIGNAL("reloadAccounts"), self.slotReloadAccounts)
        self.connect(self.mainWindow,          SIGNAL("showAbout"), self.slotShowAbout)
        self.connect(self.mainWindow,          SIGNAL("Quit"), self.slotQuit)

        self.connect(self.mainWindow.mactions["exit"], SIGNAL("triggered()"), self.slotQuit)
        self.connect(self.mainWindow.captchaDialog, SIGNAL("done"), self.slotCaptchaDone)

        self.packageEdit.connect(self.packageEdit.saveBtn, SIGNAL("clicked()"), self.slotEditPackageSave)

    def createTrayIcon(self):
        self.trayState = {"p": {"f": False, "h": False, "f&!h": False}, "l": {"f": False, "h": False, "f&!h": False}}
        self.trayState["hiddenInTray"] = False
        self.trayState["ignoreMinimizeToggled"] = False
        self.tray = TrayIcon()
        self.notification = Notification(self.tray)
        self.connect(self, SIGNAL("showMessage"),           self.notification.showMessage)
        self.connect(self, SIGNAL("minimize2Tray"),         self.slotMinimize2Tray, Qt.QueuedConnection)
        self.connect(self, SIGNAL("traySetShowActionText"), self.tray.setShowActionText)
        self.connect(self.tray,                     SIGNAL("activated(QSystemTrayIcon::ActivationReason)"), self.tray.clicked)
        self.connect(self.tray.showAction,          SIGNAL("triggered()"), self.slotToggleShowFromHideInTray)
        self.connect(self.tray.captchaAction,       SIGNAL("triggered()"), self.slotShowCaptcha)
        self.connect(self.tray.addPackageAction,    SIGNAL("triggered()"), self.slotShowAddPackageFromTray)
        self.connect(self.tray.addContainerAction,  SIGNAL("triggered()"), self.mainWindow.slotShowAddContainer)
        self.connect(self.tray.addLinksAction,      SIGNAL("triggered()"), self.slotShowAddLinksFromTray)
        self.connect(self.tray.exitAction,          SIGNAL("triggered()"), self.slotQuit)
        if self.log.isEnabledFor(logging.DEBUG9):
            self.connect(self.tray.debugTrayAction,   SIGNAL("triggered()"), self.debugTray)
            self.connect(self.tray.debugMsgboxAction, SIGNAL("triggered()"), self.debugMsgBoxTest)
        self.connect(self.mainWindow, SIGNAL("showTrayIcon"),    self.tray.show)
        self.connect(self.mainWindow, SIGNAL("hideTrayIcon"),    self.tray.hide)
        self.connect(self.mainWindow, SIGNAL("hideInTray"),      self.hideInTray)
        self.connect(self.mainWindow, SIGNAL("minimizeToggled"), self.slotMinimizeToggled)

    def deleteTrayIcon(self):
        self.disconnect(self, SIGNAL("showMessage"),           self.notification.showMessage)
        self.disconnect(self, SIGNAL("minimize2Tray"),         self.slotMinimize2Tray)
        self.disconnect(self, SIGNAL("traySetShowActionText"), self.tray.setShowActionText)
        self.disconnect(self.tray,                     SIGNAL("activated(QSystemTrayIcon::ActivationReason)"), self.tray.clicked)
        self.disconnect(self.tray.showAction,          SIGNAL("triggered()"), self.slotToggleShowFromHideInTray)
        self.disconnect(self.tray.captchaAction,       SIGNAL("triggered()"), self.slotShowCaptcha)
        self.disconnect(self.tray.addPackageAction,    SIGNAL("triggered()"), self.slotShowAddPackageFromTray)
        self.disconnect(self.tray.addContainerAction,  SIGNAL("triggered()"), self.mainWindow.slotShowAddContainer)
        self.disconnect(self.tray.addLinksAction,      SIGNAL("triggered()"), self.slotShowAddLinksFromTray)
        self.disconnect(self.tray.exitAction,          SIGNAL("triggered()"), self.slotQuit)
        if self.log.isEnabledFor(logging.DEBUG9):
            self.disconnect(self.tray.debugTrayAction,   SIGNAL("triggered()"), self.debugTray)
            self.disconnect(self.tray.debugMsgboxAction, SIGNAL("triggered()"), self.debugMsgBoxTest)
        self.disconnect(self.mainWindow, SIGNAL("showTrayIcon"),    self.tray.show)
        self.disconnect(self.mainWindow, SIGNAL("hideTrayIcon"),    self.tray.hide)
        self.disconnect(self.mainWindow, SIGNAL("hideInTray"),      self.hideInTray)
        self.disconnect(self.mainWindow, SIGNAL("minimizeToggled"), self.slotMinimizeToggled)
        self.tray.contextMenu.deleteLater()
        self.tray.setContextMenu(None)
        self.tray.deleteLater()
        self.tray = None

    def slotToggleShowFromHideInTray(self):
        """
            triggered from tray icon showAction
        """
        if self.trayState["hiddenInTray"]:
            self.showFromTray()
        elif self.mainWindow.isMinimized():
            # mainWindow is minimized in the taskbar
            self.mainWindow.show()
            self.mainWindow.raise_()
            self.mainWindow.activateWindow()
        else:
            self.hideInTray()

    def hideInTray(self):
        """
            hide main window and docks in the tray
            - called from slotToggleShowFromHideInTray()
            - called from slotMinimize2Tray()
            - emitted from main window on close button hit
        """
        if self.trayState["hiddenInTray"]:
            self.log.error("main.hideInTray: Already hidden in tray")
            return
        self.log.debug4("main.hideInTray: triggered")
        self.allowUserActions(False)
        self.trayState["maximized"] = self.mainWindow.isMaximized()
        if self.mainWindow.otherOptions.settings["Unmaximize"] and self.trayState["maximized"]:
            self.unmaximizeWait(self.hideInTray_continue)
        else:
            self.hideInTray_continue()

    def hideInTray_continue(self):
        s = self.trayState
        s["geo"] = self.mainWindow.saveGeometry()
        s["state"] = self.mainWindow.saveState()
        s["p"]["f"] = self.mainWindow.newPackDock.isFloating()
        s["p"]["h"] = self.mainWindow.newPackDock.isHidden()
        s["p"]["f&!h"] = s["p"]["f"] and not s["p"]["h"]
        s["l"]["f"] = self.mainWindow.newLinkDock.isFloating()
        s["l"]["h"] = self.mainWindow.newLinkDock.isHidden()
        s["l"]["f&!h"] = s["l"]["f"] and not s["l"]["h"]
        self.trayState["ignoreMinimizeToggled"] = True
        self.mainWindow.hide()
        self.mainWindow.newPackDock.hide()
        self.mainWindow.newLinkDock.hide()
        self.trayState["ignoreMinimizeToggled"] = False
        self.emit(SIGNAL("traySetShowActionText"), True)
        self.trayState["hiddenInTray"] = True   # must be updated before allowUserActions(True)
        self.allowUserActions(True)

    def showFromTray(self, prepForSave=False):
        """
            restore main window and docks from hidden in the tray
            - called from slotToggleShowFromHideInTray()
            - called from prepareForSaveOptionsAndWindow()
        """
        if not self.trayState["hiddenInTray"]:
            self.log.error("main.showFromTray: Not hidden in tray")
            return
        self.log.debug4("main.showFromTray: triggered, prepForSave: %s" % prepForSave)
        self.allowUserActions(False)
        s = self.trayState
        pe = self.app.processEvents
        # hide and dock in case they were shown via the tray icon menu
        pe(); self.mainWindow.newPackDock.hide()
        pe(); self.mainWindow.newLinkDock.hide()
        pe(); self.mainWindow.newPackDock.setFloating(False)
        pe(); self.mainWindow.newLinkDock.setFloating(False)
        pe(); self.mainWindow.show()
        if not self.mainWindow.trayOptions.settings["AltMethod"]:
            pe(); self.mainWindow.restoreState(s["state"]) # docks
            pe(); self.mainWindow.restoreGeometry(s["geo"])
        else: # alternative method
            pe(); self.mainWindow.newPackDock.setHidden(s["p"]["h"])
            pe(); self.mainWindow.newLinkDock.setHidden(s["l"]["h"])
            pe(); self.mainWindow.newPackDock.setFloating(s["p"]["f"])
            pe(); self.mainWindow.newLinkDock.setFloating(s["l"]["f"])
            pe(); self.mainWindow.restoreGeometry(s["geo"])
        if prepForSave:
            pe(); self.mainWindow.show()    # an extra show
            self.emit(SIGNAL("traySetShowActionText"), False)
            self.trayState["hiddenInTray"] = False
            pe(); return
        if self.mainWindow.otherOptions.settings["Unmaximize"] and s["maximized"]:
            pe(); self.maximizeWait(self.showFromTray_continue)
        else:
            pe(); self.mainWindow.show()    # an extra show
            self.showFromTray_continue()

    def showFromTray_continue(self):
        pe = self.app.processEvents
        pe(); self.mainWindow.raise_()
        pe(); self.mainWindow.activateWindow()
        pe(); self.mainWindow.tabw.setFocus(Qt.OtherFocusReason)
        pe(); self.emit(SIGNAL("traySetShowActionText"), False)
        self.trayState["hiddenInTray"] = False  # must be updated before allowUserActions(True)
        self.allowUserActions(True)

    def slotMinimizeToggled(self, minimized):
        """
            emitted from main window in changeEvent()
        """
        if self.tray is None:
            return
        if not self.mainWindow.trayOptions.settings["EnableTray"]:
            return
        if self.trayState["hiddenInTray"]:
            return
        if self.trayState["ignoreMinimizeToggled"]:
            return
        # sanity check
        if self.mainWindow.numOfOpenModalDialogs < 0:
            self.log.error("main.slotMinimizeToggled: numOfOpenModalDialogs < 0")
            return
        self.log.debug4("main.slotMinimizeToggled: %s" % minimized)
        if minimized:   # minimized flag was set
            if self.mainWindow.numOfOpenModalDialogs > 0:
                if self.mainWindow.isMaximized():
                    QTimer.singleShot(100, self.mainWindow.showMaximized)
                else:
                    QTimer.singleShot(100, self.mainWindow.showNormal)
            elif self.mainWindow.trayOptions.settings["Minimize2Tray"]:
                self.emit(SIGNAL("minimize2Tray"))   # queued connection
        else:           # minimized flag was unset
            pass

    def slotMinimize2Tray(self):
        """
            emitted from slotMinimizeToggled()
        """
        if self.trayState["hiddenInTray"]:
            self.log.error("main.slotMinimize2Tray: Already hidden in tray")
            return
        self.log.debug4("main.slotMinimize2Tray: triggered")
        self.hideInTray()

    def debugTray(self):
        self.log.debug9("mainWindow:")
        self.log.debug9("  hidden    %s" % self.mainWindow.isHidden())
        self.log.debug9("  visible   %s" % self.mainWindow.isVisible())
        self.log.debug9("  minimized %s" % self.mainWindow.isMinimized())
        self.log.debug9("  maximized %s" % self.mainWindow.isMaximized())
        self.log.debug9("  enabled   %s" % self.mainWindow.isEnabled())
        self.log.debug9("  activated %s" % self.mainWindow.isActiveWindow())
        self.log.debug9("newPackDock:")
        self.log.debug9("  floating  %s" % self.mainWindow.newPackDock.isFloating())
        self.log.debug9("  hidden    %s" % self.mainWindow.newPackDock.isHidden())
        self.log.debug9("  visible   %s" % self.mainWindow.newPackDock.isVisible())
        self.log.debug9("  minimized %s" % self.mainWindow.newPackDock.isMinimized())
        self.log.debug9("  maximized %s" % self.mainWindow.newPackDock.isMaximized())
        self.log.debug9("  enabled   %s" % self.mainWindow.newPackDock.isEnabled())
        self.log.debug9("  activated %s" % self.mainWindow.newPackDock.isActiveWindow())
        self.log.debug9("newLinkDock:")
        self.log.debug9("  floating  %s" % self.mainWindow.newLinkDock.isFloating())
        self.log.debug9("  hidden    %s" % self.mainWindow.newLinkDock.isHidden())
        self.log.debug9("  visible   %s" % self.mainWindow.newLinkDock.isVisible())
        self.log.debug9("  minimized %s" % self.mainWindow.newLinkDock.isMinimized())
        self.log.debug9("  maximized %s" % self.mainWindow.newLinkDock.isMaximized())
        self.log.debug9("  enabled   %s" % self.mainWindow.newLinkDock.isEnabled())
        self.log.debug9("  activated %s" % self.mainWindow.newLinkDock.isActiveWindow())

    def initMaxiUnmaxiWait(self):
        self.initMaximizeWait()
        self.initUnmaximizeWait()

    def initMaximizeWait(self):
        timeoutError   = 7000   # milliseconds, integer multiple of updateInterval
        updateInterval = 350    # milliseconds
        self.maxiWait = {}
        self.maxiWait["timer"] = QTimer()
        self.maxiWait["timer"].setInterval(updateInterval)
        self.maxiWait["timerCountDownStartVal"] = timeoutError / updateInterval

    def maximizeWait(self, contFunc):
        """
            maximize mainWindow and call contFunc() when its done
        """
        # sanity checks
        if self.mainWindow.isHidden():
            self.log.error("main.maximizeWait: mainWindow is hidden"); contFunc(); return
        if self.mainWindow.isMaximized():
            self.log.error("main.maximizeWait: mainWindow is already maximized"); contFunc(); return
        self.maxiWait["contFunc"] = contFunc
        self.connect(self.mainWindow, SIGNAL("maximizeDone"), self.slotMaximizeWaitDone, Qt.QueuedConnection)
        self.mainWindow.showMaximized()
        self.maxiWait["timerCountDown"] = self.maxiWait["timerCountDownStartVal"]
        self.maxiWait["timer"].connect(self.maxiWait["timer"], SIGNAL("timeout()"), self.slotMaximizeWaitTimer)
        self.maxiWait["timer"].start()

    def slotMaximizeWaitTimer(self):
        self.maxiWait["timerCountDown"] -= 1
        if self.maxiWait["timerCountDown"] > 0:
            self.log.debug4("main.slotMaximizeWaitTimer: update, schedule a paintEvent")
            self.mainWindow.update()
        else:
            self.disconnect(self.mainWindow, SIGNAL("maximizeDone"), self.slotMaximizeWaitDone)
            self.maxiWait["timer"].stop()
            self.maxiWait["timer"].disconnect(self.maxiWait["timer"], SIGNAL("timeout()"), self.slotMaximizeWaitTimer)
            self.messageBox_10()
            self.maxiWait["contFunc"]()

    def messageBox_10(self):
        text  = _("Timeout detecting main window maximize state") + ".\n\n"
        text += _("The option") + " '" + self.mainWindow.otherOptions.cbUnmaximze.text() + "' " + _("failed") + ". "
        text += _("If this happens again, you may turn it off from the") + " '" + _("Options") + " -> " + _("Other") + "' " + _("menu") + "."
        self.msgBoxOk(text, "C")

    def slotMaximizeWaitDone(self):
        self.maxiWait["timer"].stop()
        self.maxiWait["timer"].disconnect(self.maxiWait["timer"], SIGNAL("timeout()"), self.slotMaximizeWaitTimer)
        self.disconnect(self.mainWindow, SIGNAL("maximizeDone"), self.slotMaximizeWaitDone)
        self.log.debug4("main.slotMaximizeWaitDone: done")
        self.maxiWait["contFunc"]()

    def initUnmaximizeWait(self):
        timeoutError   = 7000   # milliseconds, integer multiple of updateInterval
        updateInterval = 350    # milliseconds
        self.unmaxiWait = {}
        self.unmaxiWait["timer"] = QTimer()
        self.unmaxiWait["timer"].setInterval(updateInterval)
        self.unmaxiWait["timerCountDownStartVal"] = timeoutError / updateInterval

    def unmaximizeWait(self, contFunc):
        """
            unmaximize mainWindow and call contFunc() when its done
        """
        # sanity checks
        if self.mainWindow.isHidden():
            self.log.error("main.unmaximizeWait: mainWindow is hidden"); contFunc(); return
        if not self.mainWindow.isMaximized():
            self.log.error("main.unmaximizeWait: mainWindow is not maximized"); contFunc(); return
        self.unmaxiWait["contFunc"] = contFunc
        self.connect(self.mainWindow, SIGNAL("unmaximizeDone"), self.slotUnmaximizeWaitDone, Qt.QueuedConnection)
        self.mainWindow.showNormal()
        self.unmaxiWait["timerCountDown"] = self.unmaxiWait["timerCountDownStartVal"]
        self.unmaxiWait["timer"].connect(self.unmaxiWait["timer"], SIGNAL("timeout()"), self.slotUnmaximizeWaitTimer)
        self.unmaxiWait["timer"].start()

    def slotUnmaximizeWaitTimer(self):
        self.unmaxiWait["timerCountDown"] -= 1
        if self.unmaxiWait["timerCountDown"] > 0:
            self.log.debug4("main.slotUnmaximizeWaitTimer: update, schedule a paintEvent")
            self.mainWindow.update()
        else:
            self.disconnect(self.mainWindow, SIGNAL("unmaximizeDone"), self.slotUnmaximizeWaitDone)
            self.unmaxiWait["timer"].stop()
            self.unmaxiWait["timer"].disconnect(self.unmaxiWait["timer"], SIGNAL("timeout()"), self.slotUnmaximizeWaitTimer)
            self.messageBox_11()
            self.unmaxiWait["contFunc"]()

    def messageBox_11(self):
        text  = _("Timeout detecting main window unmaximize state") + ".\n\n"
        text += _("The option") + " '" + self.mainWindow.otherOptions.cbUnmaximze.text() + "' " + _("failed") + ". "
        text += _("If this happens again, you may turn it off from the") + " '" + _("Options") + " -> " + _("Other") + "' " + _("menu") + "."
        self.msgBoxOk(text, "C")

    def slotUnmaximizeWaitDone(self):
        self.unmaxiWait["timer"].stop()
        self.unmaxiWait["timer"].disconnect(self.unmaxiWait["timer"], SIGNAL("timeout()"), self.slotUnmaximizeWaitTimer)
        self.disconnect(self.mainWindow, SIGNAL("unmaximizeDone"), self.slotUnmaximizeWaitDone)
        self.log.debug4("main.slotUnmaximizeWaitDone: done")
        self.unmaxiWait["contFunc"]()

    def slotShowAddPackageFromTray(self):
        """
            triggered from tray icon (context menu)
            show floating new-package dock when the application is hidden in the systemtray
        """
        if not self.trayState["hiddenInTray"]:
            self.log.error("main.slotShowAddPackageFromTray: Not hidden in tray")
            return
        pe = self.app.processEvents
        pe(); self.mainWindow.newLinkDock.setFloating(False)
        pe(); self.mainWindow.newPackDock.setFloating(True)
        pe(); self.mainWindow.newPackDock.show()
        pe(); self.mainWindow.newPackDock.raise_()
        pe(); self.mainWindow.newPackDock.activateWindow()

    def slotShowAddLinksFromTray(self):
        """
            triggered from tray icon (context menu)
            show floating new-links dock when the application is hidden in the systemtray
        """
        if not self.trayState["hiddenInTray"]:
            self.log.error("main.slotShowAddLinksFromTray: Not hidden in tray")
            return
        pe = self.app.processEvents
        pe(); self.mainWindow.newPackDock.setFloating(False)
        pe(); self.mainWindow.newLinkDock.setFloating(True)
        pe(); self.mainWindow.newLinkDock.show()
        pe(); self.mainWindow.newLinkDock.raise_()
        pe(); self.mainWindow.newLinkDock.activateWindow()

    def slotShowCaptcha(self):
        """
            from main window (menu)
            from tray icon (context menu)
            show captcha
        """
        self.mainWindow.captchaDialog.emit(SIGNAL("show"))

    def slotShowAbout(self):
        """
            emitted from main window (menu)
            show the about-box
        """
        ab = AboutBox(self.mainWindow)
        self.mainWindow.numOfOpenModalDialogs += 1
        ab.exec_(CURRENT_VERSION, CURRENT_INTERNAL_VERSION)
        self.mainWindow.numOfOpenModalDialogs -= 1

    def slotShowConnector(self):
        """
            emitted from main window (menu)
            hide the main window and show connection manager
            (to switch to other core)
        """
        self.quitInternal()
        self.stopMain()

    def slotShowCorePermissions(self):
        """
            emitted from main window (menu)
            show permissions info-box
        """
        perms = self.getCorePermissions(False)
        info = InfoCorePermissions(self.mainWindow, perms, self.corePermissions)
        self.mainWindow.numOfOpenModalDialogs += 1
        info.exec_()
        self.mainWindow.numOfOpenModalDialogs -= 1

    def slotQuitCore(self):
        """
            emitted from main window (menu)
            quit the pyLoad Core
        """
        if not self.corePermissions["admin"]:
            return
        if self.messageBox_12():
            self.disconnect(self.connector, SIGNAL("connectionLost"), self.slotConnectionLost)
            self.connector.proxy.kill()
            self.slotShowConnector()

    def messageBox_12(self):
        text = _("Do you really want to quit the pyLoad server?")
        return self.msgBoxYesNo(text, "I")

    def slotRestartCore(self):
        """
            emitted from main window (menu)
            restart the pyLoad Core
        """
        if not self.corePermissions["admin"]:
            return
        if self.messageBox_13():
            self.disconnect(self.connector, SIGNAL("connectionLost"), self.slotConnectionLost)
            self.connector.proxy.restart()
            self.slotShowConnector()

    def messageBox_13(self):
        text = _("Do you really want to restart the pyLoad server?")
        return self.msgBoxYesNo(text, "I")

    def slotReloadQueue(self):
        """
            emitted from main window (menu)
            force reload queue tab
        """
        self.queue.fullReloadFromMenu()

    def slotReloadCollector(self):
        """
            emitted from main window (menu)
            force reload collector tab
        """
        self.collector.fullReloadFromMenu()

    def loop(self):
        """
            start application loop
        """
        sys.exit(self.app.exec_())

    def msgBox(self, text, icon, btnSet):
        if self.mainWindow.isMinimized() and (self.tray is None or not self.trayState["hiddenInTray"]):
            if self.mainWindow.isMaximized():
                self.mainWindow.showMaximized()
            else:
                self.mainWindow.showNormal()
        msgb = MessageBox(self.mainWindow, text, icon, btnSet)
        self.mainWindow.numOfOpenModalDialogs += 1
        retval = msgb.exec_()
        self.mainWindow.numOfOpenModalDialogs -= 1
        return retval 

    def msgBoxOk(self, text, icon):
        self.msgBox(text, icon, "OK")

    def msgBoxOkCancel(self, text, icon):
        return self.msgBox(text, icon, "OK_CANCEL")

    def msgBoxYesNo(self, text, icon):
        return self.msgBox(text, icon, "YES_NO")

    def slotMsgBoxError(self, text):
        """
            display an error message box
        """
        self.msgBoxOk(text, "C")

    def debugMsgBoxTest(self):
        def msgboxes(line):
            l = line + "1"
            self.msgBox(l, icon, btnSet)
            for n in range(1, 5):
                l += "\n" + line + str(n + 1)
                self.msgBox(l, icon, btnSet)
        def tests():
            line = "Line"
            msgboxes(line)
            line = "LongXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXLine"
            msgboxes(line)
            line = "WrappedXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXLine"
            msgboxes(line)
            line = "3xWrappedXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXLine"
            msgboxes(line)
        self.msgBox("!", "Q", "OK")
        self.msgBox("!", "I", "OK")
        self.msgBox("!", "W", "OK")
        self.msgBox("!", "C", "OK_CANCEL")
        self.msgBox("!", "N", "YES_NO")
        icon = "C"
        btnSet = "OK"
        tests()
        icon = "N"
        btnSet = "YES_NO"
        tests()

    def slotNotificationMessage(self, status, name):
        """
            notifications
        """
        s = self.mainWindow.notificationOptions.settings
        if s["EnableNotify"]:
            if status == 100:
                if s["PackageFinished"]:
                    self.emit(SIGNAL("showMessage"), _("Package download finished") + ": %s" % name)
            elif status == DownloadStatus.Finished:
                if s["Finished"]:
                    self.emit(SIGNAL("showMessage"), _("Download finished") + ": %s" % name)
            elif status == DownloadStatus.Offline:
                if s["Offline"]:
                    self.emit(SIGNAL("showMessage"), _("Download offline") + ": %s" % name)
            elif status == DownloadStatus.Skipped:
                if s["Skipped"]:
                    self.emit(SIGNAL("showMessage"), _("Download skipped") + ": %s" % name)
            elif status == DownloadStatus.TempOffline:
                if s["TempOffline"]:
                    self.emit(SIGNAL("showMessage"), _("Download temporarily offline") + ": %s" % name)
            elif status == DownloadStatus.Failed:
                if s["Failed"]:
                    self.emit(SIGNAL("showMessage"), _("Download failed") + ": %s" % name)
            elif status == DownloadStatus.Aborted:
                if s["Aborted"]:
                    self.emit(SIGNAL("showMessage"), _("Download aborted") + ": %s" % name)
            elif status == 101:
                if s["Captcha"]:
                    self.emit(SIGNAL("showMessage"), _("Captcha arrived"))

    def initCollector(self):
        """
            init the collector view
            * columns
            * selection
            * refresh thread
            * drag'n'drop
        """
        view = self.mainWindow.tabs["collector"]["view"]
        
        view.setAlternatingRowColors(True)
        view.setAutoScrollMargin(24) # default is 16
        view.setDragDropMode(QAbstractItemView.InternalMove)
        view.setHorizontalScrollMode(QAbstractItemView.ScrollPerItem)
        view.setSelectionBehavior(QAbstractItemView.SelectRows)
        view.setSelectionMode(QAbstractItemView.ExtendedSelection)
        view.setDragEnabled(True)
        view.setDropIndicatorShown(False)
        view.setAllColumnsShowFocus(True)
        view.setUniformRowHeights(True)
        
        self.collector = view.model
        self.connect(self.collector, SIGNAL("notificationMessage"), self.slotNotificationMessage)

    def initQueue(self):
        """
            init the queue view
            * columns
            * progressbar
        """
        view = self.mainWindow.tabs["queue"]["view"]
        
        view.setAlternatingRowColors(True)
        view.setAutoScrollMargin(24) # default is 16
        view.setDragDropMode(QAbstractItemView.InternalMove)
        view.setHorizontalScrollMode(QAbstractItemView.ScrollPerItem)
        view.setSelectionBehavior(QAbstractItemView.SelectRows)
        view.setSelectionMode(QAbstractItemView.ExtendedSelection)
        view.setDragEnabled(True)
        view.setDropIndicatorShown(False)
        view.setAllColumnsShowFocus(True)
        view.setUniformRowHeights(True)
        
        self.queue = view.model
        self.connect(self.queue, SIGNAL("updateCount"), self.slotUpdateCount)
        self.connect(self.queue, SIGNAL("updateCount"), self.mainWindow.tabs["overview"]["view"].model.queueChanged)
        self.connect(self.queue, SIGNAL("notificationMessage"), self.slotNotificationMessage)
        self.queue.start()
    
    def slotUpdateCount(self, pc, fc):
        self.mainWindow.packageCount.setText("%i" % pc)
        self.mainWindow.fileCount.setText("%i" % fc)
    
    def refreshServerStatus(self):
        """
            refresh server status and overall speed in the status bar
        """
        if not self.corePermissions["LIST"]:
            return
        s = self.connector.proxy.statusServer()
        if s.pause:
            self.mainWindow.status.setText(_("Paused"))
        else:
            self.mainWindow.status.setText(_("Running"))
        self.mainWindow.speed.setText(formatSpeed(s.speed))
        self.mainWindow.space.setText(formatSize(self.serverStatus["freespace"]))
        self.mainWindow.actions["toggle_status"].setChecked(not s.pause)

    def getGuiLog(self, offset=0):
        """
            returns most recent gui log entries
        """
        filename = join(self.loggingOptions.settings["log_folder"], "guilog.txt")
        try:
            fh = open(filename, "r")
            lines = fh.readlines()
            fh.close()
        except:
            return ['No log available'], True
        if offset == len(lines):
            return [], False
        if offset < len(lines):
            return lines[offset:], False
        filename += ".1"
        try:
            fh = open(filename, "r")
            oldlines = fh.readlines()
            fh.close()
        except:
            return [], True
        if offset >= len(oldlines):
            return [], True
        return oldlines[offset:], True

    def refreshGuiLog(self):
        """
            update gui log window
        """
        QMutexLocker(self.guiLogMutex)
        if not self.fileLogIsEnabled:
            return
        offset = self.mainWindow.tabs["guilog"]["text"].logOffset
        lines, logrot = self.getGuiLog(offset)
        if logrot:
            self.mainWindow.tabs["guilog"]["text"].logOffset = 0
        if not lines:
            return
        if not logrot:
            self.mainWindow.tabs["guilog"]["text"].logOffset += len(lines)
        for line in lines:
            self.mainWindow.tabs["guilog"]["text"].emit(SIGNAL("append(QString)"), line.strip("\n"))
        cursor = self.mainWindow.tabs["guilog"]["text"].textCursor()
        cursor.movePosition(QTextCursor.End, QTextCursor.MoveAnchor)
        cursor.movePosition(QTextCursor.StartOfLine, QTextCursor.MoveAnchor)
        self.mainWindow.tabs["guilog"]["text"].setTextCursor(cursor)

    def refreshCoreLog(self):
        """
            update core log window
        """
        if not self.corePermissions["LOGS"]:
            return
        offset = self.mainWindow.tabs["corelog"]["text"].logOffset
        if offset == 0:
            lines = self.connector.proxy.getLog(offset)
            if not lines: # zero size log file
                return
            self.mainWindow.tabs["corelog"]["text"].logOffset += len(lines)
        else:
            lines = self.connector.proxy.getLog(offset - 1)
            if not lines:
                lines = [_("************ Log Rotation - Possibly, one or more lines are not shown here ************")]
                self.mainWindow.tabs["corelog"]["text"].logOffset = 0
            elif len(lines) == 1: # no new log entries
                return
            else: # got new log entries
                del lines[0]
                self.mainWindow.tabs["corelog"]["text"].logOffset += len(lines)
        for line in lines:
            self.mainWindow.tabs["corelog"]["text"].emit(SIGNAL("append(QString)"), line.strip("\n"))
        cursor = self.mainWindow.tabs["corelog"]["text"].textCursor()
        cursor.movePosition(QTextCursor.End, QTextCursor.MoveAnchor)
        cursor.movePosition(QTextCursor.StartOfLine, QTextCursor.MoveAnchor)
        self.mainWindow.tabs["corelog"]["text"].setTextCursor(cursor)

    def loadAllConnections(self):
        """
            parse all connections in the config file
        """
        connectionsNode = self.parser.xml.elementsByTagName("connections").item(0)
        if connectionsNode.isNull():
            raise Exception("null")
        connections = self.parser.parseNode(connectionsNode)
        ret = []
        for conn in connections:
            data = {}
            data["type"] = str(conn.attribute("type", "remote"))
            data["default"] = str(conn.attribute("default", "False"))
            data["id"] = str(conn.attribute("id", uuid().hex))
            if data["default"] == "True":
                data["default"] = True
            else:
                data["default"] = False
            subs = self.parser.parseNode(conn, "dict")
            if not subs.has_key("name"):
                data["name"] = str(_("Unnamed"))
            else:
                data["name"] = str(subs["name"].text())
            if data["type"] == "remote":
                if not subs.has_key("server"):
                    continue
                else:
                    data["host"] = str(subs["server"].text())
                    data["user"] = str(subs["server"].attribute("user", "admin"))
                    data["port"] = int(subs["server"].attribute("port", "7227"))
                    data["password"] = str(subs["server"].attribute("password", ""))
                    data["cnlpf"] = str(subs["server"].attribute("cnlpf", "False"))
                    if data["cnlpf"] == "True":
                        data["cnlpf"] = True
                    else:
                        data["cnlpf"] = False
                    data["cnlpfPort"] = int(subs["server"].attribute("cnlpfPort", "9666"))
                    data["cnlpfGetPort"] = str(subs["server"].attribute("cnlpfGetPort", "False"))
                    if data["cnlpfGetPort"] == "True":
                        data["cnlpfGetPort"] = True
                    else:
                        data["cnlpfGetPort"] = False
            ret.append(data)
        return ret

    def slotSaveAllConnections(self, connections):
        """
            save all connections to config file
            reload connections and display them
        """
        connectionsNode = self.parser.xml.elementsByTagName("connections").item(0)
        if connectionsNode.isNull():
            raise Exception("null")
        conn = self.parser.parseNode(connectionsNode)
        for c in conn:
            connectionsNode.removeChild(c)
        for data in connections:
            self.parseConnection(data)
        self.parser.saveData()
        self.refreshConnections()

    def slotSaveConnection(self, data):
        """
            save connection to config file
            reload connections and display them
        """
        try:
            self.parseConnection(data)
            self.parser.saveData()
        except:
            raise RuntimeError("Failed to save the data to the configuration file")
        self.refreshConnections()

    def parseConnection(self, data):
        """
            update or append a connection
        """
        connectionsNode = self.parser.xml.elementsByTagName("connections").item(0)
        if connectionsNode.isNull():
            raise Exception("null")
        connections = self.parser.parseNode(connectionsNode)
        connNode = self.parser.xml.createElement("connection")
        connNode.setAttribute("default", str(data["default"]))
        connNode.setAttribute("type", data["type"])
        connNode.setAttribute("id", data["id"])
        nameNode = self.parser.xml.createElement("name")
        name = data["name"].strip()
        if not name:
            name = _("UNNAMED CONNECTION")
        nameText = self.parser.xml.createTextNode(name)
        nameNode.appendChild(nameText)
        connNode.appendChild(nameNode)
        if data["type"] == "remote":
            serverNode = self.parser.xml.createElement("server")
            serverNode.setAttribute("user", data["user"])
            serverNode.setAttribute("port", str(data["port"]))
            serverNode.setAttribute("password", data["password"])
            serverNode.setAttribute("cnlpf", str(data["cnlpf"]))
            serverNode.setAttribute("cnlpfPort", str(data["cnlpfPort"]))
            serverNode.setAttribute("cnlpfGetPort", str(data["cnlpfGetPort"]))
            host = data["host"].replace(" ", "")
            hostText = self.parser.xml.createTextNode(host)
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

    def slotRemoveConnection(self, data):
        """
            remove connection from config file
        """
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
        """
            connect to a core
            if connection is local, parse the core config file for data
            if internal, start pyLoadCore
            set up connector, show main window
        """
        self.connWindow.hide()
        self.lastConnection = data.copy()

        if data["type"] not in ("remote", "internal"):
            coreparser = ConfigParser(self.configdir)
            if not coreparser.config:
                self.connector.setConnectionData("127.0.0.1", 7227, "anonymous", "anonymous")
                title = _("pyLoad Client") + " - " + data["name"] + " [127.0.0.1:7227]"
            else:
                self.connector.setConnectionData("127.0.0.1", coreparser.get("remote", "port"), "anonymous", "anonymous")
                title = _("pyLoad Client") + " - " + data["name"] + " [127.0.0.1:" + str(coreparser.get("remote", "port")) + "]"
            self.mainWindow.setWindowTitle(title)
            self.mainWindow.mactions["cnlfwding"].setEnabled(False)

        elif data["type"] == "remote":
            self.connector.setConnectionData(data["host"], data["port"], data["user"], data["password"])
            self.clickNLoadForwarderOptions.settings["enabled"] = data["cnlpf"]
            self.clickNLoadForwarderOptions.settings["toIP"] = data["host"]
            self.clickNLoadForwarderOptions.settings["toPort"] = data["cnlpfPort"]
            self.clickNLoadForwarderOptions.settings["getPort"] = data["cnlpfGetPort"]
            title = _("pyLoad Client") + " - " + data["name"] + " [" + data["host"] + ":" + str(data["port"]) + "]"
            self.mainWindow.setWindowTitle(title)

        elif data["type"] == "internal":
            from pyLoadCore import Core
            from module.ConfigParser import ConfigParser as CoreConfig

            if not self.core:
                class Core_(Core):
                    """
                        Workaround os._exit() called when the Core quits.
                        This is possible because the present Core code calls
                        os._exit() right after calling removeLogger()
                    """
                    def removeLogger(self):
                         Core.removeLogger(self)
                         thread.exit()

                del sys.argv[1:] # do not pass our command-line arguments to the core
                #sys.argv[1:2] = ["--foo=bar", "--debug"] # pass these instead

                try:
                    self.core = Core_()
                except:
                    return self.errorInternalCoreStartup(self.messageBox_14)
                self.core.startedInGui = True
                if os.path.isfile(self.core.pidfile):
                    f = open(self.core.pidfile, "rb")
                    pid = f.read().strip()
                    f.close()
                    return self.errorInternalCoreStartup(self.messageBox_15, pid)
                try:
                    thread.start_new_thread(self.core.start, (False, False))
                except:
                    return self.errorInternalCoreStartup(self.messageBox_16)
                # wait max 15sec for startup
                for t in range(0, 150):
                    if self.core.running:
                        break
                    sleep(0.1)
                if not self.core.running:
                    return self.errorInternalCoreStartup(self.messageBox_17)

                self.connector.proxy = self.core.api
                self.connector.internal = True

            self.mainWindow.mactions["quitcore"].setEnabled(False)
            self.mainWindow.mactions["restartcore"].setEnabled(False)
            self.mainWindow.mactions["cnlfwding"].setEnabled(False)
            self.mainWindow.setWindowTitle(_("pyLoad Client") + " - " + data["name"] + " [via API]")
        
        self.startMain()

    def errorInternalCoreStartup(self, mb, arg=None):
        if arg is None:
            mb()
        else:
            mb(arg)
        self.init()
        return

    def messageBox_14(self):
        text = _("Internal server init failed!")
        self.msgBoxOk(text, "C")

    def messageBox_15(self, pid):
        text = _("pyLoad server already running with pid %d!") % int(pid)
        self.msgBoxOk(text, "C")

    def messageBox_16(self):
        text = _("Failed to start internal server thread!")
        self.msgBoxOk(text, "C")

    def messageBox_17(self):
        text = _("Failed to start internal server!")
        self.msgBoxOk(text, "C")

    def refreshConnections(self, name=None):
        """
            reload connections and display them
            also returns the 'Local(default)' or the name(d) connection
        """
        self.parser.loadData()
        conns = self.loadAllConnections()
        self.connWindow.emit(SIGNAL("setConnections"), conns)
        if name:
            for conn in conns:
                if conn["name"] == name:
                    return conn
        else:
            for conn in conns:
                if conn["default"]:
                    return conn
        return None

    def slotSetDownloadStatus(self, status):
        """
            toolbar start/pause slot
        """
        if not self.corePermissions["STATUS"]:
            return
        if status:
            self.connector.proxy.unpauseServer()
        else:
            self.connector.proxy.pauseServer()

    def slotAddPackage(self, name, links, queue, password=None):
        """
            emitted from main window
            add package
        """
        if not self.corePermissions["ADD"]:
            return
        if queue:
            pack = self.connector.proxy.addPackage(name, links, Destination.Queue)
        else:
            pack = self.connector.proxy.addPackage(name, links, Destination.Collector)
        if self.corePermissions["MODIFY"] and password:
            data = {"password": password}
            self.connector.proxy.setPackageData(pack, data)

    def slotAddLinksToPackage(self, links, queue):
        """
            emitted from main window
            add links to currently selected package
        """
        if not self.corePermissions["ADD"]:
            return
        if queue:
            selection = self.queue.getSelection(False, False)
            txt = _("Queue")
        else:
            selection = self.collector.getSelection(False, False)
            txt = _("Collector")
        packs = []
        for s in selection:
            (pid, fid, isPack) = s
            if isPack:
                packs.append(pid)
        if len(packs) == 1:
            self.connector.proxy.addFiles(packs[0], links)
            self.mainWindow.newLinkDock.widget.box.clear()
        elif len(packs) == 0:
            self.mainWindow.newLinkDock.widget.slotMsgShow("<b>" + (_("Error, no package selected in %s.") % txt) + "</b>")
        else:
            self.mainWindow.newLinkDock.widget.slotMsgShow("<b>" + (_("Error, multiple packages selected in %s.") % txt) + "</b>")

    def slotAddContainer(self, path):
        """
            emitted from main window
            add container
        """
        if not self.corePermissions["ADD"]:
            return
        filename = basename(path)
        #type = "".join(filename.split(".")[-1])
        fh = open(path, "r")
        content = fh.read()
        fh.close()
        self.connector.proxy.uploadContainer(filename, content)

    def prepareForSaveOptionsAndWindow(self, contFunc):
        """
            restore main window and dock windows, unmaximize main window if desired
            before saving their state to the config file and disconnecting from server
        """
        if self.mainWindow.trayOptions.settings["EnableTray"] and self.trayState["hiddenInTray"]:
            self.log.debug4("main.prepareForSaveOptionsAndWindow: showFromTray()")
            self.geoMaximizeConfig = self.trayState["maximized"]
            self.showFromTray(True)
            QTimer.singleShot(0, contFunc)
        elif self.mainWindow.otherOptions.settings["Unmaximize"] and self.mainWindow.isMaximized():
            self.log.debug4("main.prepareForSaveOptionsAndWindow: unmaximizeWait()")
            self.geoMaximizeConfig = True
            self.unmaximizeWait(contFunc)
        else:
            self.log.debug4("main.prepareForSaveOptionsAndWindow: contFunc()")
            self.geoMaximizeConfig = self.mainWindow.isMaximized()
            QTimer.singleShot(0, contFunc)

    def saveOptionsAndWindowToConfig(self):
        """
            save options, window geometry and state to the config file
        """
        if self.mainWindow.isHidden():
            self.log.error("main.saveOptionsAndWindowToConfig: mainWindow is hidden")

        state_raw = self.mainWindow.saveState(self.mainWindow.version)
        geo_raw = self.mainWindow.saveGeometry()

        # hide everything, we are about to quit or to go back to connection manager
        self.mainWindow.captchaDialog.hide()
        self.mainWindow.newPackDock.setFloating(False)
        self.mainWindow.newLinkDock.setFloating(False)
        self.mainWindow.hide()

        mainWindowNode = self.parser.xml.elementsByTagName("mainWindow").item(0)
        if mainWindowNode.isNull():
            mainWindowNode = self.parser.xml.createElement("mainWindow")
            self.parser.root.appendChild(mainWindowNode)
        state = str(state_raw.toBase64())
        geo = str(geo_raw.toBase64())
        geoMaximize = str(self.geoMaximizeConfig)
        stateQueue = str(self.mainWindow.tabs["queue"]["view"].header().saveState().toBase64())
        stateCollector = str(self.mainWindow.tabs["collector"]["view"].header().saveState().toBase64())
        stateAccounts = str(self.mainWindow.tabs["accounts"]["view"].header().saveState().toBase64())
        optionsNotifications = str(QByteArray(str(self.mainWindow.notificationOptions.settings)).toBase64())
        optionsLogging = str(QByteArray(str(self.loggingOptions.settings)).toBase64())
        optionsClickNLoadForwarder = str(self.clickNLoadForwarderOptions.settings["fromPort"])
        optionsAutomaticReloading = str(QByteArray(str(self.automaticReloadingOptions.settings)).toBase64())
        geoCaptcha = str(self.mainWindow.captchaDialog.geo.toBase64())
        optionsCaptcha = str(QByteArray(str(self.captchaOptions.settings)).toBase64())
        optionsFonts = str(QByteArray(str(self.fontOptions.settings)).toBase64())
        optionsTray = str(QByteArray(str(self.mainWindow.trayOptions.settings)).toBase64())
        optionsOther = str(QByteArray(str(self.mainWindow.otherOptions.settings)).toBase64())
        visibilitySpeedLimit = str(QByteArray(str(self.mainWindow.actions["speedlimit_enabled"].isVisible())).toBase64())
        language = str(self.lang)
        stateNode = mainWindowNode.toElement().elementsByTagName("state").item(0)
        geoNode = mainWindowNode.toElement().elementsByTagName("geometry").item(0)
        geoMaximizeNode = mainWindowNode.toElement().elementsByTagName("geometryMaximize").item(0)
        stateQueueNode = mainWindowNode.toElement().elementsByTagName("stateQueue").item(0)
        stateCollectorNode = mainWindowNode.toElement().elementsByTagName("stateCollector").item(0)
        stateAccountsNode = mainWindowNode.toElement().elementsByTagName("stateAccounts").item(0)
        optionsNotificationsNode = mainWindowNode.toElement().elementsByTagName("optionsNotifications").item(0)
        optionsLoggingNode = mainWindowNode.toElement().elementsByTagName("optionsLogging").item(0)
        optionsClickNLoadForwarderNode = mainWindowNode.toElement().elementsByTagName("optionsClickNLoadForwarder").item(0)
        optionsAutomaticReloadingNode = mainWindowNode.toElement().elementsByTagName("optionsAutomaticReloading").item(0)
        geoCaptchaNode = mainWindowNode.toElement().elementsByTagName("geometryCaptcha").item(0)
        optionsCaptchaNode = mainWindowNode.toElement().elementsByTagName("optionsCaptcha").item(0)
        optionsFontsNode = mainWindowNode.toElement().elementsByTagName("optionsFonts").item(0)
        optionsTrayNode = mainWindowNode.toElement().elementsByTagName("optionsTray").item(0)
        optionsOtherNode = mainWindowNode.toElement().elementsByTagName("optionsOther").item(0)
        visibilitySpeedLimitNode = mainWindowNode.toElement().elementsByTagName("visibilitySpeedLimit").item(0)
        languageNode = self.parser.xml.elementsByTagName("language").item(0)
        newStateNode = self.parser.xml.createTextNode(state)
        newGeoNode = self.parser.xml.createTextNode(geo)
        newGeoMaximizeNode = self.parser.xml.createTextNode(geoMaximize)
        newStateQueueNode = self.parser.xml.createTextNode(stateQueue)
        newStateCollectorNode = self.parser.xml.createTextNode(stateCollector)
        newStateAccountsNode = self.parser.xml.createTextNode(stateAccounts)
        newOptionsNotificationsNode = self.parser.xml.createTextNode(optionsNotifications)
        newOptionsLoggingNode = self.parser.xml.createTextNode(optionsLogging)
        newOptionsClickNLoadForwarderNode = self.parser.xml.createTextNode(optionsClickNLoadForwarder)
        newOptionsAutomaticReloadingNode = self.parser.xml.createTextNode(optionsAutomaticReloading)
        newGeoCaptchaNode = self.parser.xml.createTextNode(geoCaptcha)
        newOptionsCaptchaNode = self.parser.xml.createTextNode(optionsCaptcha)
        newOptionsFontsNode = self.parser.xml.createTextNode(optionsFonts)
        newOptionsTrayNode = self.parser.xml.createTextNode(optionsTray)
        newOptionsOtherNode = self.parser.xml.createTextNode(optionsOther)
        newVisibilitySpeedLimitNode = self.parser.xml.createTextNode(visibilitySpeedLimit)
        newLanguageNode = self.parser.xml.createTextNode(language)
        stateNode.removeChild(stateNode.firstChild())
        stateNode.appendChild(newStateNode)
        geoNode.removeChild(geoNode.firstChild())
        geoNode.appendChild(newGeoNode)
        geoMaximizeNode.removeChild(geoMaximizeNode.firstChild())
        geoMaximizeNode.appendChild(newGeoMaximizeNode)
        stateQueueNode.removeChild(stateQueueNode.firstChild())
        stateQueueNode.appendChild(newStateQueueNode)
        stateCollectorNode.removeChild(stateCollectorNode.firstChild())
        stateCollectorNode.appendChild(newStateCollectorNode)
        stateAccountsNode.removeChild(stateAccountsNode.firstChild())
        stateAccountsNode.appendChild(newStateAccountsNode)
        optionsNotificationsNode.removeChild(optionsNotificationsNode.firstChild())
        optionsNotificationsNode.appendChild(newOptionsNotificationsNode)
        optionsLoggingNode.removeChild(optionsLoggingNode.firstChild())
        optionsLoggingNode.appendChild(newOptionsLoggingNode)
        optionsClickNLoadForwarderNode.removeChild(optionsClickNLoadForwarderNode.firstChild())
        optionsClickNLoadForwarderNode.appendChild(newOptionsClickNLoadForwarderNode)
        optionsAutomaticReloadingNode.removeChild(optionsAutomaticReloadingNode.firstChild())
        optionsAutomaticReloadingNode.appendChild(newOptionsAutomaticReloadingNode)
        geoCaptchaNode.removeChild(geoCaptchaNode.firstChild())
        geoCaptchaNode.appendChild(newGeoCaptchaNode)
        optionsCaptchaNode.removeChild(optionsCaptchaNode.firstChild())
        optionsCaptchaNode.appendChild(newOptionsCaptchaNode)
        optionsFontsNode.removeChild(optionsFontsNode.firstChild())
        optionsFontsNode.appendChild(newOptionsFontsNode)
        optionsTrayNode.removeChild(optionsTrayNode.firstChild())
        optionsTrayNode.appendChild(newOptionsTrayNode)
        optionsOtherNode.removeChild(optionsOtherNode.firstChild())
        optionsOtherNode.appendChild(newOptionsOtherNode)
        visibilitySpeedLimitNode.removeChild(visibilitySpeedLimitNode.firstChild())
        visibilitySpeedLimitNode.appendChild(newVisibilitySpeedLimitNode)
        languageNode.removeChild(languageNode.firstChild())
        languageNode.appendChild(newLanguageNode)
        self.parser.saveData()
        self.log.debug4("main.saveOptionsAndWindowToConfig: done")

    def loadOptionsFromConfig(self):
        """
            load options from the config file
        """
        mainWindowNode = self.parser.xml.elementsByTagName("mainWindow").item(0)
        if mainWindowNode.isNull():
            return
        nodes = self.parser.parseNode(mainWindowNode, "dict")
        if not nodes.get("optionsNotifications"):
            mainWindowNode.appendChild(self.parser.xml.createElement("optionsNotifications"))
        if not nodes.get("optionsLogging"):
            mainWindowNode.appendChild(self.parser.xml.createElement("optionsLogging"))
        if not nodes.get("optionsClickNLoadForwarder"):
            mainWindowNode.appendChild(self.parser.xml.createElement("optionsClickNLoadForwarder"))
        if not nodes.get("optionsAutomaticReloading"):
            mainWindowNode.appendChild(self.parser.xml.createElement("optionsAutomaticReloading"))
        if not nodes.get("optionsCaptcha"):
            mainWindowNode.appendChild(self.parser.xml.createElement("optionsCaptcha"))
        if not nodes.get("optionsFonts"):
            mainWindowNode.appendChild(self.parser.xml.createElement("optionsFonts"))
        if not nodes.get("optionsTray"):
            mainWindowNode.appendChild(self.parser.xml.createElement("optionsTray"))
        if not nodes.get("optionsOther"):
            mainWindowNode.appendChild(self.parser.xml.createElement("optionsOther"))
        if not nodes.get("visibilitySpeedLimit"):
            mainWindowNode.appendChild(self.parser.xml.createElement("visibilitySpeedLimit"))
        nodes = self.parser.parseNode(mainWindowNode, "dict")   # reparse with the new nodes (if any)

        optionsNotifications = str(nodes["optionsNotifications"].text())
        optionsLogging = str(nodes["optionsLogging"].text())
        optionsClickNLoadForwarder = str(nodes["optionsClickNLoadForwarder"].text())
        optionsAutomaticReloading = str(nodes["optionsAutomaticReloading"].text())
        optionsCaptcha = str(nodes["optionsCaptcha"].text())
        optionsFonts = str(nodes["optionsFonts"].text())
        optionsTray = str(nodes["optionsTray"].text())
        optionsOther = str(nodes["optionsOther"].text())
        visibilitySpeedLimit = str(nodes["visibilitySpeedLimit"].text())
        if optionsNotifications:
            self.mainWindow.notificationOptions.settings = eval(str(QByteArray.fromBase64(optionsNotifications)))
            self.mainWindow.notificationOptions.dict2checkBoxStates()
        if optionsLogging:
            self.loggingOptions.settings = eval(str(QByteArray.fromBase64(optionsLogging)))
            self.loggingOptions.dict2dialogState()
        if optionsClickNLoadForwarder:
            self.clickNLoadForwarderOptions.settings["fromPort"] = int(optionsClickNLoadForwarder)
            self.clickNLoadForwarderOptions.dict2dialogState(True)
        if optionsAutomaticReloading:
            self.automaticReloadingOptions.settings = eval(str(QByteArray.fromBase64(optionsAutomaticReloading)))
            self.automaticReloadingOptions.dict2dialogState()
        if optionsCaptcha:
            self.captchaOptions.settings = eval(str(QByteArray.fromBase64(optionsCaptcha)))
            self.captchaOptions.dict2dialogState()
            self.mainWindow.captchaDialog.adjSize = self.captchaOptions.settings["AdjSize"]
        if optionsFonts:
            self.fontOptions.settings = eval(str(QByteArray.fromBase64(optionsFonts)))
            self.fontOptions.dict2dialogState()
            self.fontOptions.applySettings()
        if optionsTray:
            self.mainWindow.trayOptions.settings = eval(str(QByteArray.fromBase64(optionsTray)))
            self.mainWindow.trayOptions.dict2checkBoxStates()
        if optionsOther:
            self.mainWindow.otherOptions.settings = eval(str(QByteArray.fromBase64(optionsOther)))
            self.mainWindow.otherOptions.dict2checkBoxStates()
        if visibilitySpeedLimit:
            visible =  eval(str(QByteArray.fromBase64(visibilitySpeedLimit)))
            self.mainWindow.mactions["showspeedlimit"].setChecked(not visible)
            self.mainWindow.mactions["showspeedlimit"].setChecked(visible)

    def loadWindowFromConfig(self):
        """
            load window geometry and state from the config file
        """
        mainWindowNode = self.parser.xml.elementsByTagName("mainWindow").item(0)
        if mainWindowNode.isNull():
            return
        nodes = self.parser.parseNode(mainWindowNode, "dict")
        if not nodes.get("geometryMaximize"):
            mainWindowNode.appendChild(self.parser.xml.createElement("geometryMaximize"))
        if not nodes.get("stateQueue"):
            mainWindowNode.appendChild(self.parser.xml.createElement("stateQueue"))
        if not nodes.get("stateCollector"):
            mainWindowNode.appendChild(self.parser.xml.createElement("stateCollector"))
        if not nodes.get("stateAccounts"):
            mainWindowNode.appendChild(self.parser.xml.createElement("stateAccounts"))
        if not nodes.get("geometryCaptcha"):
            mainWindowNode.appendChild(self.parser.xml.createElement("geometryCaptcha"))
        nodes = self.parser.parseNode(mainWindowNode, "dict")   # reparse with the new nodes (if any)

        state = str(nodes["state"].text())
        geo = str(nodes["geometry"].text())
        if True if str(nodes["geometryMaximize"].text()).lower() in ("1", "true", "on", "an", "yes") else False:
            self.geoMaximizeConfig = True
        else:
            self.geoMaximizeConfig = False
        stateQueue = str(nodes["stateQueue"].text())
        stateCollector = str(nodes["stateCollector"].text())
        stateAccounts = str(nodes["stateAccounts"].text())
        geoCaptcha = str(nodes["geometryCaptcha"].text())
        self.mainWindow.restoreState(QByteArray.fromBase64(state), self.mainWindow.version)
        self.mainWindow.restoreGeometry(QByteArray.fromBase64(geo))
        self.mainWindow.tabs["queue"]["view"].header().restoreState(QByteArray.fromBase64(stateQueue))
        self.mainWindow.tabs["collector"]["view"].header().restoreState(QByteArray.fromBase64(stateCollector))
        self.mainWindow.tabs["accounts"]["view"].header().restoreState(QByteArray.fromBase64(stateAccounts))
        self.mainWindow.captchaDialog.geo = QByteArray.fromBase64(geoCaptcha)

    def slotPushPackagesToQueue(self):
        """
            emitted from main window
            push the collector packages to queue
        """
        if not self.corePermissions["MODIFY"]:
            return
        selection = self.collector.getSelection(True, True)
        for s in selection:
            (pid, fid, isPack) = s
            if isPack:
                self.connector.proxy.pushToQueue(pid)

    def slotRestartDownloads(self, queue):
        """
            emitted from main window
            restart downloads
        """
        if not self.corePermissions["MODIFY"]:
            return
        if queue:
            selection = self.queue.getSelection(False, False)
        else:
            selection = self.collector.getSelection(False, False)
        packs = []
        for s in selection:
            (pid, fid, isPack) = s
            if isPack:
                self.connector.proxy.restartPackage(pid)
                packs.append(pid)
        for s in selection:
            (pid, fid, isPack) = s
            if not isPack and not (pid in packs):
                self.connector.proxy.restartFile(fid)

    def slotRemoveDownloads(self, queue):
        """
            emitted from main window
            remove downloads
        """
        if not self.corePermissions["DELETE"]:
            return
        if queue:
            selection = self.queue.getSelection(True, False)
        else:
            selection = self.collector.getSelection(True, False)
        packs = []
        for s in selection:
            (pid, fid, isPack) = s
            if isPack:
                packs.append(pid)
        links = []
        for s in selection:
            (pid, fid, isPack) = s
            if not isPack and not (pid in packs):
                links.append(fid)
        self.connector.proxy.deletePackages(packs)
        self.connector.proxy.deleteFiles(links)

    def slotAbortDownloads(self, queue):
        """
            emitted from main window
            abort downloads
        """
        if not self.corePermissions["MODIFY"]:
            return
        if queue:
            selection = self.queue.getSelection(False, False)
        else:
            selection = self.collector.getSelection(False, False)
        packs = []
        for s in selection:
            (pid, fid, isPack) = s
            if isPack:
                packs.append(pid)
        links = []
        for s in selection:
            (pid, fid, isPack) = s
            if not isPack and not (pid in packs):
                links.append(fid)
        if self.corePermissions["LIST"]:
            for pid in packs:
                data = self.connector.proxy.getFileOrder(pid) #less data to transmit
                if data != None and data:
                    self.connector.proxy.stopDownloads(data.values())
        self.connector.proxy.stopDownloads(links)

    def slotSelectAllPackages(self):
        """
            emitted from main window
            select all packages
        """
        if self.mainWindow.activeMenu == self.mainWindow.queueContext:
            self.queue.selectAllPackages()
        else:
            self.collector.selectAllPackages()

    def slotExpandAll(self):
        """
            emitted from main window
            expand all tree view items
        """
        if self.mainWindow.activeMenu == self.mainWindow.queueContext:
            view = self.mainWindow.tabs["queue"]["view"]
        else:
            view = self.mainWindow.tabs["collector"]["view"]
        view.treeExpandAll()

    def slotCollapseAll(self):
        """
            emitted from main window
            collapse all tree view items
        """
        if self.mainWindow.activeMenu == self.mainWindow.queueContext:
            view = self.mainWindow.tabs["queue"]["view"]
        else:
            view = self.mainWindow.tabs["collector"]["view"]
        view.treeCollapseAll()

    def slotStopAllDownloads(self):
        """
            emitted from main window
            stop all running downloads
        """
        if not self.corePermissions["MODIFY"]:
            return
        if self.corePermissions["STATUS"]:
            self.connector.proxy.pauseServer()
        self.connector.proxy.stopAllDownloads()

    def slotRestartFailed(self):
        """
            emitted from main window
            restart all failed file downloads
        """
        if not self.corePermissions["MODIFY"]:
            return
        self.connector.proxy.restartFailed()
        self.queue.setDirty()
        self.collector.setDirty()

    def slotDeleteFinished(self):
        """
            emitted from main window
            delete all finished files and completly finished packages
        """
        if not self.corePermissions["DELETE"]:
            return
        self.connector.proxy.deleteFinished()
        self.queue.setDirty()
        self.collector.setDirty()

    def slotClipboardChange(self):
        """
            called if clipboard changes
        """
        if self.checkClipboard:
            text = self.clipboard.text()
            pattern = re.compile(r"(http|https|ftp)://[a-z0-9]+([\-\.]{1}[a-z0-9]+)*\.[a-z]{2,5}(([0-9]{1,5})?/.*)?")
            matches = pattern.finditer(text)
            
            # thanks to: jmansour //#139
            links = [str(match.group(0)) for match in matches]
            if len(links) == 0:
                return
                
            filenames = [link.rpartition("/")[2] for link in links]
            
            packagename = commonprefix(filenames)
            if len(packagename) == 0:
                packagename = filenames[0]

            self.slotAddPackage(packagename, links, False)

    def slotSetClipboardStatus(self, status):
        """
            set clipboard checking
        """
        self.checkClipboard = status

    def slotPullOutPackages(self):
        """
            emitted from main window
            pull the packages out of the queue
        """
        if not self.corePermissions["MODIFY"]:
            return
        selection = self.queue.getSelection(True, True)
        for s in selection:
            (pid, fid, isPack) = s
            if isPack:
                self.connector.proxy.pullFromQueue(pid)

    def checkCaptcha(self):
        if not (self.corePermissions["STATUS"] and self.captchaOptions.settings["Enabled"]):
            return
        if self.connector.proxy.isCaptchaWaiting() and self.mainWindow.captchaDialog.isFree():
            t = self.connector.proxy.getCaptchaTask(False)
            self.mainWindow.captchaDialog.emit(SIGNAL("setTask"), t.tid, b64decode(t.data), t.type, t.resultType)
            self.tray.captchaAction.setEnabled(True)
            self.slotNotificationMessage(101, None)
        elif not self.mainWindow.captchaDialog.isFree():
            status = self.connector.proxy.getCaptchaTaskStatus(self.mainWindow.captchaDialog.currentID)
            if not (status == "user" or status == "shared-user"):
                self.mainWindow.captchaDialog.emit(SIGNAL("setFree"))
                self.tray.captchaAction.setEnabled(False)

    def slotCaptchaDone(self, cid, result):
        if not self.corePermissions["STATUS"]:
            return
        self.connector.proxy.setCaptchaResult(cid, str(result))
        self.tray.captchaAction.setEnabled(False)

    def slotEditPackages(self, queue):
        """
            popup the package edit dialog
        """
        if queue:
            selection = self.queue.getSelectedPackagesForEdit()
        else:
            selection = self.collector.getSelectedPackagesForEdit()
        for s in selection:
            (pid, name, folder, password) = s
            self.packageEdit.close()
            self.packageEdit.id = pid
            self.packageEdit.old_name = name
            self.packageEdit.old_folder = folder
            self.packageEdit.old_password = password
            self.packageEdit.name.setText(name)
            self.packageEdit.name.home(True)
            self.packageEdit.name.setFocus()
            self.packageEdit.folder.setText(folder)
            self.packageEdit.folder.home(True)
            self.packageEdit.password.setPlainText(password)
            self.mainWindow.numOfOpenModalDialogs += 1
            retval = self.packageEdit.exec_() 
            self.mainWindow.numOfOpenModalDialogs -= 1
            if retval == self.packageEdit.CANCELALL:
                break

    def slotEditPackageSave(self):
        """
            apply changes made in the package edit dialog (save button hit)
        """
        name = str(self.packageEdit.name.text())
        folder = str(self.packageEdit.folder.text())
        password = str(self.packageEdit.password.toPlainText())
        try: # keep the dialog open if something goes wrong
            if name == self.packageEdit.old_name:
                name = None
            if folder == self.packageEdit.old_folder:
                folder = None
            if password == self.packageEdit.old_password:
                password = None
            self.changePackageData(self.packageEdit.id, name, folder, password)
            self.packageEdit.close()
        except:
            raise

    def changePackageData(self, pid, name, folder, password):
        """
            submit package data changes to the core
        """
        if not self.corePermissions["MODIFY"]:
            return
        data = {}
        if name != None:
            data["name"] = name
        if folder != None:
            data["folder"] = folder
        if password != None:
            data["password"] = password
        if data:
            try:
                self.connector.proxy.setPackageData(pid, data)
            except PackageDoesNotExists:
                self.messageBox_18(pid)

    def messageBox_18(self, pid):
        text  = _("The package to edit does not exist anymore!")
        text += "\n\n" + _("Package") + " " + _("ID") + ": %d" % int(pid)
        self.msgBoxOk(text, "W")

    def pullEvents(self):
        """
            called from main loop
        """
        if not self.corePermissions["STATUS"]:
            return
        events = self.connector.proxy.getEvents(self.connector.connectionID)
        if not events:
            return
        for event in events:
            if self.log.isEnabledFor(logging.DEBUG1):
                self.debug_pullEvents(event)
            if event.eventname == "account":
                pass
            elif event.eventname == "config":
                pass
            elif event.destination == Destination.Queue:
                self.queue.addEvent(event)
            elif event.destination == Destination.Collector:
                self.collector.addEvent(event)
                if event.eventname == "reload":
                    self.queue.addEvent(event)      # workaround for Api.addFiles() sending reload for collector even when the package is in the queue
            else:
                self.log.warning("main.pullEvents: Unhandled event: '%s'" % event.eventname)

    def debug_pullEvents(self, event):
        if not self.corePermissions["LIST"]:
            return
        lf = linkstxt = fidstxt = ""
        if event.id:
            eid = str(event.id)
        else:
            eid = "<none>"
        if event.type == ElementType.File:
            et = "File"
        elif event.type == ElementType.Package:
           data = None
           try:
               data = self.connector.proxy.getPackageData(event.id)   # links, full link infos
           #   data = self.connector.proxy.getPackageInfo(event.id)   # fids only
               et = "Package"
           except PackageDoesNotExists:
               et = "Package(ne)"
           if data != None:
               if data.links != None:
                   lf += "[links]"
                   if 0:
                       for i, link in enumerate(data.links):
                           if i > 0:
                               linkstxt += "\n                              "
                           linkstxt += "                 " + str("{:<9}".format(str("links[" + str(i) + "]"))) + "   fid: " + str("{:<4}".format(str(link.fid))) + "   name: " + str(link.name)
               if data.fids != None:
                   lf += "[fids]"
                   if 0:
                       for i, fid in enumerate(data.fids):
                           if i > 0:
                               fidstxt += "\n                              "
                           fidstxt += "                 " + str("{:<8}".format(str("fids[" + str(i) + "]"))) + "   fid: " + str("{:<4}".format(str(fid)))
        else:
           et = "<unknown>"
        if event.destination == Destination.Collector:
            edest = "Destination.Collector+Queue"   # +Queue as reminder for pullEvents: workaround for Api.addFiles() sending reload for collector even when the package is in the queue
        elif event.destination == Destination.Queue:
            edest = "Destination.Queue"
        else:
           edest = "<unknown>"
        self.log.debug1(str("main.pullEvents: eventname: " + str("'%s'" % str(event.eventname)) + "   event.id: " + str("{:<6}".format(str("%s" % str(eid)))) + "   event.type: " +
                       str("{:<11}".format(str(et))) + "   event.destination: " + str("{:<21}".format(str(edest))) + "   " + str("{:<13}".format(str(lf)))))
        if linkstxt:
            self.log.debug1(str(linkstxt))
        if fidstxt:
            self.log.debug1(str(fidstxt))

    def slotReloadAccounts(self, force=False):
        self.mainWindow.tabs["accounts"]["view"].model.reloadData(force)

    def slotQuit(self):
        self.allowUserActions(False)
        self.prepareForSaveOptionsAndWindow(self.slotQuit_continue)

    def slotQuit_continue(self):
        self.saveOptionsAndWindowToConfig()
        self.quitInternal()
        self.log.info("pyLoad Client quit")
        self.removeLogger()
        self.app.quit()

    def slotQuitConnWindow(self):
        self.log.info("pyLoad Client quit")
        self.removeLogger()
        self.app.quit()

    def quitInternal(self):
        if self.core:
            self.core.api.kill()
            for i in range(10):
                if self.core.shuttedDown:
                    break
                sleep(0.5)

    def slotConnectionLost(self):
        if not self.connectionLost:
            self.connectionLost = True
            try:
                self.quitInternal()
                self.stopMain()
                return
            except:
                pass
            self.log.error("main.slotConnectionLost: Unexpected error while trying to connect to the server.")
            self.log.error("                         If this happens again and this is your default connection,")
            self.log.error("                         use command line argument '-c' with a nonexistent connection-name")
            self.log.error("                         to get in the Connection Manager, e.g. 'pyLoadGui.py -c foobar'.")
            self.log.info("pyLoad Client quit")
            self.removeLogger()
            exit()

    class Loop():
        def __init__(self, parent):
            self.log = logging.getLogger("guilog")
            self.parent = parent

            self.timer = QTimer()
            self.timer.connect(self.timer, SIGNAL("timeout()"), self.update)
            self.lastSpaceCheck = 0

        def start(self):
            self.update()
            self.timer.start(1000)

        def update(self):
            """
                methods to call
            """
            self.parent.refreshServerStatus()
            if self.lastSpaceCheck + 5 < time():
                self.lastSpaceCheck = time()
                if self.parent.corePermissions["STATUS"]:
                    self.parent.serverStatus["freespace"] = self.parent.connector.proxy.freeSpace()
            self.parent.refreshGuiLog()
            self.parent.refreshCoreLog()
            self.parent.checkCaptcha()

            # check dirty data model flags at regular intervals
            self.parent.queue.fullReloadOnDirty()
            self.parent.collector.fullReloadOnDirty()

            self.parent.pullEvents()
            if self.parent.automaticReloadingOptions.settings["enabled"]:
                interval = float(self.parent.automaticReloadingOptions.settings["interval"]) - 0.5
                self.parent.queue.automaticReloading(interval)
                self.parent.collector.automaticReloading(interval)
            self.parent.updateToolbarSpeedLimitFromCore()

        def stop(self):
            self.timer.stop()

    def slotShowLoggingOptions(self):
        """
            popup the logging options dialog
        """
        self.loggingOptions.dict2dialogState()
        oldsettings = self.loggingOptions.settings.copy()
        self.mainWindow.numOfOpenModalDialogs += 1
        retval = self.loggingOptions.exec_()
        self.mainWindow.numOfOpenModalDialogs -= 1
        if retval == QDialog.Accepted:
            QMutexLocker(self.guiLogMutex)
            self.loggingOptions.dialogState2dict()
            if self.loggingOptions.settings != oldsettings:
                fl = self.loggingOptions.settings["file_log"]
                if fl != oldsettings["file_log"]:
                    if fl:
                        self.initLogging()
                        self.log.info("File Log enabled")
                    else:
                        self.log.info("File Log disabled")
                        self.initLogging()
                else:
                    self.initLogging()
                self.setupGuiLogTab(fl)

    def slotShowClickNLoadForwarderOptions(self):
        """
            popup the ClickNLoad port forwarder options dialog
        """
        self.clickNLoadForwarderOptions.settings["enabled"] = self.clickNLoadForwarder.running
        self.clickNLoadForwarderOptions.dict2dialogState(self.clickNLoadForwarder.error)
        self.mainWindow.numOfOpenModalDialogs += 1
        retval = self.clickNLoadForwarderOptions.exec_()
        self.mainWindow.numOfOpenModalDialogs -= 1
        if retval == QDialog.Accepted:
            self.clickNLoadForwarderOptions.dialogState2dict()
            settings = self.clickNLoadForwarderOptions.settings
            if self.clickNLoadForwarder.running:
                self.clickNLoadForwarder.stop()
                if self.clickNLoadForwarder.running:
                    return
            if settings["enabled"]:
                if settings["getPort"]:
                    port = self.getClickNLoadPortFromCoreSettings()
                    if port == -1:
                        return
                    settings["toPort"] = port
                self.clickNLoadForwarder.start(settings["fromIP"], settings["fromPort"], settings["toIP"], settings["toPort"])

    def slotShowAutomaticReloadingOptions(self):
        """
            popup the automatic reloading options dialog
        """
        self.automaticReloadingOptions.dict2dialogState()
        self.mainWindow.numOfOpenModalDialogs += 1
        retval = self.automaticReloadingOptions.exec_()
        self.mainWindow.numOfOpenModalDialogs -= 1
        if retval == QDialog.Accepted:
            self.automaticReloadingOptions.dialogState2dict()

    def slotShowCaptchaOptions(self):
        """
            popup the captcha options dialog
        """
        self.captchaOptions.dict2dialogState()
        self.mainWindow.numOfOpenModalDialogs += 1
        retval = self.captchaOptions.exec_()
        self.mainWindow.numOfOpenModalDialogs -= 1
        if retval == QDialog.Accepted:
            self.captchaOptions.dialogState2dict()
            if not self.captchaOptions.settings["Enabled"]:
                self.mainWindow.captchaDialog.emit(SIGNAL("setFree"))
                self.tray.captchaAction.setEnabled(False)
            self.mainWindow.captchaDialog.adjSize = self.captchaOptions.settings["AdjSize"]

    def slotShowFontOptions(self):
        """
            popup the font options dialog
        """
        self.fontOptions.dict2dialogState()
        oldsettings = copy.deepcopy(self.fontOptions.settings)
        self.mainWindow.numOfOpenModalDialogs += 1
        retval = self.fontOptions.exec_()
        self.mainWindow.numOfOpenModalDialogs -= 1
        if retval == QDialog.Accepted:
            self.fontOptions.dialogState2dict()
            if self.fontOptions.settings != oldsettings:
                self.fontOptions.applySettings()
        else:
            self.fontOptions.settings = copy.deepcopy(oldsettings)

    def slotShowLanguageOptions(self):
        """
            popup the language options dialog
        """
        def getLanguageList():
            localedir = self.path + sep + "locale"
            if not (os.path.isdir(localedir) and os.access(localedir, os.R_OK)):
                self.log.error("main.slotShowLanguageOptions.getLanguageList: Cannot access directory: %s" % localedir)
                return []
            dirs = [d for d in os.listdir(localedir) if os.path.isdir(join(localedir, d))]
            self.log.debug9("main.slotShowLanguageOptions.getLanguageList: dirs: %s" % str(dirs))
            domain = "pyLoadGui"
            files = gettext.find(domain, localedir, dirs, True)
            self.log.debug9("main.slotShowLanguageOptions.getLanguageList: files: %s" % str(files))
            languages = []
            for f in files:
                suffix = sep + "LC_MESSAGES" + sep + domain + ".mo"
                if f.endswith(suffix):
                    lang = f[:-(len(suffix))].split(sep)[-1]
                    if lang and (os.path.getsize(f) > 100):
                        languages.append(lang)
            languages = sorted(languages, key=lambda l: l)
            self.log.debug9("main.slotShowLanguageOptions.getLanguageList: languages: %s" % str(languages))
            if len(languages) == 0:
                self.log.error("main.slotShowLanguageOptions.getLanguageList: No language files found in directory: %s" % localedir)
            return languages

        self.languageOptions.settings["languageList"] = getLanguageList()
        self.languageOptions.settings["language"] = self.lang
        self.languageOptions.dict2dialogState()
        self.mainWindow.numOfOpenModalDialogs += 1
        retval = self.languageOptions.exec_()
        self.mainWindow.numOfOpenModalDialogs -= 1
        if retval == QDialog.Accepted:
            self.languageOptions.dialogState2dict()
            if self.languageOptions.settings["language"] != self.lang:
                self.lang = self.languageOptions.settings["language"]

    def updateToolbarSpeedLimitFromCore(self):
        """
            called from main loop
        """
        if not self.corePermissions["SETTINGS"]:
            return
        if not self.mainWindow.actions["speedlimit_enabled"].isVisible():
            #self.log.debug0("updateToolbarSpeedLimitFromCore: skipped - hidden")
            return
        if self.inSlotToolbarSpeedLimitEdited:
            self.log.debug0("updateToolbarSpeedLimitFromCore: skipped - in function edited")
            return
        if self.mainWindow.toolbar_speedLimit_enabled.hasFocus():
            self.log.debug0("updateToolbarSpeedLimitFromCore: skipped - checkbox has focus")
            return
        if self.mainWindow.toolbar_speedLimit_rate.hasFocus():
            self.log.debug0("updateToolbarSpeedLimitFromCore: skipped - spinbox has focus")
            return
        #self.log.debug0("updateToolbarSpeedLimitFromCore: receiving values from server")
        try:
            enab_str = self.connector.proxy.getConfigValue("download", "limit_speed", "core")
            rate_str = self.connector.proxy.getConfigValue("download", "max_speed",   "core")
        except:
            self.mainWindow.actions["speedlimit_enabled"].setEnabled(False)
            self.mainWindow.actions["speedlimit_rate"].setEnabled(False)
            self.log.error("main.updateToolbarSpeedLimitFromCore: Failed to get the Speed Limit settings from the server.")
            return
        enab = rate = None
        if enab_str:
            enab = enab_str.lower() in ("1", "true", "on", "an", "yes")
        if rate_str:
            rate = int(rate_str)
        if enab != None and rate != None:
            self.disconnect(self.mainWindow, SIGNAL("toolbarSpeedLimitEdited"), self.slotToolbarSpeedLimitEdited)
            self.mainWindow.toolbar_speedLimit_enabled.setChecked(enab)
            self.mainWindow.toolbar_speedLimit_rate.setValue(rate)
            self.mainWindow.actions["speedlimit_enabled"].setEnabled(True)
            self.mainWindow.actions["speedlimit_rate"].setEnabled(True)
            self.connect(self.mainWindow, SIGNAL("toolbarSpeedLimitEdited"), self.slotToolbarSpeedLimitEdited)

    def slotToolbarSpeedLimitEdited(self):
        """
            the speed limit in the toolbar has been altered
        """
        if not self.corePermissions["SETTINGS"]:
            return
        if self.inSlotToolbarSpeedLimitEdited:
            self.log.debug1("slotToolbarSpeedLimitEdited: ignored, already called")
            return
        self.inSlotToolbarSpeedLimitEdited = True
        err = False
        try:
            enab_str = self.connector.proxy.getConfigValue("download", "limit_speed", "core")
            rate_str = self.connector.proxy.getConfigValue("download", "max_speed",   "core")
        except:
            self.log.error("main.slotToolbarSpeedLimitEdited: Failed to get the Speed Limit settings from the server.")
            err = True
        if not err:
            new_enab_str = str(self.mainWindow.toolbar_speedLimit_enabled.isChecked())
            new_rate_str = str(self.mainWindow.toolbar_speedLimit_rate.value())
            if enab_str != new_enab_str or rate_str != new_rate_str:
                self.mainWindow.actions["speedlimit_enabled"].setEnabled(False)
                self.mainWindow.actions["speedlimit_rate"].setEnabled(False)
                self.log.debug1("slotToolbarSpeedLimitEdited: sending values to server")
                try:
                    if enab_str != new_enab_str:
                        self.connector.proxy.setConfigValue("download", "limit_speed", new_enab_str, "core")
                    if rate_str != new_rate_str:
                        self.connector.proxy.setConfigValue("download", "max_speed", new_rate_str, "core")
                except:
                    self.log.error("main.slotToolbarSpeedLimitEdited: Failed to apply the Speed Limit settings to the server.")
                    err = True
        if not err:
            if enab_str != new_enab_str or rate_str != new_rate_str:
                self.log.debug1("slotToolbarSpeedLimitEdited: setting the values in the server settings tab accordingly")
                self.mainWindow.tabs["settings"]["w"].setSpeedLimitFromToolbar(new_enab_str, new_rate_str)
        self.inSlotToolbarSpeedLimitEdited = False

class AboutBox(QDialog):
    """
        about-box
    """

    def __init__(self, parent):
        QDialog.__init__(self, parent)
        self.log = logging.getLogger("guilog")

        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setWindowTitle(_("About pyLoad Client"))
        self.setWindowIcon(QIcon(join(pypath, "icons", "logo.png")))

        self.logo = QLabel()
        self.logo.setAlignment(Qt.AlignTop)
        pix = QPixmap(join(pypath, "icons", "logo-gui.png"))
        self.logo.setPixmap(pix)
        self.text1 = QLabel()
        self.text1.setAlignment(Qt.AlignTop)
        text1font = QFont(self.text1.font())
        text1fontSize = text1font.pointSize()
        if text1fontSize != -1:
            text1font.setPointSize(text1fontSize + 2)
        text1font.setBold(True)
        self.text1.setFont(text1font)
        self.text2 = QLabel()
        self.text2.setAlignment(Qt.AlignTop)
        self.text3 = QLabel()
        self.text3.setAlignment(Qt.AlignTop)
        self.text3.setTextFormat(Qt.PlainText)

        vboxText = QVBoxLayout()
        vboxText.setContentsMargins(0, 0, 0, 0)
        vboxText.setSpacing(0)
        vboxText.addWidget(self.text1)
        vboxText.addWidget(self.text2)
        vboxText.addSpacing(20)
        vboxText.addWidget(self.text3)
        vboxText.addStretch(1)

        hbox = QHBoxLayout()
        hbox.addWidget(self.logo)
        hbox.addSpacing(20)
        hbox.addLayout(vboxText)
        hbox.addSpacing(20)
        hbox.addStretch(1)

        self.buttons = QDialogButtonBox(Qt.Horizontal, self)
        self.okBtn = self.buttons.addButton(QDialogButtonBox.Ok)
        self.buttons.button(QDialogButtonBox.Ok).setText(_("OK"))
        self.copyBtn = QPushButton(_("Copy to Clipboard"))
        self.buttons.addButton(self.copyBtn, QDialogButtonBox.ActionRole)

        vbox = QVBoxLayout()
        vbox.addLayout(hbox)
        vbox.addSpacing(5)
        vbox.addStretch(1)
        vbox.addWidget(self.buttons)
        self.setLayout(vbox)

        self.connect(self.okBtn, SIGNAL("clicked()"), self.accept)
        self.connect(self.copyBtn, SIGNAL("clicked()"), self.copyToClipboard)

    def copyToClipboard(self):
        txt = self.text3.text()
        clipboard = QApplication.clipboard()
        clipboard.setText(txt)

    def exec_(self, version, internalversion):
        txt1 = _("pyLoad Client") + " v" + version
        self.text1.setText(txt1)
        txt2 = "2008-2016 the pyLoad Team"
        self.text2.setText(txt2)
        txt3  = "Version: " + version
        txt3 += "\nInternal version: " + internalversion
        import platform
        from PyQt4.QtCore import QT_VERSION_STR
        txt3 += "\n\nPlatform: " + platform.platform()
        txt3 += "\nQt version: " + QT_VERSION_STR
        txt3 += "\nPython version: " + platform.python_version()
        try:
            from PyQt4.pyqtconfig import Configuration
            cfg = Configuration()
            sipver = cfg.sip_version_str
            pyqtver = cfg.pyqt_version_str
        except:
            from PyQt4.Qt import PYQT_VERSION_STR
            from sip import SIP_VERSION_STR
            sipver = SIP_VERSION_STR
            pyqtver = PYQT_VERSION_STR
        txt3 += "\nPyQt version: " + pyqtver
        txt3 += "\nSIP version: " + sipver
        self.text3.setText(txt3)
        self.okBtn.setFocus(Qt.OtherFocusReason)
        self.adjustSize()
        self.setFixedSize(self.width(), self.height())
        return QDialog.exec_(self)

class InfoCorePermissions(QDialog):
    """
        permissions info box
    """
    def __init__(self, parent, perms, activeperms):
        QDialog.__init__(self, parent)
        self.log = logging.getLogger("guilog")
        self.perms = perms
        self.activeperms = activeperms

        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self.setWindowFlags(self.windowFlags() | Qt.WindowContextHelpButtonHint)
        self.setWindowTitle(_("Information"))
        self.setWindowIcon(QIcon(join(pypath, "icons", "logo.png")))

        wt_width = 500  # QWhatsThis box width
        tabP = "&nbsp;&nbsp;"
        def p(s1, s2):
            return ("<table width='%d'><tr><td><b>" % wt_width + s1 + tabP + "-" + tabP + s2 + "</b></td></tr></table>")
        def d(s):
            return ("<table width='%d'><tr><td>" % wt_width + s + "</td></tr></table>")

        grid = QGridLayout()
        (admin, plist) = self.setup()

        admLbl = QLabel(admin[0])
        admVal = LineView(admin[1])
        admKlbl = QLabel(admin[2])
        admLbl.setWhatsThis(p(admin[0], admin[3]) + d(admin[4]))

        grid.addWidget(admLbl,  1, 0)
        grid.addWidget(admVal,  1, 1)
        #grid.addWidget(admKlbl, 1, 3)
        for i, perm in enumerate(plist):
            lbl = QLabel(plist[i][0])
            val = LineView(plist[i][1])
            klbl = QLabel(plist[i][2])
            lbl.setWhatsThis(p(plist[i][0], plist[i][3]) + d(plist[i][4]))
            lbl. setDisabled(self.perms["admin"])
            val. setDisabled(self.perms["admin"])
            klbl.setDisabled(self.perms["admin"])
            grid.addWidget(lbl,  i + 2, 0)
            grid.addWidget(val,  i + 2, 1)
            grid.addWidget(klbl, i + 2, 3)

        grid.setRowMinimumHeight(0, 2)
        grid.setColumnMinimumWidth(2, 10)
        grid.setColumnStretch(2, 1)

        gp = QGroupBox(_("Server Permissions"))
        gp.setLayout(grid)

        hintLbl = QLabel("<b>" + _("Permissons were changed.<br>") + _("Takes effect on next login.") + "</b>")
        hintLbl.setWordWrap(True)

        self.buttons = QDialogButtonBox(Qt.Horizontal, self)
        self.closeBtn = self.buttons.addButton(QDialogButtonBox.Close)
        self.buttons.button(QDialogButtonBox.Close).setText(_("Close"))

        vbox = QVBoxLayout()
        vbox.addWidget(gp)
        if self.perms != self.activeperms:
            vbox.addWidget(hintLbl)
        vbox.addStretch(1)
        vbox.addWidget(self.buttons)
        self.setLayout(vbox)

        self.adjustSize()
        self.setFixedSize(self.width(), self.height())

        self.connect(self.closeBtn, SIGNAL("clicked()"), self.accept)

    def setup(self):
        plist = []
        for k, perm in self.perms.iteritems():
            if k == "admin":
                name = _("Administrator")
                wt1  = _("Administrator has all permissions")
                wt2  = _("Needed for:<br>"
                         "- Restart pyLoad Server<br>"
                         "- Quit pyLoad Server"
                         )
                p = _("Yes") if perm else _("No")
                admin = (name, p, "(%s)"%k, wt1, wt2)
                continue
            elif k == "ACCOUNTS":
                name = _("Accounts")
                wt1  = _("Access Accounts")
                wt2  = _("Needed for:<br>"
                         "- Managing file hosting service accounts")
            elif k == "ADD":
                name = _("Add")
                wt1  = _("Add packages and links to Collector and Queue")
                wt2  = _("Also needed for:<br>"
                         "- Queue: Add Container<br>"
                         "- Collector: Moving links to another package<br>"
                         "- Toolbar: Check Clipboard")
            elif k == "DELETE":
                name = _("Delete")
                wt1  = _("Remove packages and links from Collector and Queue")
                wt2  = _("Also needed for:<br>"
                         "- Collector: Moving links to another package")
            elif k == "DOWNLOAD":
                name = _("Download")
                wt1  = _("Download from webinterface")
                wt2  = _("Needed for:<br>"
                         "- Downloading files from the server to your local machine")
            elif k == "LIST":
                name = _("List")
                wt1  = _("View Queue and Collector")
                wt2  = _("Needed for:<br>"
                         "- Overview tab<br>"
                         "- Queue tab<br>"
                         "- Collector tab<br>"
                         "- Status bar")
            elif k == "LOGS":
                name = _("Logs")
                wt1  = _("View Server Log")
                wt2  = _("Needed for:<br>"
                         "- Server Log tab")
            elif k == "MODIFY":
                name = _("Modify")
                wt1  = _("Modify some attributes of downloads")
                wt2  = _("Needed for:<br>"
                         "- Toolbar: Abort All and Restart Failed<br>"
                         "- Queue and Collector: Push to Queue, Pull Out, Restart, Edit and Abort<br>"
                         "- Add Package: Password<br>"
                         "- Sorting packages and sorting links within packages")
            elif k == "SETTINGS":
                name = _("Settings")
                wt1  = _("Access settings")
                wt2  = _("Needed for:<br>"
                         "- Server Settings tab<br>"
                         "- Toolbar: Download Speed Limit<br>"
                         "- ClickNLoad Forwarding: Get Remote Port from Server Settings")
            elif k == "STATUS":
                name = _("Status")
                wt1  = _("View and change server status")
                wt2  = _("Needed for:<br>"
                         "- Updating Overview, Queue and Collector<br>"
                         "- Toolbar: Toggle Pause and Abort All for setting pause mode<br>"
                         "- Captcha solving<br>"
                         "- Status bar: Free space in the download folder")
            else:
                name = k
                wt1 = "&#60;unknown&#62;"
                wt2 = ""
            p = _("Yes") if perm else _("No")
            plist.append((name, p, "(%s)"%k, wt1, wt2))
        plist = sorted(plist, key=lambda d: d[0])
        return (admin, plist)

class CaptchaOptions(QDialog):
    """
        captcha options dialog
    """

    def __init__(self, parent):
        QDialog.__init__(self, parent)
        self.log = logging.getLogger("guilog")

        self.settings = {}

        self.setAttribute(Qt.WA_DeleteOnClose, False)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setWindowTitle(_("Options"))
        self.setWindowIcon(QIcon(join(pypath, "icons", "logo.png")))

        self.cbAdjSize = QCheckBox(_("Adjust dialog box size to its content"))

        vboxCb = QVBoxLayout()
        vboxCb.addWidget(self.cbAdjSize)

        self.cbEnableDialog = QGroupBox(_("Enable") + " " + _("Captcha Solving"))
        self.cbEnableDialog.setCheckable(True)
        self.cbEnableDialog.setLayout(vboxCb)

        self.buttons = QDialogButtonBox(Qt.Horizontal, self)
        self.okBtn     = self.buttons.addButton(QDialogButtonBox.Ok)
        self.cancelBtn = self.buttons.addButton(QDialogButtonBox.Cancel)
        self.buttons.button(QDialogButtonBox.Ok).setText(_("OK"))
        self.buttons.button(QDialogButtonBox.Cancel).setText(_("Cancel"))

        vbox = QVBoxLayout()
        vbox.addWidget(self.cbEnableDialog)
        vbox.addWidget(self.buttons)
        self.setLayout(vbox)

        self.adjustSize()
        self.setFixedSize(self.width(), self.height())

        self.connect(self.okBtn,     SIGNAL("clicked()"), self.accept)
        self.connect(self.cancelBtn, SIGNAL("clicked()"), self.reject)

        # default settings
        self.settings["Enabled"] = True
        self.settings["AdjSize"] = True
        self.dict2dialogState()

    def dialogState2dict(self):
        self.settings["Enabled"] = self.cbEnableDialog.isChecked()
        self.settings["AdjSize"] = self.cbAdjSize.isChecked()

    def dict2dialogState(self):
        self.cbEnableDialog.setChecked (self.settings["Enabled"])
        self.cbAdjSize.setChecked      (self.settings["AdjSize"])

class LoggingOptions(QDialog):
    """
        logging options dialog
    """

    def __init__(self):
        QDialog.__init__(self)

        self.settings = {}
        self.lastFont = None

        self.setAttribute(Qt.WA_DeleteOnClose, False)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setWindowTitle(_("Options"))
        self.setWindowIcon(QIcon(join(pypath, "icons", "logo.png")))

        self.cbEnableFileLog = QGroupBox(_("Enable File Log"))
        self.cbEnableFileLog.setCheckable(True)
        self.cbEnableFileLog.setMinimumWidth(250)
        folderLabel = QLabel(_("Folder"))
        self.leFolder = QLineEdit()

        self.cbRotate = QGroupBox(_("Log Rotation"))
        self.cbRotate.setCheckable(True)
        sizeLabel = QLabel(_("Size in kb"))
        self.sbSize = QSpinBox()
        self.sbSize.setMaximum(999999)
        countLabel = QLabel(_("Count"))
        self.sbCount = QSpinBox()
        self.sbCount.setMaximum(999)

        grid2 = QGridLayout()
        grid2.addWidget(sizeLabel, 0, 0)
        grid2.addWidget(self.sbSize, 0, 1)
        grid2.addWidget(countLabel, 1, 0)
        grid2.addWidget(self.sbCount, 1, 1)
        grid2.setColumnStretch(3, 1)
        self.cbRotate.setLayout(grid2)

        self.cbException = QCheckBox(_("Log Exceptions"))

        grid1 = QGridLayout()
        grid1.addWidget(folderLabel,      0, 0, 1, 1)
        grid1.addWidget(self.leFolder,    0, 1, 1, 1)
        grid1.addWidget(self.cbRotate,    1, 0, 1, 2)
        grid1.addWidget(self.cbException, 2, 0, 1, 2)
        self.cbEnableFileLog.setLayout(grid1)

        self.buttons = QDialogButtonBox(Qt.Horizontal)
        self.okBtn     = self.buttons.addButton(QDialogButtonBox.Ok)
        self.cancelBtn = self.buttons.addButton(QDialogButtonBox.Cancel)
        self.buttons.button(QDialogButtonBox.Ok).setText(_("OK"))
        self.buttons.button(QDialogButtonBox.Cancel).setText(_("Cancel"))

        grid = QGridLayout()
        grid.addWidget(self.cbEnableFileLog, 0, 0)
        grid.setRowStretch(1, 1)
        grid.addWidget(self.buttons, 2, 0)
        self.setLayout(grid)

        self.adjustSize()
        #self.setFixedSize(self.width(), self.height())

        self.connect(self.okBtn,     SIGNAL("clicked()"), self.accept)
        self.connect(self.cancelBtn, SIGNAL("clicked()"), self.reject)

        # default settings
        self.cbEnableFileLog.setChecked(True)
        self.leFolder.setText("Logs")
        self.cbRotate.setChecked(True)
        self.sbSize.setValue(100)
        self.sbCount.setValue(5)
        self.cbException.setChecked(True)
        self.dialogState2dict()

    def exec_(self):
        # It does not resize very well when the font size has changed
        if self.font() != self.lastFont:
            self.lastFont = self.font()
            self.adjustSize()
        return QDialog.exec_(self)

    def dialogState2dict(self):
        self.settings["file_log"]   = self.cbEnableFileLog.isChecked()
        self.settings["log_folder"] = str(self.leFolder.text())
        self.settings["log_rotate"] = self.cbRotate.isChecked()
        self.settings["log_size"]   = self.sbSize.value()
        self.settings["log_count"]  = self.sbCount.value()
        self.settings["exception"]  = self.cbException.isChecked()

    def dict2dialogState(self):
        self.cbEnableFileLog.setChecked (self.settings["file_log"])
        self.leFolder.setText           (self.settings["log_folder"])
        self.cbRotate.setChecked        (self.settings["log_rotate"])
        self.sbSize.setValue            (self.settings["log_size"])
        self.sbCount.setValue           (self.settings["log_count"])
        self.cbException.setChecked     (self.settings["exception"])

class FontOptions(QDialog):
    """
        font options dialog
    """

    def __init__(self, defAppFont, mainWindow):
        QDialog.__init__(self, mainWindow)
        self.defaultApplicationFont = QFont(defAppFont)
        self.mainWindow = mainWindow
        self.log = logging.getLogger("guilog")

        # references
        self.applicationFont = QFont(self.defaultApplicationFont)
        self.queueFont       = QFont(self.defaultApplicationFont)
        self.collectorFont   = QFont(self.defaultApplicationFont)
        self.accountsFont    = QFont(self.defaultApplicationFont)
        self.logFont         = QFont(self.defaultApplicationFont)

        self.settings = {"ECF":         {"enabled": False},
                         "Application": {"enabled": False},
                         "Queue":       {"enabled": False},
                         "Collector":   {"enabled": False},
                         "Accounts":    {"enabled": False},
                         "Log":         {"enabled": False}}
        self.settings["Application"]["font"] = str(self.applicationFont.toString())
        self.settings["Queue"]      ["font"] = str(self.queueFont.toString())
        self.settings["Collector"]  ["font"] = str(self.collectorFont.toString())
        self.settings["Accounts"]   ["font"] = str(self.accountsFont.toString())
        self.settings["Log"]        ["font"] = str(self.logFont.toString())

        self.setAttribute(Qt.WA_DeleteOnClose, False)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setWindowTitle(_("Options"))
        self.setWindowIcon(QIcon(join(pypath, "icons", "logo.png")))

        self.cbEnableCustomFonts = QGroupBox(_("Enable Custom Fonts"))
        self.cbEnableCustomFonts.setCheckable(True)
        self.cbApplication = QCheckBox(_("Application") + ":")
        self.cbApplication.setChecked(True)
        self.lblApplication = QLabel("Liberation Sans")
        self.lblApplicationFont = QFont()
        self.btnApplication = QPushButton(_("Choose"))

        gb2 = QGroupBox()
        self.cbQueue = QCheckBox(_("Queue") + ":")
        self.cbQueue.setChecked(True)
        self.lblQueue = QLabel("Liberation Sans")
        self.lblQueueFont = QFont()
        self.btnQueue = QPushButton(_("Choose"))
        self.cbCollector = QCheckBox(_("Collector") + ":")
        self.cbCollector.setChecked(True)
        self.lblCollector = QLabel("Liberation Sans")
        self.lblCollectorFont = QFont()
        self.btnCollector = QPushButton(_("Choose"))
        self.cbAccounts = QCheckBox(_("Accounts") + ":")
        self.cbAccounts.setChecked(True)
        self.lblAccounts = QLabel("Liberation Sans")
        self.lblAccountsFont = QFont()
        self.btnAccounts = QPushButton(_("Choose"))
        self.cbLog = QCheckBox(_("Logs") + ":")
        self.cbLog.setChecked(True)
        self.lblLog = QLabel("Liberation Sans")
        self.lblLogFont = QFont()
        self.btnLog = QPushButton(_("Choose"))

        grid2 = QGridLayout()
        grid2.addWidget(self.cbQueue,      0, 0)
        grid2.addWidget(self.lblQueue,     0, 1)
        grid2.addWidget(self.btnQueue,     0, 2)
        grid2.addWidget(self.cbCollector,  1, 0)
        grid2.addWidget(self.lblCollector, 1, 1)
        grid2.addWidget(self.btnCollector, 1, 2)
        grid2.addWidget(self.cbAccounts,   2, 0)
        grid2.addWidget(self.lblAccounts,  2, 1)
        grid2.addWidget(self.btnAccounts,  2, 2)
        grid2.addWidget(self.cbLog,        3, 0)
        grid2.addWidget(self.lblLog,       3, 1)
        grid2.addWidget(self.btnLog,       3, 2)
        grid2.setColumnStretch(1, 1)
        gb2.setLayout(grid2)

        grid1 = QGridLayout()
        grid1.addWidget(self.cbApplication,  0, 0, 1, 1)
        grid1.addWidget(self.lblApplication, 0, 1, 1, 1)
        grid1.addWidget(self.btnApplication, 0, 2, 1, 1)
        grid1.addWidget(gb2,                 1, 0, 1, 3)
        grid1.setColumnStretch(1, 1)
        self.cbEnableCustomFonts.setLayout(grid1)

        self.buttons = QDialogButtonBox(Qt.Horizontal)
        self.okBtn     = self.buttons.addButton(QDialogButtonBox.Ok)
        self.cancelBtn = self.buttons.addButton(QDialogButtonBox.Cancel)
        self.resetBtn  = self.buttons.addButton(QDialogButtonBox.Reset)
        self.buttons.button(QDialogButtonBox.Ok).setText(_("OK"))
        self.buttons.button(QDialogButtonBox.Cancel).setText(_("Cancel"))
        self.buttons.button(QDialogButtonBox.Reset).setText(_("Reset"))

        vbox = QVBoxLayout()
        vbox.setSizeConstraint(QLayout.SetMinAndMaxSize)
        vbox.addWidget(self.cbEnableCustomFonts)
        vbox.addStretch()
        vbox.addWidget(self.buttons)
        self.setLayout(vbox)

        self.setMinimumWidth(250)
        self.adjustSize()

        self.connect(self.okBtn,     SIGNAL("clicked()"), self.accept)
        self.connect(self.cancelBtn, SIGNAL("clicked()"), self.reject)
        self.connect(self.resetBtn,  SIGNAL("clicked()"), self.slotResetBtn)

        self.connect(self.cbApplication, SIGNAL("toggled(bool)"), self.cbApplicationToggled)
        self.connect(self.cbQueue,       SIGNAL("toggled(bool)"), self.cbQueueToggled)
        self.connect(self.cbCollector,   SIGNAL("toggled(bool)"), self.cbCollectorToggled)
        self.connect(self.cbAccounts,    SIGNAL("toggled(bool)"), self.cbAccountsToggled)
        self.connect(self.cbLog,         SIGNAL("toggled(bool)"), self.cbLogToggled)

        self.connect(self.btnApplication, SIGNAL("clicked()"), self.chooseApplication)
        self.connect(self.btnQueue,       SIGNAL("clicked()"), self.chooseQueue)
        self.connect(self.btnCollector,   SIGNAL("clicked()"), self.chooseCollector)
        self.connect(self.btnAccounts,    SIGNAL("clicked()"), self.chooseAccounts)
        self.connect(self.btnLog,         SIGNAL("clicked()"), self.chooseLog)

        self.dict2dialogState()

    def cbApplicationToggled(self, checked):
        if checked:
            self.lblApplicationFont = QFont()
            self.lblApplicationFont.fromString(self.settings["Application"]["font"])
        else:
            self.lblApplicationFont = QFont(self.defaultApplicationFont)
        self.lblApplication.setFont(self.lblApplicationFont)
        self.lblApplication.setText(self.lblApplicationFont.family())
        self.lblApplication.setEnabled(checked)
        self.btnApplication.setEnabled(checked)
        # update the other labels fonts (if not checked/enabled)
        self.cbQueueToggled(self.cbQueue.isChecked())
        self.cbCollectorToggled(self.cbCollector.isChecked())
        self.cbAccountsToggled(self.cbAccounts.isChecked())
        self.cbLogToggled(self.cbLog.isChecked())

    def cbQueueToggled(self, checked):
        if checked:
            self.lblQueueFont = QFont()
            self.lblQueueFont.fromString(self.settings["Queue"]["font"])
        else:
            self.lblQueueFont = QFont(self.lblApplicationFont)
        self.lblQueue.setFont(self.lblQueueFont)
        self.lblQueue.setText(self.lblQueueFont.family())
        self.lblQueue.setEnabled(checked)
        self.btnQueue.setEnabled(checked)
    def cbCollectorToggled(self, checked):
        if checked:
            self.lblCollectorFont = QFont()
            self.lblCollectorFont.fromString(self.settings["Collector"]["font"])
        else:
            self.lblCollectorFont = QFont(self.lblApplicationFont)
        self.lblCollector.setFont(self.lblCollectorFont)
        self.lblCollector.setText(self.lblCollectorFont.family())
        self.lblCollector.setEnabled(checked)
        self.btnCollector.setEnabled(checked)
    def cbAccountsToggled(self, checked):
        if checked:
            self.lblAccountsFont = QFont()
            self.lblAccountsFont.fromString(self.settings["Accounts"]["font"])
        else:
            self.lblAccountsFont = QFont(self.lblApplicationFont)
        self.lblAccounts.setFont(self.lblAccountsFont)
        self.lblAccounts.setText(self.lblAccountsFont.family())
        self.lblAccounts.setEnabled(checked)
        self.btnAccounts.setEnabled(checked)
    def cbLogToggled(self, checked):
        if checked:
            self.lblLogFont = QFont()
            self.lblLogFont.fromString(self.settings["Log"]["font"])
        else:
            self.lblLogFont = QFont(self.lblApplicationFont)
        self.lblLog.setFont(self.lblLogFont)
        self.lblLog.setText(self.lblLogFont.family())
        self.lblLog.setEnabled(checked)
        self.btnLog.setEnabled(checked)

    def chooseApplication(self):
        (self.lblApplicationFont, ok) = QFontDialog.getFont(self.lblApplicationFont)
        if ok:
            self.settings["Application"]["font"] = str(self.lblApplicationFont.toString())
            self.cbApplicationToggled(self.cbApplication.isChecked())
    def chooseQueue(self):
        (self.lblQueueFont, ok) = QFontDialog.getFont(self.lblQueueFont)
        if ok:
            self.settings["Queue"]["font"] = str(self.lblQueueFont.toString())
            self.cbQueueToggled(self.cbQueue.isChecked())
    def chooseCollector(self):
        (self.lblCollectorFont, ok) = QFontDialog.getFont(self.lblCollectorFont)
        if ok:
            self.settings["Collector"]["font"] = str(self.lblCollectorFont.toString())
            self.cbCollectorToggled(self.cbCollector.isChecked())
    def chooseAccounts(self):
        (self.lblAccountsFont, ok) = QFontDialog.getFont(self.lblAccountsFont)
        if ok:
            self.settings["Accounts"]["font"] = str(self.lblAccountsFont.toString())
            self.cbAccountsToggled(self.cbAccounts.isChecked())
    def chooseLog(self):
        (self.lblLogFont, ok) = QFontDialog.getFont(self.lblLogFont)
        if ok:
            self.settings["Log"]["font"] = str(self.lblLogFont.toString())
            self.cbLogToggled(self.cbLog.isChecked())

    def slotResetBtn(self):
        self.settings["ECF"]["enabled"]         = False
        self.settings["Application"]["enabled"] = False
        self.settings["Queue"]["enabled"]       = False
        self.settings["Collector"]["enabled"]   = False
        self.settings["Accounts"]["enabled"]    = False
        self.settings["Log"]["enabled"]         = False
        self.settings["Application"]["font"] = str(self.defaultApplicationFont.toString())
        self.settings["Queue"]      ["font"] = str(self.defaultApplicationFont.toString())
        self.settings["Collector"]  ["font"] = str(self.defaultApplicationFont.toString())
        self.settings["Accounts"]   ["font"] = str(self.defaultApplicationFont.toString())
        self.settings["Log"]        ["font"] = str(self.defaultApplicationFont.toString())
        self.dict2dialogState()

    def dialogState2dict(self):
        self.settings["ECF"]["enabled"]         = self.cbEnableCustomFonts.isChecked()
        self.settings["Application"]["enabled"] = self.cbApplication.isChecked()
        self.settings["Queue"]["enabled"]       = self.cbQueue.isChecked()
        self.settings["Collector"]["enabled"]   = self.cbCollector.isChecked()
        self.settings["Accounts"]["enabled"]    = self.cbAccounts.isChecked()
        self.settings["Log"]["enabled"]         = self.cbLog.isChecked()

    def dict2dialogState(self):
        self.cbApplication.setChecked(self.settings["Application"]["enabled"])
        self.cbApplicationToggled(self.cbApplication.isChecked())
        self.cbQueue.setChecked(self.settings["Queue"]["enabled"])
        self.cbQueueToggled(self.cbQueue.isChecked())
        self.cbCollector.setChecked(self.settings["Collector"]["enabled"])
        self.cbCollectorToggled(self.cbCollector.isChecked())
        self.cbAccounts.setChecked(self.settings["Accounts"]["enabled"])
        self.cbAccountsToggled(self.cbAccounts.isChecked())
        self.cbLog.setChecked(self.settings["Log"]["enabled"])
        self.cbLogToggled(self.cbLog.isChecked())
        self.cbEnableCustomFonts.setChecked(not self.settings["ECF"]["enabled"]) # needs to be toggled to grey out the subwidgets accordingly
        self.cbEnableCustomFonts.setChecked(self.settings["ECF"]["enabled"])

    def applySettings(self):
        self.applicationFont = QFont(self.defaultApplicationFont)
        self.queueFont     = QFont(self.applicationFont)
        self.collectorFont = QFont(self.applicationFont)
        self.accountsFont  = QFont(self.applicationFont)
        self.logFont       = QFont(self.applicationFont)
        if self.settings["ECF"]["enabled"]:
            if self.settings["Application"]["enabled"]:
                self.applicationFont = QFont()
                self.applicationFont.fromString(self.settings["Application"]["font"])
                self.queueFont     = QFont(self.applicationFont)
                self.collectorFont = QFont(self.applicationFont)
                self.accountsFont  = QFont(self.applicationFont)
                self.logFont       = QFont(self.applicationFont)
            if self.settings["Queue"]["enabled"]:
                self.queueFont = QFont()
                self.queueFont.fromString(self.settings["Queue"]["font"])
            if self.settings["Collector"]["enabled"]:
                self.collectorFont = QFont()
                self.collectorFont.fromString(self.settings["Collector"]["font"])
            if self.settings["Accounts"]["enabled"]:
                self.accountsFont = QFont()
                self.accountsFont.fromString(self.settings["Accounts"]["font"])
            if self.settings["Log"]["enabled"]:
                self.logFont = QFont()
                self.logFont.fromString(self.settings["Log"]["font"])
        QApplication.setFont(self.applicationFont)
        self.mainWindow.tabs["queue"]["view"].setFont(self.queueFont)
        self.mainWindow.tabs["collector"]["view"].setFont(self.collectorFont)
        self.mainWindow.tabs["accounts"]["view"].setFont(self.accountsFont)
        self.mainWindow.tabs["guilog"]["text"].setFont(self.logFont)
        self.mainWindow.tabs["corelog"]["text"].setFont(self.logFont)

class AutomaticReloadingOptions(QDialog):
    """
        automatic reloading options dialog
    """

    def __init__(self, parent):
        QDialog.__init__(self, parent)
        self.log = logging.getLogger("guilog")

        wt = _(
        "This is useful when there are several clients connected to the server, to reflect all changes made by others.<br>"
        "Also, to reflect your own changes when you do not have") + " '" + _("Status") + "' (STATUS) " + _("permission.<br>"
        "However, you can always trigger a Reload from the View menu manually.<br><br>"
        "This should stay disabled, if you have")  + " '" + _("Status") + "' (STATUS) " + _("permission "
        "and you are the only active user on the server."
        )
        self.setWhatsThis(whatsThisFormat(_("Automatic Reloading"), wt))

        self.settings = {}
        self.lastFont = None

        self.setAttribute(Qt.WA_DeleteOnClose, False)
        self.setWindowFlags(self.windowFlags() | Qt.WindowContextHelpButtonHint)
        self.setWindowTitle(_("Options"))
        self.setWindowIcon(QIcon(join(pypath, "icons", "logo.png")))

        lbl1 = QLabel(_("Every"))
        self.sbInterval = QSpinBox()
        self.sbInterval.setMinimum(10)
        self.sbInterval.setMaximum(3600)
        lbl2 = QLabel(_("seconds"))

        hboxCb = QHBoxLayout()
        hboxCb.addWidget(lbl1)
        hboxCb.addWidget(self.sbInterval)
        hboxCb.addWidget(lbl2)
        hboxCb.addStretch(1)

        self.cbEnabled = QGroupBox(_("Automatic Reloading"))
        self.cbEnabled.setCheckable(True)
        self.cbEnabled.setLayout(hboxCb)

        self.buttons = QDialogButtonBox(Qt.Horizontal, self)
        self.okBtn     = self.buttons.addButton(QDialogButtonBox.Ok)
        self.cancelBtn = self.buttons.addButton(QDialogButtonBox.Cancel)
        self.buttons.button(QDialogButtonBox.Ok).setText(_("OK"))
        self.buttons.button(QDialogButtonBox.Cancel).setText(_("Cancel"))

        vbox = QVBoxLayout()
        vbox.addWidget(self.cbEnabled)
        vbox.addStretch(1)
        vbox.addWidget(self.buttons)
        self.setLayout(vbox)

        self.setMinimumWidth(250)
        self.adjustSize()

        self.connect(self.okBtn,     SIGNAL("clicked()"), self.accept)
        self.connect(self.cancelBtn, SIGNAL("clicked()"), self.reject)

        # default settings
        self.settings["enabled"]  = False
        self.settings["interval"] = 300
        self.dict2dialogState()

    def exec_(self):
        # It does not resize very well when the font size has changed
        if self.font() != self.lastFont:
            self.lastFont = self.font()
            self.adjustSize()
        return QDialog.exec_(self)

    def dialogState2dict(self):
        self.settings["enabled"] = self.cbEnabled.isChecked()
        self.settings["interval"] = self.sbInterval.value()

    def dict2dialogState(self):
        self.cbEnabled.setChecked(self.settings["enabled"])
        self.sbInterval.setValue(self.settings["interval"])

class ClickNLoadForwarderOptions(QDialog):
    """
        ClickNLoad port forwarder options dialog
    """

    def __init__(self, parent):
        QDialog.__init__(self, parent)
        self.log = logging.getLogger("guilog")

        self.settings = {}
        self.lastFont = None

        self.setAttribute(Qt.WA_DeleteOnClose, False)
        self.setWindowFlags(self.windowFlags() | Qt.WindowContextHelpButtonHint)
        self.setWindowTitle(_("Options"))
        self.setWindowIcon(QIcon(join(pypath, "icons", "logo.png")))

        self.cbEnable = QCheckBox(_("Enable"))
        lblFrom = QLabel(_("Local Port"))
        self.sbFromPort = QSpinBox()
        self.sbFromPort.setMinimum(1)
        self.sbFromPort.setMaximum(65535)
        lblTo = QLabel(_("Remote Port"))
        self.sbToPort = QSpinBox()
        self.sbToPort.setMinimum(1)
        self.sbToPort.setMaximum(65535)
        self.cbGetPort = QCheckBox(_("Get Remote Port from Server Settings"))
        self.cbGetPort.setWhatsThis(whatsThisFormat(_("Get Remote Port from Server Settings"), _("Needs") + " '" + _("Settings") + "'" + " (SETTINGS) " + _("permission on the server.")))
        lblSta = QLabel(_("Status"))
        self.lblStatus = LineView("Unknown")
        self.lblStatus.setAlignment(Qt.AlignHCenter)
        self.hboxStatus = QHBoxLayout()
        self.hboxStatus.addWidget(lblSta)
        self.hboxStatus.addWidget(self.lblStatus)

        grid = QGridLayout()
        grid.addWidget(self.cbEnable,   0, 0, 1, 2)
        grid.addWidget(lblFrom,         1, 0)
        grid.addWidget(self.sbFromPort, 1, 1)
        grid.addWidget(lblTo,           2, 0)
        grid.addWidget(self.sbToPort,   2, 1)
        grid.addWidget(self.cbGetPort,  3, 0, 1, 3)
        grid.setColumnStretch(2, 1)
        grid.setRowMinimumHeight(4, 20)
        grid.addLayout(self.hboxStatus, 5, 0, 1, 3)
        grid.setRowStretch(6, 1)

        gb = QGroupBox(_("ClickNLoad Port Forwarding"))
        gb.setLayout(grid)

        self.buttons = QDialogButtonBox(Qt.Horizontal, self)
        self.okBtn     = self.buttons.addButton(QDialogButtonBox.Ok)
        self.cancelBtn = self.buttons.addButton(QDialogButtonBox.Cancel)
        self.buttons.button(QDialogButtonBox.Ok).setText(_("OK"))
        self.buttons.button(QDialogButtonBox.Cancel).setText(_("Cancel"))

        vbox = QVBoxLayout()
        vbox.addWidget(gb)
        vbox.addWidget(self.buttons)
        self.setLayout(vbox)

        self.setMinimumWidth(250)
        self.adjustSize()

        self.connect(self.okBtn,     SIGNAL("clicked()"), self.accept)
        self.connect(self.cancelBtn, SIGNAL("clicked()"), self.reject)
        self.connect(self.cbGetPort, SIGNAL("toggled(bool)"), self.sbToPort.setDisabled)

        # default settings
        self.settings["enabled"]  = False
        self.settings["fromIP"]   = "127.0.0.1"
        self.settings["fromPort"] = 9666
        self.settings["toIP"]     = "999.999.999.999"
        self.settings["toPort"]   = 9666
        self.settings["getPort"]  = False
        self.dict2dialogState(True)

    def exec_(self):
        # It does not resize very well when the font size has changed
        if self.font() != self.lastFont:
            self.lastFont = self.font()
            self.adjustSize()
        return QDialog.exec_(self)

    def dialogState2dict(self):
        self.settings["enabled"]  = self.cbEnable.isChecked()
        self.settings["fromPort"] = self.sbFromPort.value()
        self.settings["toPort"]   = self.sbToPort.value()
        self.settings["getPort"]  = self.cbGetPort.isChecked()

    def dict2dialogState(self, error):
        self.cbEnable.setChecked(self.settings["enabled"])
        self.sbFromPort.setValue(self.settings["fromPort"])
        self.sbToPort.setValue(self.settings["toPort"])
        self.cbGetPort.setChecked(self.settings["getPort"])
        if not error:
            if self.settings["enabled"]:
                self.lblStatus.setText(_("Running"))
            else:
                self.lblStatus.setText(_("Not Running"))
        else:
            self.lblStatus.setText(_("ERROR"))

class ClickNLoadForwarder(QObject):
    """
        Port forwarder to a remote Core's ClickNLoad plugin
    """

    def __init__(self):
        QObject.__init__(self)
        self.log = logging.getLogger("guilog")
        self.doStop  = False
        self.running = False
        self.error   = False
        self.connect(self, SIGNAL("messageBox_19"), self.messageBox_19)
        self.connect(self, SIGNAL("messageBox_20"), self.messageBox_20)

    def start(self, localIp, localPort, extIp, extPort):
        if self.running:
            raise RuntimeError("Port forwarder already started")
        self.localIp   = str(localIp)
        self.localPort = int(localPort)
        self.extIp     = str(extIp)
        self.extPort   = int(extPort)
        self.log.info("ClickNLoadForwarder: Starting port forwarding from %s:%d to %s:%d" % (self.localIp, self.localPort, self.extIp, self.extPort))
        self.doStop = False
        self.error  = False
        thread.start_new_thread(self.server, ())

    def stop(self):
        if not self.running:
            return
        self.doStop = True
        self.dock_socket.shutdown(socket.SHUT_RD) # abort blocking call, do this work on any OS?
        # wait max 10sec
        for t in range(0, 100):
            if not self.running:
                break
            sleep(0.1)
        if self.running:
            self.log.error("ClickNLoadForwarder.stop: Failed to stop port forwarding.")
            self.emit(SIGNAL("messageBox_19"))
        else:
            self.log.info("ClickNLoadForwarder: Port forwarder stopped.")

    def server(self):
        self.running = True
        self.forwardError = False
        try:
            self.dock_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.dock_socket.bind((self.localIp, self.localPort))
            self.dock_socket.listen(5)
        except socket.error, x:
            if x.args[0] == errno.EADDRINUSE:
                self.log.error("ClickNLoadForwarder.server: Cannot bind to port %d, someone else is using it." % self.localPort)
            self.onRaise()
            raise
        except:
            self.onRaise()
            raise
        while True:
            if self.doStop:
                self.log.debug9("ClickNLoadForwarder.server: stopped (1)")
                self.exitOnStop()
            if self.forwardError:
                self.exitOnForwardError()
            try:
                self.client_socket = self.dock_socket.accept()[0] # blocking call
            except socket.error:
                if self.doStop:
                    self.log.debug9("ClickNLoadForwarder.server: stopped (2)")
                    self.exitOnStop()
                elif self.forwardError:
                    self.exitOnForwardError()
                else:
                    self.onRaise()
                    raise
            except:
                self.onRaise()
                raise
            try:
                self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.server_socket.connect((self.extIp, self.extPort))
                thread.start_new_thread(self.forward, (self.client_socket, self.server_socket))
                thread.start_new_thread(self.forward, (self.server_socket, self.client_socket))
            except:
                if self.doStop:
                    self.log.debug9("ClickNLoadForwarder.server: stopped (3)")
                    self.exitOnStop()
                elif self.forwardError:
                    self.exitOnForwardError()
                else:
                    self.onRaise()
                    raise

    def forward(self, source, destination):
        string = " "
        while string:
            if self.doStop or self.error or self.forwardError or not self.running:
                self.log.debug9("ClickNLoadForwarder.forward: thread aborted")
                thread.exit()
            try:
                string = source.recv(1024)
                if string:
                    destination.sendall(string)
                else:
                    #source.shutdown(socket.SHUT_RD)
                    destination.shutdown(socket.SHUT_WR)
            except:
                if not self.forwardError:
                    self.forwardError = True
                    self.log.error("ClickNLoadForwarder.forward: Unexpected Error")
                    self.dock_socket.shutdown(socket.SHUT_RD) # abort blocking call

    def exitOnStop(self):
        self.closeSockets()
        self.error = False
        self.running = False
        thread.exit()

    def exitOnForwardError(self):
        self.closeSockets()
        self.error = True
        self.running = False
        self.log.error("ClickNLoadForwarder.exitOnForwardError: Port forwarding stopped.")
        self.emit(SIGNAL("messageBox_20"))
        thread.exit()

    def onRaise(self):
        self.closeSockets()
        self.error = True
        self.running = False
        self.log.error("ClickNLoadForwarder.onRaise: Port forwarding stopped.")
        self.emit(SIGNAL("messageBox_20"))

    def closeSockets(self):
        try:    self.server_socket.shutdown(socket.SHUT_RD)
        except: pass
        try:    self.server_socket.shutdown(socket.SHUT_WR)
        except: pass
        try:    self.server_socket.close()
        except: pass
        try:    self.client_socket.shutdown(socket.SHUT_RD)
        except: pass
        try:    self.client_socket.shutdown(socket.SHUT_WR)
        except: pass
        try:    self.client_socket.close()
        except: pass
        try:    self.dock_socket.shutdown(socket.SHUT_RD)
        except: pass
        try:    self.dock_socket.shutdown(socket.SHUT_WR)
        except: pass
        try:    self.dock_socket.close()
        except: pass

    def messageBox_19(self):
        self.emit(SIGNAL("msgBoxError"), _("Failed to stop ClickNLoad port forwarding."))

    def messageBox_20(self):
        self.emit(SIGNAL("msgBoxError"), _("ClickNLoad port forwarding stopped."))

class LanguageOptions(QDialog):
    """
        language options dialog
    """

    def __init__(self, parent):
        QDialog.__init__(self, parent)
        self.log = logging.getLogger("guilog")

        self.settings = {}
        self.lastFont = None

        self.setAttribute(Qt.WA_DeleteOnClose, False)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setWindowTitle(_("Options"))
        self.setWindowIcon(QIcon(join(pypath, "icons", "logo.png")))

        self.combo = QComboBox()
        self.noteLbl = QLabel()
        note = "<i>" + _("Takes effect on next login.") + "</i>"
        self.noteLbl.setText(note)

        hboxGp = QHBoxLayout()
        hboxGp.addWidget(self.combo)
        hboxGp.addStretch(1)
        vboxGp = QVBoxLayout()
        vboxGp.addLayout(hboxGp)
        vboxGp.addWidget(self.noteLbl)

        self.gb = QGroupBox(_("Language"))
        self.gb.setLayout(vboxGp)

        self.buttons = QDialogButtonBox(Qt.Horizontal, self)
        self.okBtn     = self.buttons.addButton(QDialogButtonBox.Ok)
        self.cancelBtn = self.buttons.addButton(QDialogButtonBox.Cancel)
        self.buttons.button(QDialogButtonBox.Ok).setText(_("OK"))
        self.buttons.button(QDialogButtonBox.Cancel).setText(_("Cancel"))

        vbox = QVBoxLayout()
        vbox.addWidget(self.gb)
        vbox.addWidget(self.buttons)
        self.setLayout(vbox)

        self.setMinimumWidth(250)
        self.adjustSize()

        self.connect(self.okBtn,     SIGNAL("clicked()"), self.accept)
        self.connect(self.cancelBtn, SIGNAL("clicked()"), self.reject)

        # default settings
        self.settings["languageList"] = ["en"]
        self.settings["language"] = "en"
        self.dict2dialogState()

    def exec_(self):
        # It does not resize very well when the font size has changed
        if self.font() != self.lastFont:
            self.lastFont = self.font()
            self.adjustSize()
            self.resize(self.width(), 1)
        return QDialog.exec_(self)

    def dialogState2dict(self):
        self.settings["language"] = self.combo.itemText(self.combo.currentIndex())

    def dict2dialogState(self):
        self.combo.clear()
        self.combo.addItems(self.settings["languageList"])
        self.combo.setCurrentIndex(self.combo.findText(self.settings["language"]))

class TrayIcon(QSystemTrayIcon):
    def __init__(self):
        QSystemTrayIcon.__init__(self, QIcon(join(pypath, "icons", "logo-gui.png")))
        self.log = logging.getLogger("guilog")

        self.contextMenu = QMenu()
        self.showAction = QAction("show/hide", self.contextMenu)
        self.showAction.setIcon(QIcon(join(pypath, "icons", "logo.png")))
        self.setShowActionText(False)
        self.contextMenu.addAction(self.showAction)
        self.captchaAction = QAction(_("Waiting Captcha"), self.contextMenu)
        self.contextMenu.addAction(self.captchaAction)
        self.contextAddMenu = self.contextMenu.addMenu(QIcon(join(pypath, "icons", "add_small.png")), _("Add"))
        self.addPackageAction = self.contextAddMenu.addAction(_("Package"))
        self.addLinksAction = self.contextAddMenu.addAction(_("Links"))
        self.addContainerAction = self.contextAddMenu.addAction(_("Container"))
        self.contextMenu.addSeparator()
        self.exitAction = QAction(QIcon(join(pypath, "icons", "close.png")), _("Exit"), self.contextMenu)
        self.contextMenu.addAction(self.exitAction)
        self.setContextMenu(self.contextMenu)
        if self.log.isEnabledFor(logging.DEBUG9):
            self.contextMenu.addSeparator()
            self.contextDebugMenu = self.contextMenu.addMenu("Debug")
            self.debugTrayAction = self.contextDebugMenu.addAction(_("Tray"))
            self.debugMsgboxAction = self.contextDebugMenu.addAction(_("MessageBox Test"))

        # disable/greyout menu entries
        self.showAction.setEnabled(False)
        self.captchaAction.setEnabled(False)
        self.contextAddMenu.setEnabled(False)

    def setShowActionText(self, show):
        if show:
            self.showAction.setText(_("Show") + " " + _("pyLoad Client"))
        else:
            self.showAction.setText(_("Hide") + " " + _("pyLoad Client"))

    def clicked(self, reason):
        if self.showAction.isEnabled():
            if reason == QSystemTrayIcon.Trigger:
                self.showAction.trigger()

class PackageEdit(QDialog):
    """
        package edit dialog
    """

    def __init__(self, parent):
        self.log = logging.getLogger("guilog")

        self.id = None
        self.old_name = None
        self.old_folder = None
        self.old_password = None

        # custom return codes
        self.SAVE = 100
        self.CANCEL = 101
        self.CANCELALL = 102

        QDialog.__init__(self, parent)
        self.setAttribute(Qt.WA_DeleteOnClose, False)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setWindowTitle(_("Edit Package"))
        self.setWindowIcon(QIcon(join(pypath, "icons", "logo.png")))

        vbox = QVBoxLayout()
        spacing = 15

        lbl = QLabel(_("Name"))
        vbox.addWidget(lbl)
        self.name = QLineEdit()
        vbox.addWidget(self.name)
        vbox.addSpacing(spacing)

        lbl = QLabel(_("Folder"))
        vbox.addWidget(lbl)
        self.folder = QLineEdit()
        vbox.addWidget(self.folder)
        vbox.addSpacing(spacing)

        lbl = QLabel(_("Password"))
        vbox.addWidget(lbl)
        self.password = QPlainTextEdit()
        self.password.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.password.setTabChangesFocus(True)
        vbox.addWidget(self.password)
        vbox.addSpacing(spacing)

        self.buttons = QDialogButtonBox(Qt.Horizontal, self)
        self.saveBtn = self.buttons.addButton(QDialogButtonBox.Save)
        self.saveBtn.setDefault(True)
        self.saveBtn.setAutoDefault(True)
        self.saveBtn.setText(_("Save"))
        self.cancelBtn = self.buttons.addButton(QDialogButtonBox.Cancel)
        self.cancelBtn.setDefault(False)
        self.cancelBtn.setAutoDefault(False)
        self.cancelBtn.setText(_("Cancel"))
        self.cancelAllBtn = self.buttons.addButton(QDialogButtonBox.No)
        self.cancelAllBtn.setDefault(False)
        self.cancelAllBtn.setAutoDefault(False)
        self.cancelAllBtn.setText(_("Cancel All"))
        vbox.addWidget(self.buttons)

        self.setLayout(vbox)
        self.adjustSize()
        self.resize(750, 0)

        self.connect(self.saveBtn,      SIGNAL("clicked()"), self.slotSaveClicked)
        self.connect(self.cancelBtn,    SIGNAL("clicked()"), self.slotCancelClicked)
        self.connect(self.cancelAllBtn, SIGNAL("clicked()"), self.slotCancelAllClicked)

    def slotSaveClicked(self):
        self.done(self.SAVE)

    def slotCancelClicked(self):
        self.done(self.CANCEL)

    def slotCancelAllClicked(self):
        self.done(self.CANCELALL)

class Notification(QObject):
    def __init__(self, tray):
        QObject.__init__(self)
        self.log = logging.getLogger("guilog")
        self.tray = tray

        self.usePynotify = False

        try:
            self.usePynotify = pynotify.init("icon-summary-body")
        except:
            self.log.error("Notification: Pynotify initialization failed")

    def showMessage(self, body):
        if self.usePynotify:
            n = pynotify.Notification("pyLoad", body, join(pypath, "icons", "logo.png"))
            try:
                n.set_hint_string("x-canonical-append", "")
            except:
                pass
            n.show()
        else:
            self.tray.showMessage("pyLoad", body)

if __name__ == "__main__":
    renameProcess('pyLoadGui')
    app = main()
    app.loop()

