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
CURRENT_INTERNAL_VERSION = '2017-11-19'         # YYYY-MM-DD, append a lowercase letter for a new version on the same day

import os
import sys
from sys import argv
from getopt import getopt, GetoptError

if os.name == "nt":
    import ctypes
try:
    havePynotify = True
    import pynotify                 # import before LoggingLevels to avoid gtk warning on some systems
except ImportError:
    havePynotify = False

from module.gui import LoggingLevels
from module.gui.Tools import WtDialogButtonBox, LineView
import logging.handlers
from os import makedirs, sep

from uuid import uuid4 as uuid      # import before PyQt
from time import sleep, time
from module.common.json_layer import json

from PyQt4.QtCore import *
from PyQt4.QtGui import *

import re
import copy
import traceback
import module.common.pylgettext as gettext
import socket
import errno
import thread
from os.path import abspath
from os.path import join
from os.path import basename
from os.path import commonprefix
from os.path import exists
from threading import Timer

from module import InitHomeDir
from module.gui.ConnectionManager import *
from module.gui.connector import Connector
from module.gui.MainWindow import *
from module.gui.Queue import *
from module.gui.Overview import *
from module.gui.Collector import *
from module.gui.XMLParser import *
from module.gui.CoreConfigParser import ConfigParser
from module.gui.Options import *
from module.gui.Tools import MessageBox

from module.lib.rename_process import renameProcess
from module.lib.SafeEval import const_eval as literal_eval
from module.utils import formatSize, formatSpeed

from module.remote.thriftbackend.ThriftClient import DownloadStatus
from module.Api import has_permission, PERMS, ROLE

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
        self.app.setAttribute(Qt.AA_DontShowIconsInMenus, False)
        self.defAppFont = QApplication.font()
        self.path = pypath
        self.homedir = abspath("")

        self.cmdLineConnection = None
        self.configdir = ""
        self.noConsole = False
        self.pidfile = "pyloadgui.pid"
        self.debugLogLevel = None
        if len(argv) > 1:
            try:
                options, dummy = getopt(argv[1:], 'vc:nip:hd:',
                    ["configdir=", "version", "connection=",
                     "noconsole", "icontest", "pidfile=", "help", "debug="])
                for option, argument in options:
                    if option in ("-v", "--version"):
                        print "pyLoad Client", CURRENT_VERSION
                        exit()
                    elif option in ("-c", "--connection"):
                        self.cmdLineConnection = argument
                    elif option in ("--configdir"):
                        self.configdir = argument
                    elif option in ("-n", "--noconsole"):
                        if os.name == "nt":
                            self.noConsole = True
                        else:
                            print "Error: The noconsole option works only on Windows OS"
                            exit()
                    elif option in ("-i", "--icontest"):
                        self.icontest()
                        exit()
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
        self.connManagerDisableConnect = False
        if not self.checkConfigFiles():
            exit()
        if self.noConsole:
            self.hideWindowsCommandPrompt()
        QTextCodec.setCodecForTr(QTextCodec.codecForName("UTF-8"))
        QTextCodec.setCodecForLocale(QTextCodec.codecForName("UTF-8"))
        QTextCodec.setCodecForCStrings(QTextCodec.codecForName("UTF-8"))
        self.init(True)

    @classmethod
    def icontest(self):
        print "Test of the desktop environment icon theme."
        print "  This will crash (Segmentation fault) if an icon fails to load."
        print "  In such case, the active icon theme possibly is broken or incomplete."
        print "  Try choose a different icon theme in your desktop environment and run the test again.\n"
        icons = []
        icons.append(( QMessageBox.Question,    "QMessageBox.Question                       "))
        icons.append(( QMessageBox.Information, "QMessageBox.Information                    "))
        icons.append(( QMessageBox.Warning,     "QMessageBox.Warning                        "))
        icons.append(( QMessageBox.Critical,    "QMessageBox.Critical                       "))
        msgb = QMessageBox()
        for i in icons:
            print i[1],; sys.stdout.flush()
            msgb.setIcon(i[0])
            print "OK"
        icons = []
        icons.append(( QStyle.SP_MessageBoxQuestion,               "QStyle.SP_MessageBoxQuestion               "))
        icons.append(( QStyle.SP_MessageBoxInformation,            "QStyle.SP_MessageBoxInformation            "))
        icons.append(( QStyle.SP_MessageBoxWarning,                "QStyle.SP_MessageBoxWarning                "))
        icons.append(( QStyle.SP_MessageBoxCritical,               "QStyle.SP_MessageBoxCritical               "))
        icons.append(( QStyle.SP_ToolBarHorizontalExtensionButton, "QStyle.SP_ToolBarHorizontalExtensionButton "))
        icons.append(( QStyle.SP_ToolBarVerticalExtensionButton,   "QStyle.SP_ToolBarVerticalExtensionButton   "))
        icons.append(( QStyle.SP_ToolBarHorizontalExtensionButton, "QStyle.SP_ToolBarHorizontalExtensionButton "))
        icons.append(( QStyle.SP_ToolBarVerticalExtensionButton,   "QStyle.SP_ToolBarVerticalExtensionButton   "))
        icons.append(( QStyle.SP_BrowserReload,                    "QStyle.SP_BrowserReload                    "))
        icons.append(( QStyle.SP_DialogSaveButton,                 "QStyle.SP_DialogSaveButton                 "))
        style = QApplication.style()
        for i in icons:
            print i[1],; sys.stdout.flush()
            i = style.standardIcon(i[0])
            print "OK"
        print "\nNo errors."

    @classmethod
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
        print "  -n, --noconsole", " " * 8, "Hide Command Prompt on Windows OS"
        #print "  -p, --pidfile=<file>", " " * 3, "Set pidfile to <file>"
        print "  -i, --icontest", " " * 9, "Check for crash when loading icons"
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
        self.newConfigFile = not guiFileFound
        return True

    @classmethod
    def hideWindowsCommandPrompt(self, hide=True):
        if os.name == "nt":
            hWnd = ctypes.windll.kernel32.GetConsoleWindow()
            if hWnd:
                if hide:
                    nCmdShow = 0 # SW_HIDE
                else:
                    nCmdShow = 4 # SW_SHOWNOACTIVATE
                ctypes.windll.user32.ShowWindow(hWnd, nCmdShow)

    def init(self, first=False):
        """
            set main things up
        """
        self.tray = None
        self.mainWindowPaintEventAction = {}
        self.mainWindowMaximizedSize = None
        self.geoOther = { "packDock": None, "linkDock": None, "packDockTray": None, "linkDockTray": None, "packDockIsFloating": None, "linkDockIsFloating": None, "captchaDialog": None }
        self.guiLogMutex = QMutex()
        self.lastCaptchaId = None

        self.parser = XMLParser(join(self.homedir, "gui.xml"), join(self.path, "module", "config", "gui_default.xml"))
        self.lang = self.parser.xml.elementsByTagName("language").item(0).toElement().text()
        if not self.lang:
            parser = XMLParser(join(self.path, "module", "config", "gui_default.xml"))
            self.lang = parser.xml.elementsByTagName("language").item(0).toElement().text()

        gettext.setpaths([join(os.sep, "usr", "share", "pyload", "locale"), None])
        self.translation = gettext.translation("pyLoadGui", join(pypath, "locale"), languages=[str(self.lang), "en"], fallback=True)
        self.translation.install(unicode=True)

        self.loggingOptions = LoggingOptions()
        optlog = self.parser.xml.elementsByTagName("optionsLogging").item(0).toElement().text()
        if optlog:
            try:
                self.loggingOptions.settings = literal_eval(str(QByteArray.fromBase64(str(optlog))))
                self.loggingOptions.dict2dialogState()
            except Exception:
                self.loggingOptions.defaultSettings()
        self.initLogging(first)

        self.log.info("====================================================================================================")
        if first:
            self.log.info("Starting pyLoad Client %s" % CURRENT_VERSION)
        else:
            self.log.info("Reinitializing pyLoad Client %s" % CURRENT_VERSION)
        self.log.debug9("User's home directory: %s" % InitHomeDir.homedir)
        self.log.info("Configuration directory: %s" % self.homedir)
        #self.log.info("Using pid file: %s" % self.pidfile)
        if self.debugLogLevel != None:
            self.log.info("Debug messages at level %d and higher" % self.debugLogLevel)

        self.initCorePermissions()
        self.connector = Connector(first)
        self.inSlotToolbarSpeedLimitEdited = False
        self.mainWindow = MainWindow(self.corePermissions, self.connector)
        self.notificationOptions = NotificationOptions(self.mainWindow)
        self.otherOptions = OtherOptions(self.mainWindow)
        self.trayOptions = TrayOptions(self.mainWindow)
        self.loggingOptions.setParent(self.mainWindow, self.loggingOptions.windowFlags())
        self.packageEdit = PackageEdit(self.mainWindow)
        self.setupGuiLogTab(self.loggingOptions.settings["file_log"])
        self.fontOptions = FontOptions(self.defAppFont, self.mainWindow)
        self.whatsThisOptions = WhatsThisOptions(self.mainWindow)
        self.clickNLoadForwarderOptions = ClickNLoadForwarderOptions(self.mainWindow)
        self.automaticReloadingOptions = AutomaticReloadingOptions(self.mainWindow)
        self.languageOptions = LanguageOptions(self.mainWindow)
        self.captchaOptions = CaptchaOptions(self.mainWindow)
        self.connWindow = ConnectionManager(self.connManagerDisableConnect)
        self.clickNLoadForwarder = ClickNLoadForwarder()
        self.mainloop = self.Loop(self)
        self.connectSignals()

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
            if self.debugLogLevel == 0: lvl = logging.DEBUG0
            elif self.debugLogLevel == 1: lvl = LoggingLevels.logging.DEBUG1
            elif self.debugLogLevel == 2: lvl = LoggingLevels.logging.DEBUG2
            elif self.debugLogLevel == 3: lvl = LoggingLevels.logging.DEBUG3
            elif self.debugLogLevel == 4: lvl = LoggingLevels.logging.DEBUG4
            elif self.debugLogLevel == 5: lvl = LoggingLevels.logging.DEBUG5
            elif self.debugLogLevel == 6: lvl = LoggingLevels.logging.DEBUG6
            elif self.debugLogLevel == 7: lvl = LoggingLevels.logging.DEBUG7
            elif self.debugLogLevel == 8: lvl = LoggingLevels.logging.DEBUG8
            elif self.debugLogLevel == 9: lvl = LoggingLevels.logging.DEBUG9
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
        self.refreshGuiLogFirst = True
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
        for dummy, section in pcfg.iteritems():
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
        connected = self.connector.connectProxy()
        self.connectTimeout(False)
        if not connected:
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
        self.loadWindowFromConfig()
        self.mainWindow.update()
        self.initQueue()
        self.initCollector()
        self.clipboard = self.app.clipboard()
        self.connect(self.clipboard, SIGNAL('dataChanged()'), self.slotClipboardChange)
        self.mainWindow.tabs["settings"]["w"].setConnector(self.connector)
        self.createTrayIcon()
        if self.trayOptions.settings["EnableTray"]:
            self.emit(SIGNAL("showTrayIcon"))
        else:
            self.emit(SIGNAL("hideTrayIcon"))
        self.mainloop.start()
        self.allowUserActions(True)

    def connectTimeout(self, start=True):
        if start:
            timeout = 30.0 #seconds
            self.connectTimeoutTimer = Timer(timeout, self.quitConnTimeout)
            self.connectTimeoutTimer.start()
        else:
            self.connectTimeoutTimer.cancel()

    def stopMain(self):
        """
            stop all refresh threads, save and hide main window
        """
        self.allowUserActions(False)
        self.disconnect(self.clipboard, SIGNAL('dataChanged()'), self.slotClipboardChange)
        self.disconnect(self.connector, SIGNAL("connectionLost"), self.slotConnectionLost)
        self.mainWindow.tabs["accounts"]["view"].model.timer.stop()
        self.clickNLoadForwarder.stop()
        self.mainloop.stop()
        self.queue.stop()
        self.prepareForSaveOptionsAndWindow(self.stopMain_continue)

    def stopMain_continue(self):
        self.saveWindowToConfig()
        self.saveOptionsToConfig()
        self.connector.disconnectProxy()
        if self.connectionLost:
            self.log.error("main.stopMain_continue: Lost connection to the server")
            self.messageBox_08()
        self.deleteTrayIcon()
        self.init()

    def messageBox_08(self):
        msg = _("Lost connection to the server.")
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
            self.tray.menuAdd.setEnabled(self.corePermissions["ADD"])
        else:
            self.tray.menuAdd.setEnabled(False)

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
        "Could not get information about our permissions for this remote login.\n"
        "This happens when the server is running on the localhost\n"
        "with 'No authentication on local connections' enabled\n"
        "and you try to login with invalid username/password.\n"
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
        self.connect(self.connector,           SIGNAL("connectTimeout"), self.connectTimeout)
        self.connect(self.connector,           SIGNAL("msgBoxError"), self.slotMsgBoxError)
        self.connect(self.clickNLoadForwarder, SIGNAL("msgBoxError"), self.slotMsgBoxError)
        self.connect(self.connWindow,          SIGNAL("saveConnection"), self.slotSaveConnection)
        self.connect(self.connWindow,          SIGNAL("saveAllConnections"), self.slotSaveAllConnections)
        self.connect(self.connWindow,          SIGNAL("removeConnection"), self.slotRemoveConnection)
        self.connect(self.connWindow,          SIGNAL("connect"), self.slotConnect, Qt.QueuedConnection)
        self.connect(self.connWindow,          SIGNAL("quitConnWindow"), self.slotQuitConnWindow)
        self.connect(self.fontOptions,         SIGNAL("appFontChanged"), self.slotAppFontChanged)
        self.connect(self.mainWindow,          SIGNAL("connector"), self.slotShowConnector)
        self.connect(self.mainWindow,          SIGNAL("mainWindowState"), self.slotMainWindowState, Qt.QueuedConnection)
        self.connect(self.mainWindow,          SIGNAL("mainWindowPaintEvent"), self.slotMainWindowPaintEvent, Qt.QueuedConnection)
        self.connect(self.mainWindow,          SIGNAL("showCorePermissions"), self.slotShowCorePermissions)
        self.connect(self.mainWindow,          SIGNAL("quitCore"), self.slotQuitCore)
        self.connect(self.mainWindow,          SIGNAL("restartCore"), self.slotRestartCore)
        self.connect(self.mainWindow,          SIGNAL("showLoggingOptions"), self.slotShowLoggingOptions)
        self.connect(self.mainWindow,          SIGNAL("showNotificationOptions"), self.slotShowNotificationOptions)
        self.connect(self.mainWindow,          SIGNAL("showOtherOptions"), self.slotShowOtherOptions)
        self.connect(self.mainWindow,          SIGNAL("showTrayOptions"), self.slotShowTrayOptions)
        self.connect(self.mainWindow,          SIGNAL("showClickNLoadForwarderOptions"), self.slotShowClickNLoadForwarderOptions)
        self.connect(self.mainWindow,          SIGNAL("showAutomaticReloadingOptions"), self.slotShowAutomaticReloadingOptions)
        self.connect(self.mainWindow,          SIGNAL("showCaptchaOptions"), self.slotShowCaptchaOptions)
        self.connect(self.mainWindow,          SIGNAL("showCaptcha"), self.slotShowCaptcha)
        self.connect(self.mainWindow,          SIGNAL("showFontOptions"), self.slotShowFontOptions)
        self.connect(self.mainWindow,          SIGNAL("showWhatsThisOptions"), self.slotShowWhatsThisOptions)
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
        self.connect(self.mainWindow,          SIGNAL("selectAll"), self.slotSelectAll)
        self.connect(self.mainWindow,          SIGNAL("deselectAll"), self.slotDeselectAll)
        self.connect(self.mainWindow,          SIGNAL("selectAllPackages"), self.slotSelectAllPackages)
        self.connect(self.mainWindow,          SIGNAL("deselectAllPackages"), self.slotDeselectAllPackages)
        self.connect(self.mainWindow,          SIGNAL("advancedSelect"), self.slotAdvancedSelect)
        self.connect(self.mainWindow,          SIGNAL("removeLinkDupes"), self.slotRemoveLinkDupes)
        self.connect(self.mainWindow,          SIGNAL("sortPackages"), self.slotSortPackages)
        self.connect(self.mainWindow,          SIGNAL("sortLinks"), self.slotSortLinks)
        self.connect(self.mainWindow,          SIGNAL("expandAll"), self.slotExpandAll)
        self.connect(self.mainWindow,          SIGNAL("collapseAll"), self.slotCollapseAll)
        self.connect(self.mainWindow,          SIGNAL("showAddPackage"), self.slotShowAddPackage)
        self.connect(self.mainWindow,          SIGNAL("showAddLinks"), self.slotShowAddLinks)
        self.connect(self.mainWindow,          SIGNAL("addContainer"), self.slotAddContainer)
        self.connect(self.mainWindow,          SIGNAL("stopAllDownloads"), self.slotStopAllDownloads)
        self.connect(self.mainWindow,          SIGNAL("captchaStatusButton"), self.slotCaptchaStatusButton)
        self.connect(self.mainWindow,          SIGNAL("restartFailed"), self.slotRestartFailed)
        self.connect(self.mainWindow,          SIGNAL("deleteFinished"), self.slotDeleteFinished)
        self.connect(self.mainWindow,          SIGNAL("pullOutPackages"), self.slotPullOutPackages)
        self.connect(self.mainWindow,          SIGNAL("reloadAccounts"), self.slotReloadAccounts)
        self.connect(self.mainWindow,          SIGNAL("showAbout"), self.slotShowAbout)
        self.connect(self.mainWindow,          SIGNAL("mainWindowClose"), self.slotMainWindowClose)

        self.connect(self.mainWindow.mactions["exit"], SIGNAL("triggered()"), self.slotQuit)
        self.connect(self.mainWindow.captchaDialog, SIGNAL("done"), self.slotCaptchaDone)
        self.connect(self.mainWindow.newPackDock, SIGNAL("newPackDockPaintEvent"), self.slotActivateNewPackDock, Qt.QueuedConnection)
        self.connect(self.mainWindow.newPackDock, SIGNAL("newPackDockClosed"), self.slotNewPackDockClosed)
        self.connect(self.mainWindow.newPackDock, SIGNAL("topLevelChanged(bool)"), self.slotNewPackDockTopLevelChanged, Qt.QueuedConnection)
        self.connect(self.mainWindow.newLinkDock, SIGNAL("newLinkDockPaintEvent"), self.slotActivateNewLinkDock, Qt.QueuedConnection)
        self.connect(self.mainWindow.newLinkDock, SIGNAL("newLinkDockClosed"), self.slotNewLinkDockClosed)
        self.connect(self.mainWindow.newLinkDock, SIGNAL("topLevelChanged(bool)"), self.slotNewLinkDockTopLevelChanged, Qt.QueuedConnection)

        self.packageEdit.connect(self.packageEdit.saveBtn, SIGNAL("clicked()"), self.slotEditPackageSave)

    def slotNewPackDockTopLevelChanged(self, floating):
        """
            package dock event signal, docked/undocked
        """
        if self.tray is None:
            return
        self.log.debug4("main.slotNewPackDockTopLevelChanged: floating:%s" % floating)
        if self.trayState["hiddenInTray"]:
            if not floating and not self.mainWindow.newPackDock.isHidden():
                self.geoOther["packDockTray"] = self.mainWindow.newPackDock.geo
        else:
            if floating:
                self.scheduleMainWindowPaintEventAction(pdGeo=self.geoOther["packDock"])
                self.mainWindow.update()
            else:
                self.geoOther["packDock"] = self.mainWindow.newPackDock.geo
                self.mainWindow.newPackDock.raise_() # activate tab

    def slotNewLinkDockTopLevelChanged(self, floating):
        """
            link dock event signal, docked/undocked
        """
        if self.tray is None:
            return
        self.log.debug4("main.slotNewLinkDockTopLevelChanged: floating:%s" % floating)
        if self.trayState["hiddenInTray"]:
            if not floating and not self.mainWindow.newLinkDock.isHidden():
                self.geoOther["linkDockTray"] = self.mainWindow.newLinkDock.geo
        else:
            if floating:
                self.scheduleMainWindowPaintEventAction(plGeo=self.geoOther["linkDock"])
                self.mainWindow.update()
            else:
                self.geoOther["linkDock"] = self.mainWindow.newLinkDock.geo
                self.mainWindow.newLinkDock.raise_() # activate tab

    def waitForPaintEvents(self, cnt, msec=5000):
        """
            wait until cnt main window paint events passed
        """
        timeout = self.mainWindow.time_msec() + msec
        while True:
            ec = self.mainWindow.eD["pCount"]
            if ec >= cnt:
                self.log.debug4("main.waitForPaintEvents: %d events passed (min: %d)" % (ec, cnt))
                return ec
            if self.mainWindow.time_msec() > timeout:
                self.log.error("main.waitForPaintEvents: Timeout waiting for %d events, %d events passed" % (cnt, ec))
                return ec
            self.app.processEvents()

    def waitForPackDockPaintEvents(self, cnt, msec=5000):
        """
            wait until cnt package dock paint window events passed
        """
        timeout = self.mainWindow.time_msec() + msec
        while True:
            ec = self.mainWindow.newPackDock.paintEventCounter
            if ec >= cnt:
                self.log.debug4("main.waitForPackDockPaintEvents: %d events passed (min: %d)" % (ec, cnt))
                return ec
            if self.mainWindow.time_msec() > timeout:
                self.log.error("main.waitForPackDockPaintEvents: Timeout waiting for %d events, %d events passed" % (cnt, ec))
                return ec
            self.app.processEvents()

    def waitForLinkDockPaintEvents(self, cnt, msec=5000):
        """
            wait until cnt link dock window paint events passed
        """
        timeout = self.mainWindow.time_msec() + msec
        while True:
            ec = self.mainWindow.newLinkDock.paintEventCounter
            if ec >= cnt:
                self.log.debug4("main.waitForLinkDockPaintEvents: %d events passed (min: %d)" % (ec, cnt))
                return ec
            if self.mainWindow.time_msec() > timeout:
                self.log.error("main.waitForLinkDockPaintEvents: Timeout waiting for %d events, %d events passed" % (cnt, ec))
                return ec
            self.app.processEvents()

    def createTrayIcon(self):
        self.trayState = {"p": {"f": False, "h": False, "f&!h": False}, "l": {"f": False, "h": False, "f&!h": False}}
        self.trayState["hiddenInTray"] = False
        self.trayState["ignoreMinimizeToggled"] = False
        self.trayState["maximized"] = self.mainWindow.isMaximized()
        self.trayState["unmaxed_pos"]  = self.geoUnmaximized["unmaxed_pos"]
        self.trayState["unmaxed_size"] = self.geoUnmaximized["unmaxed_size"]
        self.trayState["restore_unmaxed_geo"] = True if (self.trayState["maximized"]) and (self.trayState["unmaxed_pos"] is not None) and (self.trayState["unmaxed_size"] is not None) else False
        self.tray = TrayIcon()
        self.tray.setupIcon(self.trayOptions.settings["IconFile"])
        self.notification = Notification(self.tray)
        self.connect(self, SIGNAL("showTrayIcon"),          self.tray.show)
        self.connect(self, SIGNAL("hideTrayIcon"),          self.tray.hide)
        self.connect(self, SIGNAL("setupIcon"),             self.tray.setupIcon)
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
            self.connect(self.tray.debugTrayAction,        SIGNAL("triggered()"), self.debugTray)
            self.connect(self.tray.debugMsgBoxTest1Action, SIGNAL("triggered()"), self.debugMsgBoxTest1)
            self.connect(self.tray.debugMsgBoxTest2Action, SIGNAL("triggered()"), self.debugMsgBoxTest2)
            self.connect(self.tray.debugKillAction,        SIGNAL("triggered()"), self.debugKill)
        self.connect(self.mainWindow, SIGNAL("minimizeToggled"), self.slotMinimizeToggled)
        self.connect(self.mainWindow, SIGNAL("maximizeToggled"), self.slotMaximizeToggled)

    def deleteTrayIcon(self):
        self.disconnect(self, SIGNAL("showTrayIcon"),          self.tray.show)
        self.disconnect(self, SIGNAL("hideTrayIcon"),          self.tray.hide)
        self.disconnect(self, SIGNAL("setupIcon"),             self.tray.setupIcon)
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
            self.disconnect(self.tray.debugTrayAction,        SIGNAL("triggered()"), self.debugTray)
            self.disconnect(self.tray.debugMsgBoxTest1Action, SIGNAL("triggered()"), self.debugMsgBoxTest1)
            self.disconnect(self.tray.debugMsgBoxTest2Action, SIGNAL("triggered()"), self.debugMsgBoxTest2)
            self.disconnect(self.tray.debugKillAction,        SIGNAL("triggered()"), self.debugKill)
        self.disconnect(self.mainWindow, SIGNAL("minimizeToggled"), self.slotMinimizeToggled)
        self.disconnect(self.mainWindow, SIGNAL("maximizeToggled"), self.slotMaximizeToggled)
        self.tray.menu.deleteLater()
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
            self.unminimizeMainWindow()   # needed on windows os
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
        if QApplication.activeModalWidget() is not None:
            self.log.debug4("main.hideInTray: ignored, due to an active modal widget")
            return
        self.log.debug4("main.hideInTray: triggered")
        self.allowUserActions(False)
        s = self.trayState
        s["geo"] = self.mainWindow.saveGeometry()
        s["state"] = self.mainWindow.saveState()
        s["p"]["f"] = self.mainWindow.newPackDock.isFloating()
        s["p"]["h"] = self.mainWindow.newPackDock.isHidden()
        s["p"]["f&!h"] = s["p"]["f"] and not s["p"]["h"]
        s["l"]["f"] = self.mainWindow.newLinkDock.isFloating()
        s["l"]["h"] = self.mainWindow.newLinkDock.isHidden()
        s["l"]["f&!h"] = s["l"]["f"] and not s["l"]["h"]
        if s["p"]["f"]: self.geoOther["packDock"] = self.mainWindow.newPackDock.geometry()
        if s["l"]["f"]: self.geoOther["linkDock"] = self.mainWindow.newLinkDock.geometry()
        s["ignoreMinimizeToggled"] = True
        self.mainWindow.hide()
        self.unminimizeMainWindow()     # needed on windows os
        self.mainWindow.newPackDock.hide()
        self.unminimizeNewPackDock()    # needed on lxde and lxqt when minimized to tray
        self.mainWindow.newLinkDock.hide()
        self.unminimizeNewLinkDock()    # needed on lxde and lxqt when minimized to tray
        self.emit(SIGNAL("traySetShowActionText"), True)
        s["hiddenInTray"] = True   # must be set before allowUserActions(True)
        s["restore_unmaxed_geo"] = s["maximized"]
        s["ignoreMinimizeToggled"] = False
        self.allowUserActions(True)
        self.log.debug4("main.hideInTray: done")

    def unminimizeMainWindow(self):
        self.mainWindow.setWindowState(self.mainWindow.windowState() & ~Qt.WindowMinimized)

    def unminimizeNewPackDock(self):
        self.mainWindow.newPackDock.setWindowState(self.mainWindow.newPackDock.windowState() & ~Qt.WindowMinimized)

    def unminimizeNewLinkDock(self):
        self.mainWindow.newLinkDock.setWindowState(self.mainWindow.newLinkDock.windowState() & ~Qt.WindowMinimized)

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
        if self.mainWindow.newPackDock.isFloating() and not self.mainWindow.newPackDock.isHidden():
            self.geoOther["packDockTray"] = self.mainWindow.newPackDock.geo
        if self.mainWindow.newLinkDock.isFloating() and not self.mainWindow.newLinkDock.isHidden():
            self.geoOther["linkDockTray"] = self.mainWindow.newLinkDock.geo
        # hide and dock in case they were shown via the tray icon menu
        pe(); self.mainWindow.newPackDock.hide()
        pe(); self.mainWindow.newLinkDock.hide()
        pe(); self.mainWindow.newPackDock.setFloating(False)
        pe(); self.mainWindow.newLinkDock.setFloating(False)
        pe(); self.mainWindow.eD["pCount"] = 0
        if self.fixFirstShowFromTrayWhenLoadedMaximized:
            if s["maximized"]:
                self.mainWindow.showMaximized()     # needed on mate when started maximized and hidden to tray straightaway
            else:
                self.mainWindow.show()
            self.fixFirstShowFromTrayWhenLoadedMaximized = False
        else:
            self.mainWindow.show()
        self.waitForPaintEvents(1)
        numOfPaintEventsToWait = 1  # ignore maximize/unmaximize events until num paintEvents happened
        self.mainWindow.eD["pCount"] = 0
        self.mainWindow.newPackDock.paintEventCounter = 0
        self.mainWindow.newLinkDock.paintEventCounter = 0
        self.mainWindow.restoreState(s["state"]) # docks
        pe(); self.unminimizeNewPackDock()  # needed on gnome 3 and mint cinnamon when minimized to tray
        pe(); self.unminimizeNewLinkDock()  # needed on gnome 3 and mint cinnamon when minimized to tray
        if s["maximized"]:
            self.mainWindow.showMaximized() # needed on mint cinnamon
        self.waitForPaintEvents(1)
        if s["p"]["f&!h"]:
            self.waitForPackDockPaintEvents(1)
            pdgeo = self.geoOther["packDock"]
        else:
            pdgeo = None
        if s["l"]["f&!h"]:
            self.waitForLinkDockPaintEvents(1)
            plgeo = self.geoOther["linkDock"]
        else:
            plgeo = None
        if not s["maximized"]:
            if self.trayOptions.settings["RestoreGeo"]:
                pe(); self.mainWindow.restoreGeometry(s["geo"])
            if prepForSave: return
            if self.trayOptions.settings["RestoreGeo"]:
                self.scheduleMainWindowPaintEventAction(pos=self.mainWindow.pos(), size=self.mainWindow.size(), pdGeo=pdgeo, plGeo=plgeo)
            else:
                self.scheduleMainWindowPaintEventAction()
                self.mainWindow.update(); pe()
            self.showFromTray_continue()
        else:
            if prepForSave: return
            if self.trayOptions.settings["RestoreGeo"]:
                self.scheduleMainWindowPaintEventAction(showFromTrayContinue=numOfPaintEventsToWait, pdGeo=pdgeo, plGeo=plgeo)
            else:
                self.scheduleMainWindowPaintEventAction(showFromTrayContinue=numOfPaintEventsToWait)
            s["showFromTrayShowTime"] = self.mainWindow.time_msec()
            for dummy in range(numOfPaintEventsToWait + 2):
                self.mainWindow.update();pe();pe();pe();pe();pe()

    def showFromTray_continue(self):
        s = self.trayState
        self.log.debug4("main.showFromTray_continue: entered")
        if s["maximized"]:
            self.log.debug4("main.showFromTray_continue: mainWindow is maximized, delay: %d msec", self.mainWindow.time_msec() - self.trayState["showFromTrayShowTime"])
        self.emit(SIGNAL("traySetShowActionText"), False)
        s["hiddenInTray"] = False  # must be updated before allowUserActions(True)
        self.allowUserActions(True)
        self.log.debug4("main.showFromTray_continue: done")

    def slotMinimizeToggled(self, minimized):
        """
            emitted from main window in changeEvent()
        """
        if self.tray is None:
            return
        if not self.trayOptions.settings["EnableTray"]:
            return
        if self.trayState["hiddenInTray"]:
            return
        if self.trayState["ignoreMinimizeToggled"]:
            return
        self.log.debug4("main.slotMinimizeToggled: %s" % minimized)
        if minimized:   # minimized flag was set
            if self.trayOptions.settings["Minimize2Tray"] and (QApplication.activeModalWidget() is None):
                self.emit(SIGNAL("minimize2Tray"))   # queued connection
            else:
                self.emit(SIGNAL("traySetShowActionText"), True)
        else:           # minimized flag was unset
            self.emit(SIGNAL("traySetShowActionText"), False)

    def slotMinimize2Tray(self):
        """
            emitted from slotMinimizeToggled()
        """
        if self.trayState["hiddenInTray"]:
            self.log.error("main.slotMinimize2Tray: Already hidden in tray")
            return
        self.log.debug4("main.slotMinimize2Tray: triggered")
        self.hideInTray()

    def slotMaximizeToggled(self, maximized):
        """
            emitted from main window in changeEvent()
        """
        if self.tray is None:
            self.log.error("main.slotMaximizeToggled: self.tray is None, maximized: %s" % maximized)
            return
        if self.trayState["hiddenInTray"]:
            self.log.debug4("main.slotMaximizeToggled: ignored: hidden in tray, maximized: %s" % maximized)
            return
        if self.mainWindow.isHidden():
            self.log.error("main.slotMaximizeToggled: mainWindow is hidden, maximized: %s" % maximized)
            return
        self.log.debug4("main.slotMaximizeToggled: maximized: %s" % maximized)
        s = self.trayState
        if maximized:   # maximized flag was set
            if s["maximized"]:
                self.log.debug4("main.slotMaximizeToggled: repeated maximize")
                return
            if self.otherOptions.settings["SecondLastNormalGeo"]:
                if self.mainWindow.eD["2ndLastNormPos"] is not None:
                    s["unmaxed_pos"] = self.mainWindow.eD["2ndLastNormPos"]
                else:
                    s["unmaxed_pos"] = self.mainWindow.pos()
                    self.log.error("main.slotMaximizeToggled: paintEventSecondLastNormalPos is None")
                if self.mainWindow.eD["2ndLastNormSize"] is not None:
                    s["unmaxed_size"] = self.mainWindow.eD["2ndLastNormSize"]
                else:
                    s["unmaxed_size"] = self.mainWindow.size()
                    self.log.error("main.slotMaximizeToggled: paintEventSecondLastNormalSize is None")
            else:
                if self.mainWindow.eD["lastNormPos"] is not None:
                    s["unmaxed_pos"] = self.mainWindow.eD["lastNormPos"]
                else:
                    s["unmaxed_pos"] = self.mainWindow.pos()
                    self.log.error("main.slotMaximizeToggled: paintEventLastNormalPos is None")
                if self.mainWindow.eD["lastNormSize"] is not None:
                    s["unmaxed_size"] = self.mainWindow.eD["lastNormSize"]
                else:
                    s["unmaxed_size"] = self.mainWindow.size()
                    self.log.error("main.slotMaximizeToggled: paintEventLastNormalSize is None")
            s["restore_unmaxed_geo"] = False
            self.log.debug4("main.slotMaximizeToggled: geometry stored,     pos: %s   size: %s" % (s["unmaxed_pos"], s["unmaxed_size"]))
        else:           # maximized flag was unset
            self.fixFirstShowFromTrayWhenLoadedMaximized = False    # fix not needed when the mainWindow was unmaximized in the meantime
            if not s["maximized"]:
                self.log.debug4("main.slotMaximizeToggled: repeated unmaximize")
                return
            if self.otherOptions.settings["RestoreUnmaximizedGeo"] and (s["restore_unmaxed_geo"] or self.otherOptions.settings["AlwaysRestore"]) and not QApplication.activeModalWidget():
                if self.otherOptions.settings["HideShowOnUnmax"]:
                    pdShownFloating = self.mainWindow.newPackDock.isFloating() and not self.mainWindow.newPackDock.isHidden()
                    ldShownFloating = self.mainWindow.newLinkDock.isFloating() and not self.mainWindow.newLinkDock.isHidden()
                    self.mainWindow.hide()
                    if pdShownFloating:
                        self.mainWindow.newPackDock.hide()
                    if ldShownFloating:
                        self.mainWindow.newLinkDock.hide()
                    self.mainWindow.eD["pCount"] = 0
                    self.mainWindow.show()
                    self.waitForPaintEvents(1)
                    self.log.debug4("main.slotMaximizeToggled: Option '%s' done, show()" % str(self.otherOptions.cbHideShowOnUnmax.text()))
                    if pdShownFloating:
                        self.mainWindow.newPackDock.show()
                    if ldShownFloating:
                        self.mainWindow.newLinkDock.show()
                restoreDocks = self.mainWindow.eD["pStateSig"]    # restore docked widgets width (divider position) at first unmaximize when the app was lauched maximized
                if self.mainWindow.eD["pStateSig"]:
                    self.mainWindow.eD["pStateSig"] = False
                self.scheduleMainWindowPaintEventAction(pos=s["unmaxed_pos"], size=s["unmaxed_size"], refreshGeo=self.otherOptions.settings["RefreshGeo"], restoreDocks=restoreDocks)
                self.mainWindow.update()
                self.log.debug4("main.slotMaximizeToggled: geometry restored,   pos: %s   size: %s" % (s["unmaxed_pos"], s["unmaxed_size"]))
            else:
                self.log.debug4("main.slotMaximizeToggled: geo. not restored,   pos: %s   size: %s" % (s["unmaxed_pos"], s["unmaxed_size"]))
        s["maximized"] = maximized

    def slotRestoreDocks(self):
        self.mainWindow.newPackDock.paintEventCounter = 0
        self.mainWindow.newLinkDock.paintEventCounter = 0
        self.mainWindow.restoreState(self.mainWindowStateFirstUnmax, self.mainWindow.version)  # also restores floating state of docks
        if self.mainWindow.newPackDock.isFloating() and not self.mainWindow.newPackDock.isHidden():
            self.waitForPackDockPaintEvents(1)
        if self.mainWindow.newLinkDock.isFloating() and not self.mainWindow.newLinkDock.isHidden():
            self.waitForLinkDockPaintEvents(1)
        self.mainWindow.raise_()
        self.mainWindow.tabw.setFocus(Qt.OtherFocusReason)
        self.mainWindow.activateWindow()
        # fire an extra fusillade for slow window managers
        for i in [10, 50, 100, 200]:
            QTimer.singleShot(i, self.mainWindow.activateWindow)
        self.log.debug4("main.slotRestoreDocks: docked widgets width (divider position) restored at first unmaximize")

    def debugTray(self):
        self.log.debug9("mainWindow pos() + size():                     pos: %s   size: %s" % (self.mainWindow.pos(), self.mainWindow.size()))
        self.log.debug9("mainWindow geometry():                         pos: %s   size: %s" % (self.mainWindow.geometry().topLeft(), self.mainWindow.geometry().size()))
        self.log.debug9("newPackDock pos() + size():                    pos: %s   size: %s" % (self.mainWindow.newPackDock.pos(), self.mainWindow.newPackDock.size()))
        self.log.debug9("newPackDock geometry():                        pos: %s   size: %s" % (self.mainWindow.newPackDock.geometry().topLeft(), self.mainWindow.newPackDock.geometry().size()))
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
        pe(); self.unminimizeNewPackDock()  # needed on gnome 3 when minimized to tray
        self.mainWindow.newPackDock.paintEventSignal = True
        pe(); self.mainWindow.newPackDock.paintEventCounter = 0
        self.mainWindow.newPackDock.show()
        if self.geoOther["packDockTray"] is not None:
            self.mainWindow.newPackDock.update()
            self.waitForPackDockPaintEvents(1)
            self.mainWindow.newPackDock.setGeometry(self.geoOther["packDockTray"])

    def slotActivateNewPackDock(self):
        self.mainWindow.newPackDock.raise_()
        self.mainWindow.newPackDock.activateWindow()

    def slotNewPackDockClosed(self):
        if self.trayState["hiddenInTray"]:
            self.geoOther["packDockTray"] = self.mainWindow.newPackDock.geo

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
        pe(); self.unminimizeNewLinkDock()  # needed on gnome 3 when minimized to tray
        self.mainWindow.newLinkDock.paintEventSignal = True
        pe(); self.mainWindow.newLinkDock.paintEventCounter = 0
        self.mainWindow.newLinkDock.show()
        if self.geoOther["linkDockTray"] is not None:
            self.mainWindow.newLinkDock.update()
            self.waitForLinkDockPaintEvents(1)
            self.mainWindow.newLinkDock.setGeometry(self.geoOther["linkDockTray"])

    def slotActivateNewLinkDock(self):
        self.mainWindow.newLinkDock.raise_()
        self.mainWindow.newLinkDock.activateWindow()

    def slotNewLinkDockClosed(self):
        if self.trayState["hiddenInTray"]:
            self.geoOther["linkDockTray"] = self.mainWindow.newLinkDock.geo

    def slotShowCaptcha(self):
        """
            from main window (menu)
            from main window (toolbar)
            from tray icon (context menu)
            show captcha
        """
        self.mainWindow.captchaDialog.emit(SIGNAL("show"), self.lastCaptchaId is None)

    def slotShowAbout(self):
        """
            emitted from main window (menu)
            show the about-box
        """
        ab = AboutBox(self.mainWindow)
        ab.exec_(CURRENT_VERSION, CURRENT_INTERNAL_VERSION)

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
        info.exec_()

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
        return self.msgBoxYesNo(text, "Q")

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
        text = _("Do you really want to restart the pyLoad server?") + "<br><i>" + _("This does not work when the server is running on a Windows OS.") + "</i>"
        return self.msgBoxYesNo(text, "Q")

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
        retval = msgb.exec_()
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

    def debugMsgBoxTest1(self):
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

    def debugMsgBoxTest2(self):
        def dm(n):
            self.log.debug9("main.debugMsgBoxTest2: showing messageBox_%s" % n)
        # Connector
        host = "looooooooooooooooooooooooong.hostname.com"
        port = 66666
        server_version = '42'
        dm("01"); self.connector.messageBox_01(host, port)
        dm("02"); self.connector.messageBox_02(host, port)                          # no explicit parent
        dm("03"); self.connector.messageBox_03(host, port, "BananaJoe", "tomato")   # no explicit parent, class AskForUserAndPassword
        dm("04"); self.connector.messageBox_04(host, port)
        dm("05"); self.connector.messageBox_05(host, port)
        dm("06"); self.connector.messageBox_06(server_version, host, port)
        # main
        pidfile = "bob/pyload.pid"
        pid = 536485
        optCat = "FooBar"
        dm("07"); self.messageBox_07()
        dm("08"); self.messageBox_08()
        dm("09"); self.messageBox_09()
        dm("12"); self.messageBox_12()
        dm("13"); self.messageBox_13()
        dm("14"); self.messageBox_14()
        dm("15"); self.messageBox_15((pidfile, pid))
        dm("16"); self.messageBox_16()
        dm("17"); self.messageBox_17()
        dm("18"); self.messageBox_18(pid)
        dm("21"); self.messageBox_21(optCat)
        dm("22"); self.messageBox_22()
        dm("23"); self.messageBox_23(pidfile, pid)
        dm("24"); self.messageBox_24()
        # ClickNLoadForwarder
        dm("19"); self.clickNLoadForwarder.messageBox_19()
        dm("20"); self.clickNLoadForwarder.messageBox_20()

    def debugKill(self):
        self.log.debug9("main.debugKill: terminate process")
        self.quitConnTimeout()

    def slotNotificationMessage(self, status, name):
        """
            notifications
        """
        s = self.notificationOptions.settings
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
                    self.emit(SIGNAL("showMessage"), _("New Captcha Request"))
            elif status == 102:
                if s["CaptchaInteractive"]:
                    self.emit(SIGNAL("showMessage"), _("New Interactive Captcha Request"))

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
        self.mainWindow.statuswItems["packages"].lbl2.setText("%i" % pc)
        self.mainWindow.statuswItems["links"].lbl2.setText("%i" % fc)

    def refreshServerStatus(self):
        """
            refresh server status and overall speed in the status bar
        """
        if self.corePermissions["LIST"]:
            s = self.connector.proxy.statusServer()
            if s.pause:
                self.mainWindow.actions["status_pause"].setChecked(True)
                self.mainWindow.statuswItems["status"].lbl2.setText(_("Paused"))
            else:
                self.mainWindow.actions["status_start"].setChecked(True)
                self.mainWindow.statuswItems["status"].lbl2.setText(_("Running"))
            self.mainWindow.statuswItems["speed"].lbl2.setText(formatSpeed(s.speed))
        if self.corePermissions["STATUS"]:
            self.mainWindow.statuswItems["space"].lbl2.setText(formatSize(self.serverStatus["freespace"]))

    def getGuiLog(self, offset=0):
        """
            returns most recent gui log entries
        """
        filename = join(self.loggingOptions.settings["log_folder"], "guilog.txt")
        try:
            fh = open(filename, "r")
            lines = fh.readlines()
            fh.close()
        except Exception:
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
        except Exception:
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
        if self.refreshGuiLogFirst:
            lines = lines[-100:]    # load only the last lines in the widget
            self.refreshGuiLogFirst = False
        for line in lines:
            self.mainWindow.tabs["guilog"]["text"].emit(SIGNAL("append(QString)"), line.strip("\n"))
        cursor = self.mainWindow.tabs["guilog"]["text"].textCursor()
        cursor.movePosition(QTextCursor.End, QTextCursor.MoveAnchor)
        cursor.movePosition(QTextCursor.StartOfLine, QTextCursor.MoveAnchor)
        self.mainWindow.tabs["guilog"]["text"].setTextCursor(cursor)

    def refreshCoreLog(self, first):
        """
            update core log window
        """
        if not self.corePermissions["LOGS"]:
            return
        offset = self.mainWindow.tabs["corelog"]["text"].logOffset
        if offset == 0:
            if first:
                self.log.debug9("main.refreshCoreLog: Fetching server log ...")
            lines = self.connector.proxy.getLog(offset)
            if first:
                self.log.debug9("main.refreshCoreLog: Server log fetched")
            if not lines: # zero size log file
                return
            self.mainWindow.tabs["corelog"]["text"].logOffset += len(lines)
            if first:
                lines = lines[-100:]    # load only the last lines in the widget
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
                data["name"] = unicode("- unnamed -")
            else:
                data["name"] = unicode(subs["name"].text())
            if data["type"] == "remote":
                if not subs.has_key("server"):
                    continue
                else:
                    data["host"] = unicode(subs["server"].text())
                    data["user"] = unicode(subs["server"].attribute("user", "admin"))
                    data["port"] = int(subs["server"].attribute("port", "7227"))
                    data["password"] = unicode(subs["server"].attribute("password", ""))
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
        except Exception:
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
            if self.configdir:
                pyloadConf = self.homedir + sep + "pyload.conf"
            else:
                pyloadConf = abspath("pyload.conf")
            if not (os.path.isfile(pyloadConf) and os.access(pyloadConf, os.R_OK)):
                self.messageBox_22()
                self.init()
                return

            from pyLoadCore import Core
            if not self.core:
                class CoreSignal(QObject):
                    coreRestart = pyqtSignal()
                class Core_(Core):
                    def __init__(self):
                        Core.__init__(self)
                        self.signal = CoreSignal()
                        self.internal_core_restart = False
                    # Workaround os._exit() called when the Core quits. This is possible because the present Core code calls os._exit() right after calling removeLogger()
                    def removeLogger(self):
                         Core.removeLogger(self)
                         thread.exit()
                    # Workaround Core restart invoked by the UpdateManager plugin
                    def restart(self):
                        if self.internal_core_restart:
                            return
                        self.internal_core_restart = True
                        self.threadManager.pause = True
                        self.signal.emit(SIGNAL("coreRestart()"))

                self.connManagerDisableConnect = True

                del sys.argv[1:] # do not pass our command-line arguments to the core
                #sys.argv[1:2] = ["--foo=bar", "--debug"] # pass these instead

                try:
                    self.core = Core_()
                except Exception:
                    return self.errorInternalCoreStartup(self.messageBox_14)
                if self.configdir: pf = self.homedir + sep + self.core.pidfile
                else:              pf = abspath(self.core.pidfile)
                if os.name != "nt":
                    pid = self.core.isAlreadyRunning()
                    if pid: return self.errorInternalCoreStartup(self.messageBox_15, (pf, pid))
                else:
                    pid = self.core.checkPidFile()
                    if pid and not self.messageBox_23(pf, pid): self.init(); return
                self.connect(self.core.signal, SIGNAL("coreRestart()"), self.slotCoreRestart, Qt.QueuedConnection)
                self.core.startedInGui = True
                try:
                    thread.start_new_thread(self.core.start, (False, True))
                except Exception:
                    return self.errorInternalCoreStartup(self.messageBox_16)
                # wait max 15sec for startup
                for dummy in range(0, 150):
                    if self.core.running:
                        break
                    sleep(0.1)
                if not self.core.running:
                    return self.errorInternalCoreStartup(self.messageBox_17)

                self.translation.install(unicode=True) # restore the gui language
                self.connector.proxy = self.core.api
                self.connector.internal = True

            self.mainWindow.mactions["quitcore"].setEnabled(False)
            self.mainWindow.mactions["restartcore"].setEnabled(False)
            self.mainWindow.mactions["cnlfwding"].setEnabled(False)
            self.mainWindow.setWindowTitle(_("pyLoad Client") + " - " + data["name"] + " [via API]")

        QTimer.singleShot(0, self.startMain)

    def errorInternalCoreStartup(self, mb, arg=None):
        if arg is None:
            mb()
        else:
            mb(arg)
        self.init()
        return

    def slotCoreRestart(self):
        """
            the internal server wants to restart
        """
        self.log.info("The internal server wants to restart, exiting pyLoad Client")
        QTimer.singleShot(60000, self.slotQuit)
        self.messageBox_24()
        QTimer.singleShot(0, self.slotQuit)

    def messageBox_22(self):
        text = _("Cannot start the internal server because the server is not configured.\n"
        "Please run the server setup from console, respectively from\ncommand prompt if you are on Windows OS.\n\nFor example:\n"
        ) + "pyLoadCore.py -s"
        self.msgBoxOk(text, "C")

    def messageBox_14(self):
        text = _("Internal server initialization failed.")
        self.msgBoxOk(text, "C")

    def messageBox_15(self, (pidfile, pid)):
        text =  _("Cannot start the internal server.")
        text += "\n" + _("A pyLoad server for this configuration is already running.")
        text += "\n" + "PID-file: " + unicode(pidfile)
        text += "\n" + "PID: %d" % int(pid)
        self.msgBoxOk(text, "C")

    def messageBox_23(self, pidfile, pid):
        text  = _("A pyLoad server for this configuration is already running")
        text += "\n" + _("or the server was not shut down properly last time.")
        text += "\n" + _("PID-file: ") + unicode(pidfile)
        text += "\n" + "PID: %d" % int(pid)
        text += "\n\n" + _("Do you want to start the internal server anyway?")
        return self.msgBoxYesNo(text, "C")

    def messageBox_16(self):
        text = _("Failed to start internal server thread.")
        self.msgBoxOk(text, "C")

    def messageBox_17(self):
        text = _("Failed to start internal server.")
        self.msgBoxOk(text, "C")

    def messageBox_24(self):
        text = _("The internal server wants to restart.")
        text += "\n" + _("Probably for plugin updates to take effect.")
        text += "\n\n" + _("Therefore, we must exit the application")
        text += "\n" + _("and you have to restart it manually.")
        text += "\n\n" + _("Exiting in 60 seconds ...")
        text += "\n" + _("Close this window to exit immediately.")
        self.msgBoxOk(text, "I")

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
        nm = name if (name and name.strip()) else "Unnamed Package"
        if queue:
            pack = self.connector.proxy.addPackage(nm, links, Destination.Queue)
        else:
            pack = self.connector.proxy.addPackage(nm, links, Destination.Collector)
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
            (pid, dummy, isPack) = s
            if isPack:
                packs.append(pid)
        if len(packs) == 1:
            self.connector.proxy.addFiles(packs[0], links)
            self.mainWindow.newLinkDock.widget.box.clear()
        elif len(packs) == 0:
            self.mainWindow.newLinkDock.widget.slotMsgShow("<b>" + (_("Error, no package selected in %s.") % txt) + "</b>")
        else:
            self.mainWindow.newLinkDock.widget.slotMsgShow("<b>" + (_("Error, multiple packages selected in %s.") % txt) + "</b>")

    def slotShowAddPackage(self):
        """
            emitted from main window
            show new-package dock
        """
        if self.mainWindow.newPackDock.isHidden():
            self.mainWindow.newPackDock.paintEventCounter = 0
            self.mainWindow.newPackDock.show()
            if self.mainWindow.newPackDock.isFloating() and self.geoOther["packDock"] is not None:
                self.mainWindow.newPackDock.update()
                self.waitForPackDockPaintEvents(1)
                self.mainWindow.newPackDock.setGeometry(self.geoOther["packDock"])
        if not self.mainWindow.newPackDock.isFloating():
            self.mainWindow.newPackDock.raise_() # activate tab

    def slotShowAddLinks(self):
        """
            emitted from main window
            show new-links dock
        """
        if self.mainWindow.newLinkDock.isHidden():
            self.mainWindow.newLinkDock.paintEventCounter = 0
            self.mainWindow.newLinkDock.show()
            if self.mainWindow.newLinkDock.isFloating() and self.geoOther["linkDock"] is not None:
                self.mainWindow.newLinkDock.update()
                self.waitForLinkDockPaintEvents(1)
                self.mainWindow.newLinkDock.setGeometry(self.geoOther["linkDock"])
        if not self.mainWindow.newLinkDock.isFloating():
            self.mainWindow.newLinkDock.raise_() # activate tab

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
        # the core doesn't like unicode filenames here
        fn = QString(filename).toLatin1()
        self.connector.proxy.uploadContainer(str(fn), content)

    def prepareForSaveOptionsAndWindow(self, contFunc):
        """
            restore main window and dock windows, unmaximize main window if desired
            before saving their state to the config file and disconnecting from server
        """
        self.geoUnmaximized = {}
        self.geoUnmaximized["unmaxed_pos"]  = self.trayState["unmaxed_pos"]
        self.geoUnmaximized["unmaxed_size"] = self.trayState["unmaxed_size"]
        self.geoUnmaximized["maximized"]    = self.trayState["maximized"]
        self.log.debug4("main.prepareForSaveOptionsAndWindow: save geoUnmaximized to xml:  pos: %s                     size: %s" % (self.geoUnmaximized["unmaxed_pos"], self.geoUnmaximized["unmaxed_size"]))
        if not self.mainWindow.captchaDialog.isHidden():
            self.geoOther["captchaDialog"] = self.mainWindow.captchaDialog.geometry()
        else:
            self.geoOther["captchaDialog"] = self.mainWindow.captchaDialog.geo
        if self.trayOptions.settings["EnableTray"] and self.trayState["hiddenInTray"]:
            self.log.debug4("main.prepareForSaveOptionsAndWindow: showFromTray()")
            self.showFromTray(True)
            QTimer.singleShot(0, contFunc)
        else:
            if self.mainWindow.newPackDock.isFloating() and not self.mainWindow.newPackDock.isHidden():
                self.geoOther["packDock"] = self.mainWindow.newPackDock.geometry()
            if self.mainWindow.newLinkDock.isFloating() and not self.mainWindow.newLinkDock.isHidden():
                self.geoOther["linkDock"] = self.mainWindow.newLinkDock.geometry()
            self.log.debug4("main.prepareForSaveOptionsAndWindow: contFunc()")
            QTimer.singleShot(0, contFunc)

    def saveOptionsToConfig(self):
        """
            save options to the config file
        """
        mainWindowNode = self.parser.xml.elementsByTagName("mainWindow").item(0)
        if mainWindowNode.isNull():
            mainWindowNode = self.parser.xml.createElement("mainWindow")
            self.parser.root.appendChild(mainWindowNode)
        optionsNotifications = str(QByteArray(str(self.notificationOptions.settings)).toBase64())
        optionsLogging = str(QByteArray(str(self.loggingOptions.settings)).toBase64())
        optionsClickNLoadForwarder = str(self.clickNLoadForwarderOptions.settings["fromPort"])
        optionsAutomaticReloading = str(QByteArray(str(self.automaticReloadingOptions.settings)).toBase64())
        optionsCaptcha = str(QByteArray(str(self.captchaOptions.settings)).toBase64())
        optionsFonts = str(QByteArray(str(self.fontOptions.settings)).toBase64())
        optionsTray = str(QByteArray(str(self.trayOptions.settings)).toBase64())
        optionsWhatsThis = str(QByteArray(str(self.whatsThisOptions.settings)).toBase64())
        optionsOther = str(QByteArray(str(self.otherOptions.settings)).toBase64())
        lastAddContainerDir = self.mainWindow.lastAddContainerDir
        optionsNotificationsNode = mainWindowNode.toElement().elementsByTagName("optionsNotifications").item(0)
        optionsLoggingNode = mainWindowNode.toElement().elementsByTagName("optionsLogging").item(0)
        optionsClickNLoadForwarderNode = mainWindowNode.toElement().elementsByTagName("optionsClickNLoadForwarder").item(0)
        optionsAutomaticReloadingNode = mainWindowNode.toElement().elementsByTagName("optionsAutomaticReloading").item(0)
        optionsCaptchaNode = mainWindowNode.toElement().elementsByTagName("optionsCaptcha").item(0)
        optionsFontsNode = mainWindowNode.toElement().elementsByTagName("optionsFonts").item(0)
        optionsTrayNode = mainWindowNode.toElement().elementsByTagName("optionsTray").item(0)
        optionsWhatsThisNode = mainWindowNode.toElement().elementsByTagName("optionsWhatsThis").item(0)
        optionsOtherNode = mainWindowNode.toElement().elementsByTagName("optionsOther").item(0)
        lastAddContainerDirNode = mainWindowNode.toElement().elementsByTagName("lastAddContainerDir").item(0)
        newOptionsNotificationsNode = self.parser.xml.createTextNode(optionsNotifications)
        newOptionsLoggingNode = self.parser.xml.createTextNode(optionsLogging)
        newOptionsClickNLoadForwarderNode = self.parser.xml.createTextNode(optionsClickNLoadForwarder)
        newOptionsAutomaticReloadingNode = self.parser.xml.createTextNode(optionsAutomaticReloading)
        newOptionsCaptchaNode = self.parser.xml.createTextNode(optionsCaptcha)
        newOptionsFontsNode = self.parser.xml.createTextNode(optionsFonts)
        newOptionsTrayNode = self.parser.xml.createTextNode(optionsTray)
        newOptionsWhatsThisNode = self.parser.xml.createTextNode(optionsWhatsThis)
        newOptionsOtherNode = self.parser.xml.createTextNode(optionsOther)
        newLastAddContainerDirNode = self.parser.xml.createTextNode(lastAddContainerDir)
        optionsNotificationsNode.removeChild(optionsNotificationsNode.firstChild())
        optionsNotificationsNode.appendChild(newOptionsNotificationsNode)
        optionsLoggingNode.removeChild(optionsLoggingNode.firstChild())
        optionsLoggingNode.appendChild(newOptionsLoggingNode)
        optionsClickNLoadForwarderNode.removeChild(optionsClickNLoadForwarderNode.firstChild())
        optionsClickNLoadForwarderNode.appendChild(newOptionsClickNLoadForwarderNode)
        optionsAutomaticReloadingNode.removeChild(optionsAutomaticReloadingNode.firstChild())
        optionsAutomaticReloadingNode.appendChild(newOptionsAutomaticReloadingNode)
        optionsCaptchaNode.removeChild(optionsCaptchaNode.firstChild())
        optionsCaptchaNode.appendChild(newOptionsCaptchaNode)
        optionsFontsNode.removeChild(optionsFontsNode.firstChild())
        optionsFontsNode.appendChild(newOptionsFontsNode)
        optionsTrayNode.removeChild(optionsTrayNode.firstChild())
        optionsTrayNode.appendChild(newOptionsTrayNode)
        optionsWhatsThisNode.removeChild(optionsWhatsThisNode.firstChild())
        optionsWhatsThisNode.appendChild(newOptionsWhatsThisNode)
        optionsOtherNode.removeChild(optionsOtherNode.firstChild())
        optionsOtherNode.appendChild(newOptionsOtherNode)
        lastAddContainerDirNode.removeChild(lastAddContainerDirNode.firstChild())
        lastAddContainerDirNode.appendChild(newLastAddContainerDirNode)
        self.parser.saveData()
        self.log.debug4("main.saveOptionsToConfig: done")

    def saveWindowToConfig(self):
        """
            save window geometry and state to the config file
        """
        if self.mainWindow.isHidden():
            self.log.error("main.saveWindowToConfig: mainWindow is hidden")
        gOther = {}
        gOther["packDockIsFloating"] = self.mainWindow.newPackDock.isFloating()
        gOther["linkDockIsFloating"] = self.mainWindow.newLinkDock.isFloating()
        # undock before saveState() else the dock widget geometry does not restore correctly ...
        self.mainWindow.newPackDock.setFloating(True)
        self.mainWindow.newLinkDock.setFloating(True)
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
        gUnmax = {} # convert Qt variable types to integer, literal_eval does not accept Qt variables
        gUnmax["unmaxed_pos"] = 0 if (self.geoUnmaximized["unmaxed_pos"] is None) else [self.geoUnmaximized["unmaxed_pos"].x(),self.geoUnmaximized["unmaxed_pos"].y()]
        gUnmax["unmaxed_size"] = 0 if (self.geoUnmaximized["unmaxed_size"] is None) else [self.geoUnmaximized["unmaxed_size"].width(),self.geoUnmaximized["unmaxed_size"].height()]
        gUnmax["maximized"] = self.geoUnmaximized["maximized"]
        geoUnmaximized = str(QByteArray(str(gUnmax)).toBase64())
        # convert Qt variable types to integer, literal_eval does not accept Qt variables
        gOther["packDock"] = 0 if (self.geoOther["packDock"] is None) else [self.geoOther["packDock"].x(),self.geoOther["packDock"].y(),self.geoOther["packDock"].width(),self.geoOther["packDock"].height()]
        gOther["linkDock"] = 0 if (self.geoOther["linkDock"] is None) else [self.geoOther["linkDock"].x(),self.geoOther["linkDock"].y(),self.geoOther["linkDock"].width(),self.geoOther["linkDock"].height()]
        gOther["packDockTray"] = 0 if (self.geoOther["packDockTray"] is None) else [self.geoOther["packDockTray"].x(),self.geoOther["packDockTray"].y(),self.geoOther["packDockTray"].width(),self.geoOther["packDockTray"].height()]
        gOther["linkDockTray"] = 0 if (self.geoOther["linkDockTray"] is None) else [self.geoOther["linkDockTray"].x(),self.geoOther["linkDockTray"].y(),self.geoOther["linkDockTray"].width(),self.geoOther["linkDockTray"].height()]
        gOther["captchaDialog"] = 0 if (self.geoOther["captchaDialog"] is None) else [self.geoOther["captchaDialog"].x(),self.geoOther["captchaDialog"].y(),self.geoOther["captchaDialog"].width(),self.geoOther["captchaDialog"].height()]
        geoOther = str(QByteArray(str(gOther)).toBase64())
        stateQueue = str(self.mainWindow.tabs["queue"]["view"].header().saveState().toBase64())
        stateCollector = str(self.mainWindow.tabs["collector"]["view"].header().saveState().toBase64())
        stateAccounts = str(self.mainWindow.tabs["accounts"]["view"].header().saveState().toBase64())
        statePackageDock = str(QByteArray(str(self.mainWindow.newPackDock.getSettings())).toBase64())
        stateLinkDock = str(QByteArray(str(self.mainWindow.newLinkDock.getSettings())).toBase64())
        visibilitySpeedLimit = str(QByteArray(str(self.mainWindow.actions["speedlimit_enabled"].isVisible())).toBase64())
        language = str(self.lang)
        stateNode = mainWindowNode.toElement().elementsByTagName("state").item(0)
        geoNode = mainWindowNode.toElement().elementsByTagName("geometry").item(0)
        geoUnmaximizedNode = mainWindowNode.toElement().elementsByTagName("geometryUnmaximized").item(0)
        geoOtherNode = mainWindowNode.toElement().elementsByTagName("geometryOther").item(0)
        stateQueueNode = mainWindowNode.toElement().elementsByTagName("stateQueue").item(0)
        stateCollectorNode = mainWindowNode.toElement().elementsByTagName("stateCollector").item(0)
        stateAccountsNode = mainWindowNode.toElement().elementsByTagName("stateAccounts").item(0)
        statePackageDockNode = mainWindowNode.toElement().elementsByTagName("statePackageDock").item(0)
        stateLinkDockNode = mainWindowNode.toElement().elementsByTagName("stateLinkDock").item(0)
        visibilitySpeedLimitNode = mainWindowNode.toElement().elementsByTagName("visibilitySpeedLimit").item(0)
        languageNode = self.parser.xml.elementsByTagName("language").item(0)
        newStateNode = self.parser.xml.createTextNode(state)
        newGeoNode = self.parser.xml.createTextNode(geo)
        newGeoUnmaximizedNode = self.parser.xml.createTextNode(geoUnmaximized)
        newGeoOtherNode = self.parser.xml.createTextNode(geoOther)
        newStateQueueNode = self.parser.xml.createTextNode(stateQueue)
        newStateCollectorNode = self.parser.xml.createTextNode(stateCollector)
        newStateAccountsNode = self.parser.xml.createTextNode(stateAccounts)
        newStatePackageDockNode = self.parser.xml.createTextNode(statePackageDock)
        newStateLinkDockNode = self.parser.xml.createTextNode(stateLinkDock)
        newVisibilitySpeedLimitNode = self.parser.xml.createTextNode(visibilitySpeedLimit)
        newLanguageNode = self.parser.xml.createTextNode(language)
        stateNode.removeChild(stateNode.firstChild())
        stateNode.appendChild(newStateNode)
        geoNode.removeChild(geoNode.firstChild())
        geoNode.appendChild(newGeoNode)
        geoUnmaximizedNode.removeChild(geoUnmaximizedNode.firstChild())
        geoUnmaximizedNode.appendChild(newGeoUnmaximizedNode)
        geoOtherNode.removeChild(geoOtherNode.firstChild())
        geoOtherNode.appendChild(newGeoOtherNode)
        stateQueueNode.removeChild(stateQueueNode.firstChild())
        stateQueueNode.appendChild(newStateQueueNode)
        stateCollectorNode.removeChild(stateCollectorNode.firstChild())
        stateCollectorNode.appendChild(newStateCollectorNode)
        stateAccountsNode.removeChild(stateAccountsNode.firstChild())
        stateAccountsNode.appendChild(newStateAccountsNode)
        statePackageDockNode.removeChild(statePackageDockNode.firstChild())
        statePackageDockNode.appendChild(newStatePackageDockNode)
        stateLinkDockNode.removeChild(stateLinkDockNode.firstChild())
        stateLinkDockNode.appendChild(newStateLinkDockNode)
        visibilitySpeedLimitNode.removeChild(visibilitySpeedLimitNode.firstChild())
        visibilitySpeedLimitNode.appendChild(newVisibilitySpeedLimitNode)
        languageNode.removeChild(languageNode.firstChild())
        languageNode.appendChild(newLanguageNode)
        self.parser.saveData()
        self.log.debug4("main.saveWindowToConfig: done")

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
        if not nodes.get("optionsWhatsThis"):
            mainWindowNode.appendChild(self.parser.xml.createElement("optionsWhatsThis"))
        if not nodes.get("optionsOther"):
            mainWindowNode.appendChild(self.parser.xml.createElement("optionsOther"))
        if not nodes.get("lastAddContainerDir"):
            mainWindowNode.appendChild(self.parser.xml.createElement("lastAddContainerDir"))
        nodes = self.parser.parseNode(mainWindowNode, "dict")   # reparse with the new nodes (if any)

        if self.newConfigFile:
            self.saveOptionsToConfig()
            self.newConfigFile = False
            return

        optionsNotifications = str(nodes["optionsNotifications"].text())
        optionsLogging = str(nodes["optionsLogging"].text())
        optionsClickNLoadForwarder = str(nodes["optionsClickNLoadForwarder"].text())
        optionsAutomaticReloading = str(nodes["optionsAutomaticReloading"].text())
        optionsCaptcha = str(nodes["optionsCaptcha"].text())
        optionsFonts = str(nodes["optionsFonts"].text())
        optionsTray = str(nodes["optionsTray"].text())
        optionsWhatsThis = str(nodes["optionsWhatsThis"].text())
        optionsOther = str(nodes["optionsOther"].text())
        lastAddContainerDir = unicode(nodes["lastAddContainerDir"].text())
        reset = False

        def base64ToDict(b64):
            try:
                d = literal_eval(str(QByteArray.fromBase64(b64)))
            except Exception:
                d = None
            if d and not isinstance(d, dict):
                d = None
            return d

        # Desktop Notifications
        d = base64ToDict(optionsNotifications)
        if d is not None:
            try:              self.notificationOptions.settings = d; self.notificationOptions.dict2checkBoxStates()
            except Exception: self.notificationOptions.defaultSettings(); d = None
        if d is None: self.messageBox_21(_("Desktop Notifications")); reset = True
        # Client Log
        d = base64ToDict(optionsLogging)
        if d is not None:
            try:              self.loggingOptions.settings = d; self.loggingOptions.dict2dialogState()
            except Exception: self.loggingOptions.defaultSettings(); d = None
        if d is None: self.messageBox_21(_("Client Log")); reset = True
        # ClickNLoad Forwarding -> Local Port
        err = False
        try:              self.clickNLoadForwarderOptions.settings["fromPort"] = int(optionsClickNLoadForwarder); self.clickNLoadForwarderOptions.dict2dialogState(True)
        except Exception: self.clickNLoadForwarderOptions.defaultFromPort(); err = True
        if err: self.messageBox_21(_("ClickNLoad Forwarding") + " -> " + _("Local Port")); reset = True
        # Automatic Reloading
        d = base64ToDict(optionsAutomaticReloading)
        if d is not None:
            try:              self.automaticReloadingOptions.settings = d; self.automaticReloadingOptions.dict2dialogState()
            except Exception: self.automaticReloadingOptions.defaultSettings(); d = None
        if d is None: self.messageBox_21(_("Automatic Reloading")); reset = True
        # Captchas
        d = base64ToDict(optionsCaptcha)
        if d is not None:
            try:              self.captchaOptions.settings = d; self.captchaOptions.dict2dialogState()
            except Exception: self.captchaOptions.defaultSettings(); d = None
        if d is None: self.messageBox_21(_("Captchas")); reset = True
        self.mainWindow.captchaDialog.adjSize = self.captchaOptions.settings["AdjSize"]
        # Fonts
        d = base64ToDict(optionsFonts)
        if d is not None:
            try:              self.fontOptions.settings = d; self.fontOptions.dict2dialogState()
            except Exception: self.fontOptions.defaultSettings(); d = None
        if d is None: self.messageBox_21(_("Fonts")); reset = True
        self.fontOptions.applySettings()
        # Tray Icon
        d = base64ToDict(optionsTray)
        if d is not None:
            try:              self.trayOptions.settings = d; self.trayOptions.dict2checkBoxStates()
            except Exception: self.trayOptions.defaultSettings(); d = None
        if d is None: self.messageBox_21(_("Tray Icon")); reset = True
        # What's This
        d = base64ToDict(optionsWhatsThis)
        if d is not None:
            try:              self.whatsThisOptions.settings = d; self.whatsThisOptions.dict2dialogState()
            except Exception: self.whatsThisOptions.defaultSettings(); d = None
        if d is None: self.messageBox_21(_("What's This")); reset = True
        self.whatsThisOptions.applySettings()
        self.whatsThisOptions.choosenColors = None
        # Other
        d = base64ToDict(optionsOther)
        if d is not None:
            try:              self.otherOptions.settings = d; self.otherOptions.dict2checkBoxStates()
            except Exception: self.otherOptions.defaultSettings(); d = None
        if d is None: self.messageBox_21(_("Other")); reset = True
        # Last folder from where a container file has been loaded
        self.mainWindow.lastAddContainerDir = lastAddContainerDir
        if reset:
            self.saveOptionsToConfig()

    def messageBox_21(self, optCat):
        text = _("The following options had to be reset:") + "\n" + optCat
        self.msgBoxOk(text, "W")

    def loadWindowFromConfig(self):
        """
            load window geometry and state from the config file
            and show main window and docks
        """
        mainWindowNode = self.parser.xml.elementsByTagName("mainWindow").item(0)
        if mainWindowNode.isNull():
            return
        nodes = self.parser.parseNode(mainWindowNode, "dict")
        if not nodes.get("geometryUnmaximized"):
            mainWindowNode.appendChild(self.parser.xml.createElement("geometryUnmaximized"))
        if not nodes.get("stateQueue"):
            mainWindowNode.appendChild(self.parser.xml.createElement("stateQueue"))
        if not nodes.get("stateCollector"):
            mainWindowNode.appendChild(self.parser.xml.createElement("stateCollector"))
        if not nodes.get("stateAccounts"):
            mainWindowNode.appendChild(self.parser.xml.createElement("stateAccounts"))
        if not nodes.get("statePackageDock"):
            mainWindowNode.appendChild(self.parser.xml.createElement("statePackageDock"))
        if not nodes.get("stateLinkDock"):
            mainWindowNode.appendChild(self.parser.xml.createElement("stateLinkDock"))
        if not nodes.get("visibilitySpeedLimit"):
            mainWindowNode.appendChild(self.parser.xml.createElement("visibilitySpeedLimit"))
        if not nodes.get("geometryOther"):
            mainWindowNode.appendChild(self.parser.xml.createElement("geometryOther"))
        nodes = self.parser.parseNode(mainWindowNode, "dict")   # reparse with the new nodes (if any)

        state = str(nodes["state"].text())
        geo = str(nodes["geometry"].text())
        geoUnmaxed = str(nodes["geometryUnmaximized"].text())
        geoOther = str(nodes["geometryOther"].text())
        stateQueue = str(nodes["stateQueue"].text())
        stateCollector = str(nodes["stateCollector"].text())
        stateAccounts = str(nodes["stateAccounts"].text())
        statePackageDockBase64 = str(nodes["statePackageDock"].text())
        stateLinkDockBase64 = str(nodes["stateLinkDock"].text())
        visibilitySpeedLimit = str(nodes["visibilitySpeedLimit"].text())

        # mainWindow restoreState
        self.mainWindow.eD["pCount"] = 0
        self.mainWindow.show()
        self.waitForPaintEvents(1)
        self.log.debug4("main.loadWindowFromConfig: first show() done")
        self.mainWindow.eD["pCount"] = 0
        self.mainWindow.restoreState(QByteArray.fromBase64(state), self.mainWindow.version)   # also restores floating state of docks
        self.waitForPaintEvents(1)
        self.app.processEvents()   # needed on deepin
        self.log.debug4("main.loadWindowFromConfig: restoreState() done")

        gUnmaxError = False
        try: gUnmax = literal_eval(str(QByteArray.fromBase64(geoUnmaxed)))
        except Exception: gUnmaxError = True
        if not gUnmaxError:
            if not isinstance(gUnmax, dict):
                gUnmaxError = True
            elif not (("unmaxed_pos" in gUnmax) and ("unmaxed_size" in gUnmax) and ("maximized" in gUnmax)):
                gUnmaxError = True
        if gUnmaxError:
            gUnmax = {}; gUnmax["unmaxed_pos"] = gUnmax["unmaxed_size"] = 0 ; gUnmax["maximized"] = False
        self.geoUnmaximized = {}
        self.geoUnmaximized["unmaxed_pos"] = None if (gUnmax["unmaxed_pos"] == 0) else QPoint(gUnmax["unmaxed_pos"][0], gUnmax["unmaxed_pos"][1])
        self.geoUnmaximized["unmaxed_size"] = None if (gUnmax["unmaxed_size"] == 0) else QSize(gUnmax["unmaxed_size"][0], gUnmax["unmaxed_size"][1])
        self.geoUnmaximized["maximized"] = gUnmax["maximized"]

        gOtherError = False
        try: gOther = literal_eval(str(QByteArray.fromBase64(geoOther)))
        except Exception: gOtherError = True
        if not gOtherError:
            if not isinstance(gOther, dict):
                gOtherError = True
            elif not (("packDockIsFloating" in gOther) and ("linkDockIsFloating" in gOther) and ("packDock" in gOther) and
                      ("linkDock" in gOther) and ("packDockTray" in gOther) and ("linkDockTray" in gOther) and ("captchaDialog" in gOther)):
                gOtherError = True
        if gOtherError:
            gOther = {}; gOther["packDockIsFloating"] = gOther["linkDockIsFloating"] = False
            gOther["packDock"] = gOther["linkDock"] = gOther["packDockTray"] = gOther["linkDockTray"] = gOther["captchaDialog"] = 0
        self.geoOther["packDock"] = None if (gOther["packDock"] == 0) else QRect(gOther["packDock"][0], gOther["packDock"][1], gOther["packDock"][2], gOther["packDock"][3])
        self.geoOther["linkDock"] = None if (gOther["linkDock"] == 0) else QRect(gOther["linkDock"][0], gOther["linkDock"][1], gOther["linkDock"][2], gOther["linkDock"][3])
        self.geoOther["packDockTray"] = None if (gOther["packDockTray"] == 0) else QRect(gOther["packDockTray"][0], gOther["packDockTray"][1], gOther["packDockTray"][2], gOther["packDockTray"][3])
        self.geoOther["linkDockTray"] = None if (gOther["linkDockTray"] == 0) else QRect(gOther["linkDockTray"][0], gOther["linkDockTray"][1], gOther["linkDockTray"][2], gOther["linkDockTray"][3])
        self.geoOther["captchaDialog"] = None if (gOther["captchaDialog"] == 0) else QRect(gOther["captchaDialog"][0], gOther["captchaDialog"][1], gOther["captchaDialog"][2], gOther["captchaDialog"][3])

        if not self.geoUnmaximized["maximized"]:
            self.mainWindow.restoreGeometry(QByteArray.fromBase64(geo))
            self.mainWindow.newPackDock.setFloating(False)   # needed on enlightenment
            self.mainWindow.newLinkDock.setFloating(False)   # needed on enlightenment
            self.mainWindow.newPackDock.setFloating(gOther["packDockIsFloating"])
            self.mainWindow.newLinkDock.setFloating(gOther["linkDockIsFloating"])
            pdGeo = self.geoOther["packDock"]
            if not self.mainWindow.newPackDock.isFloating() or self.mainWindow.newPackDock.isHidden():
                pdGeo = None
            plGeo = self.geoOther["linkDock"]
            if not self.mainWindow.newLinkDock.isFloating() or self.mainWindow.newLinkDock.isHidden():
                plGeo = None
            self.scheduleMainWindowPaintEventAction(pos=self.mainWindow.pos(), size=self.mainWindow.size(), refreshGeo=self.otherOptions.settings["RefreshGeo"], pdGeo=pdGeo, plGeo=plGeo)
        else:
            self.mainWindow.eD["pCount"] = 0
            self.mainWindow.showMaximized()
            self.waitForPaintEvents(1)
            self.mainWindow.newPackDock.setFloating(False)   # needed on enlightenment
            self.mainWindow.newLinkDock.setFloating(False)   # needed on enlightenment
            if self.otherOptions.settings["RestoreUnmaximizedGeo"] and self.otherOptions.settings["HideShowOnStart"]:
                self.log.debug4("main.loadWindowFromConfig: Option '%s' done, showMaximized()" % str(self.otherOptions.cbHideShowOnStart.text()))
                self.mainWindow.hide()
                self.app.processEvents()
                self.mainWindow.eD["pCount"] = 0
                self.mainWindow.show()
                self.waitForPaintEvents(1)
                self.log.debug4("main.loadWindowFromConfig: Option '%s' done, show() after hide()" % str(self.otherOptions.cbHideShowOnStart.text()))
                self.app.processEvents()
            self.mainWindow.eD["pCount"] = 0
            self.mainWindow.newPackDock.setFloating(gOther["packDockIsFloating"])
            self.mainWindow.newLinkDock.setFloating(gOther["linkDockIsFloating"])
            if (self.mainWindow.newPackDock.isFloating() and not self.mainWindow.newPackDock.isHidden()) or (self.mainWindow.newLinkDock.isFloating() and not self.mainWindow.newLinkDock.isHidden()):
                self.waitForPaintEvents(1)
            self.scheduleMainWindowPaintEventAction()

        self.app.processEvents()   # needed on enlightenment
        self.mainWindow.eD["pStateSig"] = self.geoUnmaximized["maximized"]
        self.mainWindow.eD["pCount"] = 0   # for self.mainWindow.newPackDock.raise_() below
        self.mainWindow.tabifyDockWidget(self.mainWindow.newPackDock, self.mainWindow.newLinkDock)

        # tabs restoreState
        self.mainWindow.tabs["queue"]["view"].header().restoreState(QByteArray.fromBase64(stateQueue))
        self.mainWindow.tabs["collector"]["view"].header().restoreState(QByteArray.fromBase64(stateCollector))
        self.mainWindow.tabs["accounts"]["view"].header().restoreState(QByteArray.fromBase64(stateAccounts))

        # docks, buttons and checkboxes for selecting queue/collector
        def base64ToDict(b64):
            try:
                d = literal_eval(str(QByteArray.fromBase64(b64)))
            except Exception:
                d = None
            if d and not isinstance(d, dict):
                d = None
            return d
        if statePackageDockBase64:
            d = base64ToDict(statePackageDockBase64)
            if d is not None:
                try:              self.mainWindow.newPackDock.setSettings(d)
                except Exception: self.mainWindow.newPackDock.defaultSettings()
        if stateLinkDockBase64:
            d = base64ToDict(stateLinkDockBase64)
            if d is not None:
                try:              self.mainWindow.newLinkDock.setSettings(d)
                except Exception: self.mainWindow.newLinkDock.defaultSettings()

        if visibilitySpeedLimit:
            visSpeed = literal_eval(str(QByteArray.fromBase64(visibilitySpeedLimit)))
        else:
            visSpeed = True
        self.mainWindow.mactions["showspeedlimit"].setChecked(not visSpeed)
        self.mainWindow.mactions["showspeedlimit"].setChecked(visSpeed)
        self.mainWindow.captchaDialog.geo = self.geoOther["captchaDialog"]
        self.fixFirstShowFromTrayWhenLoadedMaximized = self.geoUnmaximized["maximized"]

        if not (self.mainWindow.newPackDock.isFloating() or self.mainWindow.newPackDock.isHidden()):
            self.waitForPaintEvents(1)
            self.mainWindow.newPackDock.raise_()   # activate tab

    def slotMainWindowState(self):
        """
            catch the main window state right before the first unmaximize when the app was lauched maximized,
            this is to restore the docked widgets width (divider position)
            emitted from main window in paintEvent() (queued signal)
        """
        if self.mainWindow.isMaximized() and bool(self.mainWindow.windowState() & Qt.WindowMaximized):
            state = self.mainWindow.saveState(self.mainWindow.version)
            size = self.mainWindow.size()
            if self.mainWindowMaximizedSize is None:
                valid = True
            elif size.width() >= self.mainWindowMaximizedSize.width() and size.height() >= self.mainWindowMaximizedSize.height():
                valid = True
            else:
                valid = False
            if valid:
                self.mainWindowStateFirstUnmax = state
                self.mainWindowMaximizedSize = size

    def scheduleMainWindowPaintEventAction(self, pos=None, size=None, raise_=True, activate=True, focus=True, showFromTrayContinue=0, refreshGeo=False, pdGeo=None, plGeo=None, restoreDocks=False):
        """
            schedule an action on a main window paintEvent
            pos is of type QPoint and size of type QSize
            called from:
              self.loadWindowFromConfig()
              self.showFromTray()
              self.slotMaximizeToggled()
        """
        if self.mainWindow.eD["pSignal"]:
            self.log.error("main.scheduleMainWindowPaintEventAction: last action not queued yet")
            return
        if self.log.isEnabledFor(logging.DEBUG4):
            p = pos
            if p is not None:
                p = "(%s, %s)" % (pos.x(), pos.y())
            s = size
            if s is not None:
                s = "(%s, %s)" % (s.width(), s.height())
            self.log.debug4("main.scheduleMainWindowPaintEventAction: pos:%s  size:%s  raise:%s  act:%s  foc:%s  cont:%s  refreshGeo:%s  pdGeo:%s  plGeo:%s  restoreDocks:%s" % (p, s, raise_, activate, focus, showFromTrayContinue, refreshGeo, pdGeo, plGeo, restoreDocks))
        a = self.mainWindowPaintEventAction
        a["pos"]                  = pos
        a["size"]                 = size
        a["raise_"]               = raise_
        a["activate"]             = activate
        a["focus"]                = focus
        a["showFromTrayContinue"] = showFromTrayContinue
        a["refreshGeo"]           = refreshGeo
        a["pdGeo"]                = pdGeo
        a["plGeo"]                = plGeo
        a["restoreDocks"]         = restoreDocks
        # try set geometry right now to possibly avoid flicker with some window managers
        if size is not None:
            self.mainWindow.resize(size)
        if pos is not None:
            self.mainWindow.move(pos.x() + 1, pos.y() + 1)  # needed on LXDE
            self.mainWindow.move(pos)
        self.mainWindow.eD["pSignal"] = True

    def slotMainWindowPaintEvent(self):
        """
            do the scheduled action
            emitted from main window in paintEvent()
        """
        dm = self.log.isEnabledFor(logging.DEBUG4)
        actmsg = []
        a = self.mainWindowPaintEventAction
        if a["size"] is not None:
            self.mainWindow.resize(a["size"])
            if dm: actmsg.append("resized (%d, %d)" % (a["size"].width(), a["size"].height()))
        if a["pos"] is not None:
            self.mainWindow.move(a["pos"])
            if dm: actmsg.append("moved (%d, %d)" % (a["pos"].x(), a["pos"].y()))
        if a["refreshGeo"]: # fix for lxde, read the geometry and set it again
            g = self.mainWindow.geometry()
            self.mainWindow.setGeometry(g)
            if dm: actmsg.append("refreshGeo")
        if a["pdGeo"] is not None:
            self.mainWindow.newPackDock.setGeometry(a["pdGeo"])
            if dm: actmsg.append("pdGeo")
        if a["plGeo"] is not None:
            self.mainWindow.newLinkDock.setGeometry(a["plGeo"])
            if dm: actmsg.append("plGeo")
        if a["raise_"]:
            self.mainWindow.raise_()
            if dm: actmsg.append("raised")
        if a["focus"]:
            self.mainWindow.tabw.setFocus(Qt.OtherFocusReason)
            if dm: actmsg.append("focused")
        if a["activate"]:
            self.mainWindow.activateWindow()
            # fire an extra fusillade for slow window managers
            for i in [10, 50, 100, 200]:
                QTimer.singleShot(i, self.mainWindow.activateWindow)
            if dm: actmsg.append("activated")
        if a["restoreDocks"]:
            QTimer.singleShot(300, self.slotRestoreDocks)
            if dm: actmsg.append("restoreDocks")
        if len(actmsg) > 0:
            am = "main.slotMainWindowPaintEvent: "
            for i, msg in enumerate(actmsg):
                if i > 0: am += ", "
                am += msg
            self.log.debug4(am)
        if a["showFromTrayContinue"] > 0:
            a["showFromTrayContinue"] -= 1
            if a["showFromTrayContinue"] == 0:
                self.showFromTray_continue()
            else:
                # rescheduling here is OK, since no more actions can be scheduled from any part of the code until showFromTray_continue() has finished
                a["pos"] = a["size"] = None
                a["raise_"] = a["activate"] = a["focus"] = False
                self.mainWindow.eD["pSignal"] = True

    def slotPushPackagesToQueue(self):
        """
            emitted from main window
            push the collector packages to queue
        """
        if not self.corePermissions["MODIFY"]:
            return
        selection = self.collector.getSelection(True, True)
        for s in selection:
            (pid, dummy, isPack) = s
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

    def slotSelectAll(self):
        """
            emitted from main window
            select all items
        """
        if self.mainWindow.activeMenu == self.mainWindow.queueContext:
            self.queue.selectAll(False)
        else:
            self.collector.selectAll(False)

    def slotDeselectAll(self):
        """
            emitted from main window
            deselect all item
        """
        if self.mainWindow.activeMenu == self.mainWindow.queueContext:
            self.queue.selectAll(True)
        else:
            self.collector.selectAll(True)

    def slotSelectAllPackages(self):
        """
            emitted from main window
            select all packages
        """
        if self.mainWindow.activeMenu == self.mainWindow.queueContext:
            self.queue.selectAllPackages(False)
        else:
            self.collector.selectAllPackages(False)

    def slotDeselectAllPackages(self):
        """
            emitted from main window
            deselect all packages
        """
        if self.mainWindow.activeMenu == self.mainWindow.queueContext:
            self.queue.selectAllPackages(True)
        else:
            self.collector.selectAllPackages(True)

    def slotAdvancedSelect(self, deselect):
        """
            emitted from main window
            advanced link/package select
        """
        pattern = self.mainWindow.advselect.patternEdit.currentText()
        if not pattern.isEmpty():
            self.mainWindow.advselect.setEnabled(False)
            mode = self.mainWindow.advselect.modeCmb.currentIndex()
            matchCase = self.mainWindow.advselect.caseCb.isChecked()
            selectLinks = self.mainWindow.advselect.linksCb.isChecked()
            if mode == self.mainWindow.advselect.modeIdx.STRING:
                syntax = QRegExp.FixedString
            elif mode == self.mainWindow.advselect.modeIdx.WILDCARD:
                syntax = QRegExp.Wildcard
            elif mode == self.mainWindow.advselect.modeIdx.REGEXP:
                syntax = QRegExp.RegExp2
            else:
                self.log.error("main.slotAdvancedSelect: Invalid mode")
                return
            cs = Qt.CaseSensitive if matchCase == True else Qt.CaseInsensitive
            if self.mainWindow.tabw.currentIndex() == 1:
                self.queue.advancedSelect(pattern, syntax, cs, deselect, selectLinks)
            else:
                self.collector.advancedSelect(pattern, syntax, cs, deselect, selectLinks)
            QTimer.singleShot(300, self.mainWindow.advselect.slotEnable)

    def slotRemoveLinkDupes(self):
        """
            emitted from main window
            remove duplicate links
        """
        if self.mainWindow.tabw.currentIndex() == 1:
            self.mainWindow.tabs["queue"]["view"].setEnabled(False)
            QTimer.singleShot(300, self.queue.removeLinkDupes)
        else:
            self.mainWindow.tabs["collector"]["view"].setEnabled(False)
            QTimer.singleShot(300, self.collector.removeLinkDupes)

    def slotSortPackages(self):
        """
            emitted from main window
            sort packages
        """
        if self.mainWindow.tabw.currentIndex() == 1:
            self.mainWindow.tabs["queue"]["view"].setEnabled(False)
            QTimer.singleShot(300, self.queue.sortPackages)
        else:
            self.mainWindow.tabs["collector"]["view"].setEnabled(False)
            QTimer.singleShot(300, self.collector.sortPackages)

    def slotSortLinks(self):
        """
            emitted from main window
            sort packages
        """
        if self.mainWindow.tabw.currentIndex() == 1:
            self.mainWindow.tabs["queue"]["view"].setEnabled(False)
            QTimer.singleShot(300, self.queue.sortLinks)
        else:
            self.mainWindow.tabs["collector"]["view"].setEnabled(False)
            QTimer.singleShot(300, self.collector.sortLinks)

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
        mode_queue     = self.mainWindow.actions["clipboard_queue"].isChecked()
        mode_collector = self.mainWindow.actions["clipboard_collector"].isChecked()
        mode_packDock  = self.mainWindow.actions["clipboard_packDock"].isChecked()
        if mode_queue or mode_collector or mode_packDock:
            text = unicode(self.clipboard.text())
            links = self.mainWindow.urlFilter(text)
            if len(links) == 0:
                return
            filenames = [link.rpartition("/")[2] for link in links]
            packagename = commonprefix(filenames)
            if len(packagename) == 0:
                packagename = filenames[0]
            if mode_queue:
                self.slotAddPackage(packagename, links, True)
            elif mode_collector:
                self.slotAddPackage(packagename, links, False)
            else:
                self.mainWindow.newPackDock.appendClipboardLinks(links)

    def slotPullOutPackages(self):
        """
            emitted from main window
            pull the packages out of the queue
        """
        if not self.corePermissions["MODIFY"]:
            return
        selection = self.queue.getSelection(True, True)
        for s in selection:
            (pid, dummy, isPack) = s
            if isPack:
                self.connector.proxy.pullFromQueue(pid)

    def checkCaptcha(self):
        """
            called from main loop
            poll for captcha requests
        """
        if not (self.corePermissions["STATUS"] and self.captchaOptions.settings["Accept"]):
            return
        if self.connector.proxy.isCaptchaWaiting():
            t = self.connector.proxy.getCaptchaTask(False)
            if t.tid != self.lastCaptchaId:
                self.lastCaptchaId = t.tid
                if not self.mainWindow.captchaDialog.isFree():
                    self.mainWindow.captchaDialog.emit(SIGNAL("setFree"))
                if t.resultType == "interactive":
                    self.slotNotificationMessage(102, None)
                    if self.captchaOptions.settings["PopUpCaptchaInteractive"]:
                        self.mainWindow.captchaDialog.emit(SIGNAL("show"), False)
                    self.tray.captchaAction.setEnabled(False)
                    self.mainWindow.toolbar_captcha.setText(_("Interactive Captcha"))
                    self.mainWindow.actions["captcha"].setVisible(True)
                else:
                    self.slotNotificationMessage(101, None)
                    self.mainWindow.captchaDialog.emit(SIGNAL("setTask"), t.tid, json.loads(t.data), t.type, t.resultType)
                    if self.captchaOptions.settings["PopUpCaptcha"]:
                        self.mainWindow.captchaDialog.emit(SIGNAL("show"), False)
                    self.tray.captchaAction.setEnabled(True)
                    self.mainWindow.toolbar_captcha.setText(_("Captcha"))
                    self.mainWindow.actions["captcha"].setVisible(True)
        else:
            if self.lastCaptchaId is not None:
                self.mainWindow.captchaDialog.emit(SIGNAL("setFree"))
            self.lastCaptchaId = None
            self.tray.captchaAction.setEnabled(False)
            self.mainWindow.toolbar_captcha.setText("NO CAPTCHA")
            self.mainWindow.actions["captcha"].setVisible(False)

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
            retval = self.packageEdit.exec_()
            if retval == self.packageEdit.CANCELALL:
                break

    def slotEditPackageSave(self):
        """
            apply changes made in the package edit dialog (save button hit)
        """
        name = unicode(self.packageEdit.name.text())
        folder = unicode(self.packageEdit.folder.text())
        password = unicode(self.packageEdit.password.toPlainText())
        try: # keep the dialog open if something goes wrong
            if name == self.packageEdit.old_name:
                name = None
            if folder == self.packageEdit.old_folder:
                folder = None
            if password == self.packageEdit.old_password:
                password = None
            self.changePackageData(self.packageEdit.id, name, folder, password)
            self.packageEdit.close()
        except Exception:
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
        text  = _("The package to edit does not exist anymore.")
        text += "\n" + _("Package") + " " + _("ID") + ": %d" % int(pid)
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

    def slotMainWindowClose(self):
        """
            emitted from main window closeEvent()
        """
        # quit when the option to minimize is disabled
        if not (self.trayOptions.settings["EnableTray"] and self.trayOptions.settings["Close2Tray"]):
            QTimer.singleShot(0, self.slotQuit)
        # quit when there is no system tray is available
        elif not QSystemTrayIcon.isSystemTrayAvailable():
            QTimer.singleShot(0, self.slotQuit)
        # hide in tray
        elif self.trayOptions.settings["EnableTray"] and (self.tray is not None):
            QTimer.singleShot(0, self.hideInTray)

    def slotQuit(self):
        self.allowUserActions(False)
        self.prepareForSaveOptionsAndWindow(self.slotQuit_continue)

    def slotQuit_continue(self):
        self.saveWindowToConfig()
        self.saveOptionsToConfig()
        self.quitInternal()
        self.log.info("pyLoad Client quit")
        try:
            self.tray.deleteLater()
        except Exception:
            self.log.debug4("main.slotQuit_continue: tray was already deleted by the garbage collector")
        self.removeLogger()
        self.app.quit()

    def slotQuitConnWindow(self):
        self.connWindow = None # odd fix for python/pyqt crash on windows 7 when exiting the application
        self.log.info("pyLoad Client quit")
        self.removeLogger()
        self.app.quit()

    def quitConnTimeout(self):
        self.log.error("Connecting to the pyLoad server is taking an unusually long time")
        self.log.info("Terminating pyLoad Client")
        self.setExcepthook(False)
        self.removeLogger()
        pid = os.getpid()
        os.kill(pid, 9)
        if os.name == "nt":
            self.win_os_kill(pid)   # in case that the above failed on windows os
        sleep(3)
        print ("Error: Failed to terminate the pyLoad Client process")

    @classmethod
    def win_os_kill(self, pid):
        handle = ctypes.windll.kernel32.OpenProcess(1, 0, pid)
        ctypes.windll.kernel32.TerminateProcess(handle, 0)

    def quitInternal(self):
        if self.core:
            self.core.api.kill()
            timeout = 30    # seconds
            popup   = 3     # seconds, progess dialog pop up delay
            p = QProgressDialog("", "", 0, timeout * 10, self.mainWindow)
            p.setCancelButton(None)
            p.setWindowFlags(p.windowFlags() & ~Qt.WindowContextHelpButtonHint)
            p.setWindowModality(Qt.ApplicationModal)
            p.setWindowTitle(_("Shutting down the internal server"))
            p.setWindowIcon(QIcon(join(pypath, "icons", "logo.png")))
            p.setMinimumWidth(400)
            p.setAutoReset(False)
            p.setAutoClose(True)
            p.setValue(0)
            for i in range(timeout * 2):
                if self.core.shuttedDown:
                    p.reset()
                    return
                sleep(0.5)
                if i >= (popup * 2):
                    p.setValue(i * 10 / 2 + 5)
                    self.app.processEvents()
            p.reset()
            self.log.error("Timeout while shutting down the internal server")

    def slotConnectionLost(self):
        if not self.connectionLost:
            self.connectionLost = True
            error = False
            try:
                self.quitInternal()
                self.stopMain()
            except Exception:
                error = True
            if not error:
                return
            self.log.error("main.slotConnectionLost: Unexpected error while trying to connect to the server.")
            self.log.error("                         If this happens again and this is your default connection,")
            self.log.error("                         use command line argument '-c' with a nonexistent connection-name")
            self.log.error("                         to get in the Connection Manager, e.g. 'pyLoadGui.py -c foobar'.")
            self.log.info("pyLoad Client quit")
            self.removeLogger()
            exit()

    class Loop(object):
        def __init__(self, parent):
            self.log = logging.getLogger("guilog")
            self.parent = parent

            self.timer = QTimer()
            self.timer.connect(self.timer, SIGNAL("timeout()"), self.update)
            self.lastSpaceCheck = 0

        def start(self):
            self.update(True)
            self.timer.start(1000)

        def update(self, first=False):
            """
                methods to call
            """
            if self.parent.connectionLost:
                self.stop()
                return

            self.parent.refreshServerStatus()
            if self.lastSpaceCheck + 5 < time():
                self.lastSpaceCheck = time()
                if self.parent.corePermissions["STATUS"]:
                    self.parent.serverStatus["freespace"] = self.parent.connector.proxy.freeSpace()
            self.parent.refreshGuiLog()
            self.parent.refreshCoreLog(first)
            self.parent.checkCaptcha()

            # check dirty data model flags at regular intervals
            self.parent.queue.fullReloadOnDirty()
            self.parent.collector.fullReloadOnDirty()

            self.parent.pullEvents()
            if self.parent.automaticReloadingOptions.settings["enabled"]:
                interval = float(self.parent.automaticReloadingOptions.settings["interval"]) - 0.5
                self.parent.queue.automaticReloading(interval)
                self.parent.collector.automaticReloading(interval)
            self.parent.updateToolbarSpeedLimitFromCore(first)

        def stop(self):
            self.timer.stop()

    def slotShowLoggingOptions(self):
        """
            popup the logging options dialog
        """
        self.loggingOptions.dict2dialogState()
        oldsettings = self.loggingOptions.settings.copy()
        retval = self.loggingOptions.exec_()
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

    def slotShowNotificationOptions(self):
        """
            popup the notification options dialog
        """
        self.notificationOptions.dict2checkBoxStates()
        retval = self.notificationOptions.exec_()
        if retval == QDialog.Accepted:
            self.notificationOptions.checkBoxStates2dict()

    def slotShowOtherOptions(self):
        """
            popup the other options dialog
        """
        self.otherOptions.dict2checkBoxStates()
        retval = self.otherOptions.exec_()
        if retval == QDialog.Accepted:
            self.otherOptions.checkBoxStates2dict()

    def slotShowTrayOptions(self):
        """
            popup the tray options dialog
        """
        self.trayOptions.dict2checkBoxStates()
        retval = self.trayOptions.exec_()
        if retval == QDialog.Accepted:
            self.trayOptions.checkBoxStates2dict()
            if self.trayOptions.settings["EnableTray"]:
                self.emit(SIGNAL("showTrayIcon"))
            else:
                self.emit(SIGNAL("hideTrayIcon"))
            self.emit(SIGNAL("setupIcon"), self.trayOptions.settings["IconFile"])

    def slotShowClickNLoadForwarderOptions(self):
        """
            popup the ClickNLoad port forwarder options dialog
        """
        self.clickNLoadForwarderOptions.settings["enabled"] = self.clickNLoadForwarder.running
        self.clickNLoadForwarderOptions.dict2dialogState(self.clickNLoadForwarder.error)
        retval = self.clickNLoadForwarderOptions.exec_()
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
        retval = self.automaticReloadingOptions.exec_()
        if retval == QDialog.Accepted:
            self.automaticReloadingOptions.dialogState2dict()

    def slotShowCaptchaOptions(self):
        """
            popup the captcha options dialog
        """
        self.captchaOptions.dict2dialogState()
        retval = self.captchaOptions.exec_()
        if retval == QDialog.Accepted:
            self.captchaOptions.dialogState2dict()
            if not self.captchaOptions.settings["Accept"]:
                self.mainWindow.toolbar_captcha.setText("DISABLED")
                self.mainWindow.actions["captcha"].setVisible(False)
                self.mainWindow.captchaDialog.emit(SIGNAL("setFree"))
                self.tray.captchaAction.setEnabled(False)
            self.mainWindow.captchaDialog.adjSize = self.captchaOptions.settings["AdjSize"]

    def slotShowFontOptions(self):
        """
            popup the font options dialog
        """
        self.fontOptions.dict2dialogState()
        oldsettings = copy.deepcopy(self.fontOptions.settings)
        retval = self.fontOptions.exec_()
        if retval == QDialog.Accepted:
            self.fontOptions.dialogState2dict()
            if self.fontOptions.settings != oldsettings:
                self.fontOptions.applySettings()
        else:
            self.fontOptions.settings = copy.deepcopy(oldsettings)

    def slotAppFontChanged(self):
        """
            the application font changed
        """
        self.mainWindow.advselect.appFontChanged()
        self.captchaOptions.appFontChanged()
        self.loggingOptions.appFontChanged()
        self.fontOptions.appFontChanged()
        self.whatsThisOptions.appFontChanged()
        self.automaticReloadingOptions.appFontChanged()
        self.clickNLoadForwarderOptions.appFontChanged()
        self.languageOptions.appFontChanged()
        self.packageEdit.appFontChanged()
        self.notificationOptions.appFontChanged()
        self.trayOptions.appFontChanged()
        self.otherOptions.appFontChanged()
        self.mainWindow.captchaDialog.appFontChanged()
        self.connWindow.appFontChanged()
        self.connector.pwBox.appFontChanged()

    def slotShowWhatsThisOptions(self):
        """
            popup the whatsthis options dialog
        """
        self.whatsThisOptions.dict2dialogState()
        retval = self.whatsThisOptions.exec_()
        if retval == QDialog.Accepted:
            self.whatsThisOptions.dialogState2dict()
            self.whatsThisOptions.applySettings()

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
        retval = self.languageOptions.exec_()
        if retval == QDialog.Accepted:
            self.languageOptions.dialogState2dict()
            if self.languageOptions.settings["language"] != self.lang:
                self.lang = self.languageOptions.settings["language"]

    def updateToolbarSpeedLimitFromCore(self, first):
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
        except Exception:
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
            if not first:
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
        except Exception:
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
                except Exception:
                    self.log.error("main.slotToolbarSpeedLimitEdited: Failed to apply the Speed Limit settings to the server.")
                    err = True
        if not err:
            if enab_str != new_enab_str or rate_str != new_rate_str:
                self.log.debug1("slotToolbarSpeedLimitEdited: setting the values in the server settings tab accordingly")
                self.mainWindow.tabs["settings"]["w"].setSpeedLimitFromToolbar(new_enab_str, new_rate_str)
        self.inSlotToolbarSpeedLimitEdited = False

    def slotCaptchaStatusButton(self):
        """
            the captcha status button in the toolbar was clicked
        """
        self.mainWindow.captchaDialog.emit(SIGNAL("show"), self.lastCaptchaId is None)

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

        self.buttons = WtDialogButtonBox(Qt.Horizontal, self)
        self.buttons.hideWhatsThisButton()
        self.okBtn = self.buttons.addButton(QDialogButtonBox.Ok)
        self.buttons.button(QDialogButtonBox.Ok).setText(_("OK"))
        self.copyBtn = QPushButton(_("Copy to Clipboard"))
        self.buttons.addButton(self.copyBtn, QDialogButtonBox.ActionRole)

        vbox = QVBoxLayout()
        vbox.addLayout(hbox)
        vbox.addSpacing(5)
        vbox.addStretch(1)
        vbox.addLayout(self.buttons.layout())
        self.setLayout(vbox)

        self.connect(self.okBtn, SIGNAL("clicked()"), self.accept)
        self.connect(self.copyBtn, SIGNAL("clicked()"), self.copyToClipboard)

    def copyToClipboard(self):
        txt = self.text3.text()
        clipboard = QApplication.clipboard()
        clipboard.setText(txt)

    def exec_(self, version, internalversion):
        import platform
#       import os
        import struct
        from PyQt4.QtCore import QT_VERSION_STR
        txt1 = _("pyLoad Client") + " v" + version
        self.text1.setText(txt1)
        txt2 = "2008-2016 the pyLoad Team"
        self.text2.setText(txt2)
        txt3  = "Version: " + version
        txt3 += "\nInternal version: " + internalversion
        txt3 += "\n\nPlatform: " + platform.platform()
        if os.name == "nt":
            if "PROGRAMFILES(X86)" in os.environ:
                txt3 += " (64bit)"
            else:
                txt3 += " (32bit)"
        txt3 += "\nPython version: " + platform.python_version() + " (%dbit)" % (struct.calcsize("P") * 8)
        txt3 += "\nQt version: " + QT_VERSION_STR
        try:
            from PyQt4.pyqtconfig import Configuration
            cfg = Configuration()
            sipver = cfg.sip_version_str
            pyqtver = cfg.pyqt_version_str
        except Exception:
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
        self.setWindowFlags(self.windowFlags() &~ Qt.WindowContextHelpButtonHint)
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
        #admKlbl = QLabel(admin[2])
        admLbl.setWhatsThis(p(admin[0], admin[3]) + d(admin[4]))

        grid.addWidget(admLbl,  1, 0)
        grid.addWidget(admVal,  1, 1)
        #grid.addWidget(admKlbl, 1, 3)
        for i, perm in enumerate(plist):
            lbl = QLabel(perm[0])
            val = LineView(perm[1])
            klbl = QLabel(perm[2])
            lbl.setWhatsThis(p(perm[0], perm[3]) + d(perm[4]))
            lbl. setDisabled(self.perms["admin"])
            val. setDisabled(self.perms["admin"])
            klbl.setDisabled(self.perms["admin"])
            grid.addWidget(lbl,  i + 2, 0)
            grid.addWidget(val,  i + 2, 1)
            grid.addWidget(klbl, i + 2, 3)

        grid.setRowMinimumHeight(0, 2)
        grid.setColumnMinimumWidth(2, 10)
        grid.setColumnStretch(2, 1)

        gp = QGroupBox(_("Server Permissions") + "     ")
        gp.setLayout(grid)

        hintLbl = QLabel("<b>" + _("Permissons were changed.<br>") + _("Takes effect on next login.") + "</b>")
        hintLbl.setWordWrap(True)

        self.buttons = WtDialogButtonBox(Qt.Horizontal, self)
        self.closeBtn = self.buttons.addButton(QDialogButtonBox.Close)
        self.buttons.button(QDialogButtonBox.Close).setText(_("Close"))

        vbox = QVBoxLayout()
        vbox.addWidget(gp)
        if self.perms != self.activeperms:
            vbox.addWidget(hintLbl)
        vbox.addStretch(1)
        vbox.addLayout(self.buttons.layout())
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
                         "- Toolbar: Clipboard Watcher")
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
                         "- Toolbar: Run, Pause and Stop feature to set server status 'Paused'<br>"
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
        # wait max 10sec
        for dummy in range(0, 100):
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
            self.dock_socket.settimeout(0.2)
            self.dock_socket.bind((self.localIp, self.localPort))
            self.dock_socket.listen(5)
        except socket.error, x:
            if x.args[0] == errno.EADDRINUSE:
                self.log.error("ClickNLoadForwarder.server: Cannot bind to port %d, the port is occupied." % self.localPort)
                self.log.info("ClickNLoadForwarder.server: If you are pretty sure that the port should be free, try waiting 2-3 minutes for the operating system to close the port.")
            self.onRaise()
            raise
        except Exception:
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
            except socket.timeout:
                continue
            except socket.error:
                if self.doStop:
                    self.log.debug9("ClickNLoadForwarder.server: stopped (2)")
                    self.exitOnStop()
                elif self.forwardError:
                    self.exitOnForwardError()
                else:
                    self.onRaise()
                    raise
            except Exception:
                self.onRaise()
                raise
            try:
                self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.server_socket.connect((self.extIp, self.extPort))
                thread.start_new_thread(self.forward, (self.client_socket, self.server_socket))
                thread.start_new_thread(self.forward, (self.server_socket, self.client_socket))
            except Exception:
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
                string = source.recv(1024) # throws EWOULDBLOCK when there is no data to read yet
                if string:
                    destination.sendall(string)
                else:
                    #source.shutdown(socket.SHUT_RD)
                    destination.shutdown(socket.SHUT_WR)
            except socket.error, x:
                if x.args[0] == errno.EWOULDBLOCK:
                    sleep(0.2)
                    continue
                elif not self.forwardError:
                    self.forwardError = True
                    self.log.error("ClickNLoadForwarder.forward: Unexpected socket error")
            except Exception:
                if not self.forwardError:
                    self.forwardError = True
                    self.log.error("ClickNLoadForwarder.forward: Unexpected error")

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
        except Exception: self.log.debug9("ClickNLoadForwarder.closeSockets: Exception (1) when shutting down the read side of the socket")
        try:    self.server_socket.shutdown(socket.SHUT_WR)
        except Exception: self.log.debug9("ClickNLoadForwarder.closeSockets: Exception (1) when shutting down the write side of the socket")
        try:    self.server_socket.close()
        except Exception: self.log.debug9("ClickNLoadForwarder.closeSockets: Exception (1) when closing the socket")
        try:    self.client_socket.shutdown(socket.SHUT_RD)
        except Exception: self.log.debug9("ClickNLoadForwarder.closeSockets: Exception (2) when shutting down the read side of the socket")
        try:    self.client_socket.shutdown(socket.SHUT_WR)
        except Exception: self.log.debug9("ClickNLoadForwarder.closeSockets: Exception (2) when shutting down the write side of the socket")
        try:    self.client_socket.close()
        except Exception: self.log.debug9("ClickNLoadForwarder.closeSockets: Exception (2) when closing the socket")
        try:    self.dock_socket.shutdown(socket.SHUT_RD)
        except Exception: self.log.debug9("ClickNLoadForwarder.closeSockets: Exception (3) when shutting down the read side of the socket")
        try:    self.dock_socket.shutdown(socket.SHUT_WR)
        except Exception: self.log.debug9("ClickNLoadForwarder.closeSockets: Exception (3) when shutting down the write side of the socket")
        try:    self.dock_socket.close()
        except Exception: self.log.debug9("ClickNLoadForwarder.closeSockets: Exception (3) when closing the socket")

    def messageBox_19(self):
        self.emit(SIGNAL("msgBoxError"), _("Failed to stop ClickNLoad port forwarding."))

    def messageBox_20(self):
        self.emit(SIGNAL("msgBoxError"), _("ClickNLoad port forwarding stopped due to an error."))

class TrayIcon(QSystemTrayIcon):
    def __init__(self):
        QSystemTrayIcon.__init__(self)
        self.log = logging.getLogger("guilog")

        self.menu = QMenu()
        self.showAction = QAction("show/hide", self.menu)
        self.showAction.setIcon(QIcon(join(pypath, "icons", "logo.png")))
        self.setShowActionText(False)
        self.menu.addAction(self.showAction)
        self.captchaAction = QAction(_("Captcha"), self.menu)
        self.menu.addAction(self.captchaAction)
        self.menuAdd = self.menu.addMenu(QIcon(join(pypath, "icons", "add_small.png")), _("Add"))
        self.addPackageAction = self.menuAdd.addAction(_("Package"))
        self.addLinksAction = self.menuAdd.addAction(_("Links"))
        self.addContainerAction = self.menuAdd.addAction(_("Container"))
        self.menu.addSeparator()
        self.exitAction = QAction(QIcon(join(pypath, "icons", "abort_small.png")), _("Exit"), self.menu)
        self.menu.addAction(self.exitAction)
        self.setContextMenu(self.menu)
        if self.log.isEnabledFor(logging.DEBUG9):
            self.menu.addSeparator()
            self.menuDebug = self.menu.addMenu("Debug")
            self.debugTrayAction = self.menuDebug.addAction("Tray")
            self.debugMsgBoxTest1Action = self.menuDebug.addAction("MessageBox Test 1")
            self.debugMsgBoxTest2Action = self.menuDebug.addAction("MessageBox Test 2")
            self.debugKillAction = self.menuDebug.addAction("kill")

        # disable/greyout menu entries
        self.showAction.setEnabled(False)
        self.captchaAction.setEnabled(False)
        self.menuAdd.setEnabled(False)

    def setupIcon(self, size):
        if size == "24x24":
            icon = QIcon(join(pypath, "icons", "logo-gui24x24.png"))
        elif size == "64x64":
            icon = QIcon(join(pypath, "icons", "logo-gui64x64.png"))
        else:
            icon = QIcon()
        self.setIcon(icon)

    def setShowActionText(self, show):
        if show:
            self.showAction.setText(_("Show pyLoad Client"))
        else:
            self.showAction.setText(_("Hide pyLoad Client"))

    def clicked(self, reason):
        # forbid all actions when a modal dialog is visible, this is mainly for ms windows os
        if QApplication.activeModalWidget() is not None:
            if self.contextMenu() is not None:
                self.menu.hide()
                self.setContextMenu(None)
                self.log.debug4("TrayIcon.clicked: context menu deactivated")
            self.log.debug4("TrayIcon.clicked: click ignored")
            return
        elif self.contextMenu() is None:
            self.setContextMenu(self.menu)
            self.log.debug4("TrayIcon.clicked: context menu reactivated")
            if reason == QSystemTrayIcon.Context:
                self.menu.show()
                self.log.debug4("TrayIcon.clicked: show reactivated context menu")
                return

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

        self.buttons = WtDialogButtonBox(Qt.Horizontal, self)
        self.buttons.hideWhatsThisButton()
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
        vbox.addLayout(self.buttons.layout())

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

    def appFontChanged(self):
        self.buttons.updateWhatsThisButton()

class Notification(QObject):
    def __init__(self, tray):
        QObject.__init__(self)
        self.log = logging.getLogger("guilog")
        self.tray = tray

        self.usePynotify = False
        if os.name != "nt":
            if not havePynotify:
                self.log.info("Notification: Pynotify not installed, falling back to qt tray notification")
                return
            try:
                self.usePynotify = pynotify.init(_("pyLoad Client"))
            except Exception:
                self.usePynotify = False
            if not self.usePynotify:
                self.log.error("Notification: Pynotify initialization failed")

    def showMessage(self, body):
        if self.usePynotify:
            n = pynotify.Notification(_("pyLoad Client"), body, join(pypath, "icons", "logo.png"))
            try:
                n.set_hint_string("x-canonical-append", "")
            except Exception:
                self.log.debug9("Notification: set_hint_string failed")
            n.show()
        else:
            self.tray.showMessage(_("pyLoad Client"), body)

if __name__ == "__main__":
    renameProcess('pyLoadGui')
    app = main()
    app.loop()

