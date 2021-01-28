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
"""

from module.gui.PyQtVersion import USE_PYQT5
if USE_PYQT5:
    from PyQt5.QtCore import QByteArray, QPoint, QRect, QSize, Qt
else:
    from PyQt4.QtCore import QByteArray, QPoint, QRect, QSize, Qt

from os.path import join

from module.lib.SafeEval import const_eval as literal_eval

def connectSignals(self, first):
    """
        signal and slot stuff, yay!
    """
    if first:
        self.guiLogAppendSGL.connect(self.slotGuiLogAppend, Qt.QueuedConnection)
        self.coreLogAppendSGL.connect(self.slotCoreLogAppend, Qt.QueuedConnection)
    self.connector.connectTimeoutSGL.connect(self.slotConnectTimeout)
    self.connector.msgBoxErrorSGL.connect(self.slotMsgBoxError)
    self.clickNLoadForwarder.msgBoxErrorSGL.connect(self.slotMsgBoxError)
    self.connWindow.saveConnectionSGL.connect(self.slotSaveConnection)
    self.connWindow.saveAllConnectionsSGL.connect(self.slotSaveAllConnections)
    self.connWindow.removeConnectionSGL.connect(self.slotRemoveConnection)
    self.connWindow.connectSGL.connect(self.slotConnect, Qt.QueuedConnection)
    self.connWindow.quitConnWindowSGL.connect(self.slotQuitConnWindow)
    self.fontOptions.appFontChangedSGL.connect(self.slotAppFontChanged)
    self.mainWindow.showConnectorSGL.connect(self.slotShowConnector)
    self.mainWindow.mainWindowStateSGL.connect(self.slotMainWindowState, Qt.QueuedConnection)
    self.mainWindow.mainWindowPaintEventSGL.connect(self.slotMainWindowPaintEvent, Qt.QueuedConnection)
    self.mainWindow.showCorePermissionsSGL.connect(self.slotShowCorePermissions)
    self.mainWindow.quitCoreSGL.connect(self.slotQuitCore)
    self.mainWindow.restartCoreSGL.connect(self.slotRestartCore)
    self.mainWindow.showLoggingOptionsSGL.connect(self.slotShowLoggingOptions)
    self.mainWindow.showNotificationOptionsSGL.connect(self.slotShowNotificationOptions)
    self.mainWindow.showOtherOptionsSGL.connect(self.slotShowOtherOptions)
    self.mainWindow.showTrayOptionsSGL.connect(self.slotShowTrayOptions)
    self.mainWindow.showClickNLoadForwarderOptionsSGL.connect(self.slotShowClickNLoadForwarderOptions)
    self.mainWindow.showAutomaticReloadingOptionsSGL.connect(self.slotShowAutomaticReloadingOptions)
    self.mainWindow.showCaptchaOptionsSGL.connect(self.slotShowCaptchaOptions)
    self.mainWindow.showCaptchaFromMenuSGL.connect(self.slotShowCaptcha)
    self.mainWindow.showIconThemeOptionsSGL.connect(self.slotShowIconThemeOptions)
    self.mainWindow.showFontOptionsSGL.connect(self.slotShowFontOptions)
    self.mainWindow.showColorFixOptionsSGL.connect(self.slotShowColorFixOptions)
    self.mainWindow.showWhatsThisOptionsSGL.connect(self.slotShowWhatsThisOptions)
    self.mainWindow.showLanguageOptionsSGL.connect(self.slotShowLanguageOptions)
    self.mainWindow.showPyQtVersionOptionsSGL.connect(self.slotShowPyQtVersionOptions)
    self.mainWindow.reloadQueueSGL.connect(self.slotReloadQueue)
    self.mainWindow.reloadCollectorSGL.connect(self.slotReloadCollector)
    self.mainWindow.addPackageSGL.connect(self.slotAddPackage)
    self.mainWindow.addLinksToPackageSGL.connect(self.slotAddLinksToPackage)
    self.mainWindow.setDownloadStatusSGL.connect(self.slotSetDownloadStatus)
    self.mainWindow.pushPackagesToQueueSGL.connect(self.slotPushPackagesToQueue)
    self.mainWindow.restartDownloadsSGL.connect(self.slotRestartDownloads)
    self.mainWindow.removeDownloadsSGL.connect(self.slotRemoveDownloads)
    self.mainWindow.editPackagesSGL.connect(self.slotEditPackages)
    self.mainWindow.abortDownloadsSGL.connect(self.slotAbortDownloads)
    self.mainWindow.selectAllSGL.connect(self.slotSelectAll)
    self.mainWindow.deselectAllSGL.connect(self.slotDeselectAll)
    self.mainWindow.selectAllPackagesSGL.connect(self.slotSelectAllPackages)
    self.mainWindow.deselectAllPackagesSGL.connect(self.slotDeselectAllPackages)
    self.mainWindow.advancedSelectSGL.connect(self.slotAdvancedSelect)
    self.mainWindow.removePackageDupesSGL.connect(self.slotRemovePackageDupes)
    self.mainWindow.removeLinkDupesSGL.connect(self.slotRemoveLinkDupes)
    self.mainWindow.sortPackagesSGL.connect(self.slotSortPackages)
    self.mainWindow.sortLinksSGL.connect(self.slotSortLinks)
    self.mainWindow.expandAllSGL.connect(self.slotExpandAll)
    self.mainWindow.collapseAllSGL.connect(self.slotCollapseAll)
    self.mainWindow.showAddPackageSGL.connect(self.slotShowAddPackage)
    self.mainWindow.showAddLinksSGL.connect(self.slotShowAddLinks)
    self.mainWindow.addContainerSGL.connect(self.slotAddContainer)
    self.mainWindow.stopAllDownloadsSGL.connect(self.slotStopAllDownloads)
    self.mainWindow.captchaStatusButtonSGL.connect(self.slotCaptchaStatusButton)
    self.mainWindow.restartFailedSGL.connect(self.slotRestartFailed)
    self.mainWindow.deleteFinishedSGL.connect(self.slotDeleteFinished)
    self.mainWindow.pullOutPackagesSGL.connect(self.slotPullOutPackages)
    self.mainWindow.reloadAccountsSGL.connect(self.slotReloadAccounts)
    self.mainWindow.menuPluginNotFoundSGL.connect(self.slotMenuPluginNotFound)
    self.mainWindow.showAboutSGL.connect(self.slotShowAbout)
    self.mainWindow.mainWindowCloseSGL.connect(self.slotMainWindowClose)

    self.mainWindow.mactions["exit"].triggered.connect(self.slotQuit)
    self.mainWindow.captchaDialog.captchaDoneSGL.connect(self.slotCaptchaDone)
    self.mainWindow.newPackDock.newPackDockPaintEventSGL.connect(self.slotActivateNewPackDock, Qt.QueuedConnection)
    self.mainWindow.newPackDock.newPackDockClosedSGL.connect(self.slotNewPackDockClosed)
    self.mainWindow.newPackDock.topLevelChanged[bool].connect(self.slotNewPackDockTopLevelChanged, Qt.QueuedConnection)
    self.mainWindow.newLinkDock.newLinkDockPaintEventSGL.connect(self.slotActivateNewLinkDock, Qt.QueuedConnection)
    self.mainWindow.newLinkDock.newLinkDockClosedSGL.connect(self.slotNewLinkDockClosed)
    self.mainWindow.newLinkDock.topLevelChanged[bool].connect(self.slotNewLinkDockTopLevelChanged, Qt.QueuedConnection)

    self.packageEdit.saveBtn.clicked.connect(self.slotEditPackageSave)

def saveOptionsToConfig(self, backup):
    """
        save options to the config file
    """
    if backup:
        with open("gui.xml", "r") as src, open("gui.xml.backup.reset", "w") as dst: dst.write(src.read())
    mainWindowNode = self.parser.xml.elementsByTagName("mainWindow").item(0)
    if mainWindowNode.isNull():
        mainWindowNode = self.parser.xml.createElement("mainWindow")
        self.parser.root.appendChild(mainWindowNode)
    optionsNotifications = str(QByteArray(str(self.notificationOptions.settings)).toBase64())
    optionsLogging = str(QByteArray(str(self.loggingOptions.settings)).toBase64())
    optionsClickNLoadForwarder = str(self.clickNLoadForwarderOptions.settings["fromPort"])
    optionsAutomaticReloading = str(QByteArray(str(self.automaticReloadingOptions.settings)).toBase64())
    optionsCaptcha = str(QByteArray(str(self.captchaOptions.settings)).toBase64())
    optionsIconTheme = str(QByteArray(str(self.iconThemeOptions.settings)).toBase64())
    optionsFonts = str(QByteArray(str(self.fontOptions.settings)).toBase64())
    optionsColorFix = str(QByteArray(str(self.colorFixOptions.settings)).toBase64())
    optionsTray = str(QByteArray(str(self.trayOptions.settings)).toBase64())
    optionsWhatsThis = str(QByteArray(str(self.whatsThisOptions.settings)).toBase64())
    optionsOther = str(QByteArray(str(self.otherOptions.settings)).toBase64())
    menuPlugins = str(self.mainWindow.tabs["settings"]["w"].menuPlugins)
    lastAddContainerDir = self.mainWindow.lastAddContainerDir
    optionsNotificationsNode = mainWindowNode.toElement().elementsByTagName("optionsNotifications").item(0)
    optionsLoggingNode = mainWindowNode.toElement().elementsByTagName("optionsLogging").item(0)
    optionsClickNLoadForwarderNode = mainWindowNode.toElement().elementsByTagName("optionsClickNLoadForwarder").item(0)
    optionsAutomaticReloadingNode = mainWindowNode.toElement().elementsByTagName("optionsAutomaticReloading").item(0)
    optionsCaptchaNode = mainWindowNode.toElement().elementsByTagName("optionsCaptcha").item(0)
    optionsIconThemeNode = mainWindowNode.toElement().elementsByTagName("optionsIconTheme").item(0)
    optionsFontsNode = mainWindowNode.toElement().elementsByTagName("optionsFonts").item(0)
    optionsColorFixNode = mainWindowNode.toElement().elementsByTagName("optionsColorFix").item(0)
    optionsTrayNode = mainWindowNode.toElement().elementsByTagName("optionsTray").item(0)
    optionsWhatsThisNode = mainWindowNode.toElement().elementsByTagName("optionsWhatsThis").item(0)
    optionsOtherNode = mainWindowNode.toElement().elementsByTagName("optionsOther").item(0)
    menuPluginsNode = mainWindowNode.toElement().elementsByTagName("menuPlugins").item(0)
    lastAddContainerDirNode = mainWindowNode.toElement().elementsByTagName("lastAddContainerDir").item(0)
    newOptionsNotificationsNode = self.parser.xml.createTextNode(optionsNotifications)
    newOptionsLoggingNode = self.parser.xml.createTextNode(optionsLogging)
    newOptionsClickNLoadForwarderNode = self.parser.xml.createTextNode(optionsClickNLoadForwarder)
    newOptionsAutomaticReloadingNode = self.parser.xml.createTextNode(optionsAutomaticReloading)
    newOptionsCaptchaNode = self.parser.xml.createTextNode(optionsCaptcha)
    newOptionsIconThemeNode = self.parser.xml.createTextNode(optionsIconTheme)
    newOptionsFontsNode = self.parser.xml.createTextNode(optionsFonts)
    newOptionsColorFixNode = self.parser.xml.createTextNode(optionsColorFix)
    newOptionsTrayNode = self.parser.xml.createTextNode(optionsTray)
    newOptionsWhatsThisNode = self.parser.xml.createTextNode(optionsWhatsThis)
    newOptionsOtherNode = self.parser.xml.createTextNode(optionsOther)
    newMenuPluginsNode = self.parser.xml.createTextNode(menuPlugins)
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
    optionsIconThemeNode.removeChild(optionsIconThemeNode.firstChild())
    optionsIconThemeNode.appendChild(newOptionsIconThemeNode)
    optionsFontsNode.removeChild(optionsFontsNode.firstChild())
    optionsFontsNode.appendChild(newOptionsFontsNode)
    optionsColorFixNode.removeChild(optionsColorFixNode.firstChild())
    optionsColorFixNode.appendChild(newOptionsColorFixNode)
    optionsTrayNode.removeChild(optionsTrayNode.firstChild())
    optionsTrayNode.appendChild(newOptionsTrayNode)
    optionsWhatsThisNode.removeChild(optionsWhatsThisNode.firstChild())
    optionsWhatsThisNode.appendChild(newOptionsWhatsThisNode)
    optionsOtherNode.removeChild(optionsOtherNode.firstChild())
    optionsOtherNode.appendChild(newOptionsOtherNode)
    menuPluginsNode.removeChild(menuPluginsNode.firstChild())
    menuPluginsNode.appendChild(newMenuPluginsNode)
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
    gUnmax["unmaxed_pos"] = gUnmax["unmaxed_size"] = 0
    if self.geoUnmaximized["unmaxed_pos"] is not None:
        gUnmax["unmaxed_pos"] = [self.geoUnmaximized["unmaxed_pos"].x(), self.geoUnmaximized["unmaxed_pos"].y()]
    if self.geoUnmaximized["unmaxed_size"] is not None:
        gUnmax["unmaxed_size"] = [self.geoUnmaximized["unmaxed_size"].width(), self.geoUnmaximized["unmaxed_size"].height()]
    gUnmax["maximized"] = self.geoUnmaximized["maximized"]
    geoUnmaximized = str(QByteArray(str(gUnmax)).toBase64())
    # convert Qt variable types to integer, literal_eval does not accept Qt variables
    gOther["packDock"] = gOther["linkDock"] = gOther["packDockTray"] = gOther["linkDockTray"] = gOther["captchaDialog"] = 0
    if self.geoOther["packDock"] is not None:
        gOther["packDock"] = [self.geoOther["packDock"].x(), self.geoOther["packDock"].y(),
                              self.geoOther["packDock"].width(), self.geoOther["packDock"].height()]
    if self.geoOther["linkDock"] is not None:
        gOther["linkDock"] = [self.geoOther["linkDock"].x(), self.geoOther["linkDock"].y(),
                              self.geoOther["linkDock"].width(), self.geoOther["linkDock"].height()]
    if self.geoOther["packDockTray"] is not None:
        gOther["packDockTray"] = [self.geoOther["packDockTray"].x(), self.geoOther["packDockTray"].y(),
                                  self.geoOther["packDockTray"].width(), self.geoOther["packDockTray"].height()]
    if self.geoOther["linkDockTray"] is not None:
        gOther["linkDockTray"] = [self.geoOther["linkDockTray"].x(), self.geoOther["linkDockTray"].y(),
                                  self.geoOther["linkDockTray"].width(), self.geoOther["linkDockTray"].height()]
    if self.geoOther["captchaDialog"] is not None:
        gOther["captchaDialog"] = [self.geoOther["captchaDialog"].x(), self.geoOther["captchaDialog"].y(),
                                   self.geoOther["captchaDialog"].width(), self.geoOther["captchaDialog"].height()]
    geoOther = str(QByteArray(str(gOther)).toBase64())
    stateQueue = str(self.mainWindow.tabs["queue"]["view"].header().saveState().toBase64())
    stateCollector = str(self.mainWindow.tabs["collector"]["view"].header().saveState().toBase64())
    stateAccounts = str(self.mainWindow.tabs["accounts"]["view"].header().saveState().toBase64())
    statePackageDock = str(QByteArray(str(self.mainWindow.newPackDock.getSettings())).toBase64())
    stateLinkDock = str(QByteArray(str(self.mainWindow.newLinkDock.getSettings())).toBase64())
    visibilitySpeedLimit = str(QByteArray(str(self.mainWindow.actions["speedlimit_enabled"].isVisible())).toBase64())
    visibilityMaxParallelDownloads = str(QByteArray(str(self.mainWindow.actions["maxparalleldownloads_label"].isVisible())).toBase64())
    language = str(self.lang)
    pyqtVersion = str(self.pyqtVersionOption)
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
    visibilityMaxParallelDownloadsNode = mainWindowNode.toElement().elementsByTagName("visibilityMaxParallelDownloads").item(0)
    languageNode = self.parser.xml.elementsByTagName("language").item(0)
    pyqtVersionNode = self.parser.xml.elementsByTagName("pyqtVersion").item(0)
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
    newVisibilityMaxParallelDownloadsNode = self.parser.xml.createTextNode(visibilityMaxParallelDownloads)
    newLanguageNode = self.parser.xml.createTextNode(language)
    newPyqtVersionNode = self.parser.xml.createTextNode(pyqtVersion)
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
    visibilityMaxParallelDownloadsNode.removeChild(visibilityMaxParallelDownloadsNode.firstChild())
    visibilityMaxParallelDownloadsNode.appendChild(newVisibilityMaxParallelDownloadsNode)
    languageNode.removeChild(languageNode.firstChild())
    languageNode.appendChild(newLanguageNode)
    pyqtVersionNode.removeChild(pyqtVersionNode.firstChild())
    pyqtVersionNode.appendChild(newPyqtVersionNode)
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
    if not nodes.get("optionsIconTheme"):
        mainWindowNode.appendChild(self.parser.xml.createElement("optionsIconTheme"))
    if not nodes.get("optionsFonts"):
        mainWindowNode.appendChild(self.parser.xml.createElement("optionsFonts"))
    if not nodes.get("optionsColorFix"):
        mainWindowNode.appendChild(self.parser.xml.createElement("optionsColorFix"))
    if not nodes.get("optionsTray"):
        mainWindowNode.appendChild(self.parser.xml.createElement("optionsTray"))
    if not nodes.get("optionsWhatsThis"):
        mainWindowNode.appendChild(self.parser.xml.createElement("optionsWhatsThis"))
    if not nodes.get("optionsOther"):
        mainWindowNode.appendChild(self.parser.xml.createElement("optionsOther"))
    if not nodes.get("menuPlugins"):
        mainWindowNode.appendChild(self.parser.xml.createElement("menuPlugins"))
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
    optionsIconTheme = str(nodes["optionsIconTheme"].text())
    optionsFonts = str(nodes["optionsFonts"].text())
    optionsColorFix = str(nodes["optionsColorFix"].text())
    optionsTray = str(nodes["optionsTray"].text())
    optionsWhatsThis = str(nodes["optionsWhatsThis"].text())
    optionsOther = str(nodes["optionsOther"].text())
    menuPlugins = str(nodes["menuPlugins"].text())
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

    def strToList(s):
        try:
            l = literal_eval(s)
        except Exception:
            l = None
        if l and not isinstance(l, list):
            l = None
        return l

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
    try:     self.clickNLoadForwarderOptions.settings["fromPort"] = int(optionsClickNLoadForwarder); self.clickNLoadForwarderOptions.dict2dialogState(True)
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
    self.mainWindow.actions["captcha"].setVisible(self.captchaOptions.settings["Enabled"])
    # Icon Theme
    d = base64ToDict(optionsIconTheme)
    if d is not None:
        try:              self.iconThemeOptions.settings = d; self.iconThemeOptions.dict2dialogState()
        except Exception: self.iconThemeOptions.defaultSettings(); d = None
    if d is None: self.messageBox_21(_("Icon Theme")); reset = True
    # Fonts
    d = base64ToDict(optionsFonts)
    if d is not None:
        try:              self.fontOptions.settings = d; self.fontOptions.dict2dialogState()
        except Exception: self.fontOptions.defaultSettings(); d = None
    if d is None: self.messageBox_21(_("Fonts")); reset = True
    self.fontOptions.applySettings()
    # Color Fix
    d = base64ToDict(optionsColorFix)
    if d is not None:
        try:              self.colorFixOptions.settings = d; self.colorFixOptions.dict2dialogState()
        except Exception: self.colorFixOptions.defaultSettings(); d = None
    if d is None: self.messageBox_21(_("Color Fix")); reset = True
    self.colorFixOptions.applySettings()
    self.colorFixOptions.slotSetPreviewButtonAlpha(self.colorFixOptions.settings["alpha"])
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
    # Menu->Plugins entries
    l = strToList(menuPlugins)
    if l is None: self.messageBox_25(); reset = True
    else: self.mainWindow.tabs["settings"]["w"].menuPlugins = l
    # Last folder from where a container file was loaded
    self.mainWindow.lastAddContainerDir = lastAddContainerDir
    if reset:
        self.messageBox_26()
        self.saveOptionsToConfig(True)

def loadWindowFromConfig(self):
    """
        load window geometry and state from the config file
        and show main window and docks
    """
    rootNode = self.parser.xml.elementsByTagName("root").item(0)
    if rootNode.isNull():
        return
    nodes = self.parser.parseNode(rootNode, "dict")
    if not nodes.get("pyqtVersion"):
        rootNode.appendChild(self.parser.xml.createElement("pyqtVersion"))
    self.parser.parseNode(rootNode, "dict")   # reparse with the new nodes (if any)

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
    if not nodes.get("visibilityMaxParallelDownloads"):
        mainWindowNode.appendChild(self.parser.xml.createElement("visibilityMaxParallelDownloads"))
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
    visibilityMaxParallelDownloads = str(nodes["visibilityMaxParallelDownloads"].text())

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
    self.geoOther["packDock"] = self.geoOther["linkDock"] = None
    self.geoOther["packDockTray"] = self.geoOther["linkDockTray"] = None
    self.geoOther["captchaDialog"] = None
    if gOther["packDock"] != 0:
        self.geoOther["packDock"] = QRect(gOther["packDock"][0], gOther["packDock"][1], gOther["packDock"][2], gOther["packDock"][3])
    if gOther["linkDock"] != 0:
        self.geoOther["linkDock"] = QRect(gOther["linkDock"][0], gOther["linkDock"][1], gOther["linkDock"][2], gOther["linkDock"][3])
    if gOther["packDockTray"] != 0:
        self.geoOther["packDockTray"] = QRect(gOther["packDockTray"][0], gOther["packDockTray"][1], gOther["packDockTray"][2], gOther["packDockTray"][3])
    if gOther["linkDockTray"] != 0:
        self.geoOther["linkDockTray"] = QRect(gOther["linkDockTray"][0], gOther["linkDockTray"][1], gOther["linkDockTray"][2], gOther["linkDockTray"][3])
    if gOther["captchaDialog"] != 0:
        self.geoOther["captchaDialog"] = QRect(gOther["captchaDialog"][0], gOther["captchaDialog"][1], gOther["captchaDialog"][2], gOther["captchaDialog"][3])

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
        self.scheduleMainWindowPaintEventAction(pos=self.mainWindow.pos(), size=self.mainWindow.size(),
                                                refreshGeo=self.otherOptions.settings["RefreshGeo"], pdGeo=pdGeo, plGeo=plGeo)
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
        if ((self.mainWindow.newPackDock.isFloating() and not self.mainWindow.newPackDock.isHidden()) or
                (self.mainWindow.newLinkDock.isFloating() and not self.mainWindow.newLinkDock.isHidden())):
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
    if visibilityMaxParallelDownloads:
        visMaxPaDls = literal_eval(str(QByteArray.fromBase64(visibilityMaxParallelDownloads)))
    else:
        visMaxPaDls = True
    self.mainWindow.mactions["showmaxpadls"].setChecked(not visMaxPaDls)
    self.mainWindow.mactions["showmaxpadls"].setChecked(visMaxPaDls)
    self.mainWindow.captchaDialog.geo = self.geoOther["captchaDialog"]
    self.fixFirstShowFromTrayWhenLoadedMaximized = self.geoUnmaximized["maximized"]

    if not (self.mainWindow.newPackDock.isFloating() or self.mainWindow.newPackDock.isHidden()):
        self.waitForPaintEvents(1)
        self.mainWindow.newPackDock.raise_()   # activate tab

