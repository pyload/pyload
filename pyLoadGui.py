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

import sys

from uuid import uuid4 as uuid # should be above PyQt imports
from time import sleep, time

from base64 import b64decode

from PyQt4.QtCore import *
from PyQt4.QtGui import *

import re
import module.common.pylgettext as gettext
import os
from os.path import abspath
from os.path import join
from os.path import basename
from os.path import commonprefix

from module import InitHomeDir
from module.gui.ConnectionManager import *
from module.gui.Connector import Connector
from module.gui.MainWindow import *
from module.gui.Queue import *
from module.gui.Overview import *
from module.gui.Collector import *
from module.gui.XMLParser import *
from module.gui.CoreConfigParser import ConfigParser

from module.lib.rename_process import renameProcess
from module.utils import formatSize, formatSpeed

try:
    import pynotify
except ImportError:
    print "pynotify not installed, falling back to qt tray notification"

class main(QObject):
    def __init__(self):
        """
            main setup
        """
        QObject.__init__(self)
        self.app = QApplication(sys.argv)
        self.path = pypath
        self.homedir = abspath("")

        self.configdir = ""

        self.init(True)

    def init(self, first=False):
        """
            set main things up
        """
        self.parser = XMLParser(join(self.configdir, "gui.xml"), join(self.path, "module", "config", "gui_default.xml"))
        lang = self.parser.xml.elementsByTagName("language").item(0).toElement().text()
        if not lang:
            parser = XMLParser(join(self.path, "module", "config", "gui_default.xml"))
            lang = parser.xml.elementsByTagName("language").item(0).toElement().text()

        gettext.setpaths([join(os.sep, "usr", "share", "pyload", "locale"), None])
        translation = gettext.translation("pyLoadGui", join(pypath, "locale"), languages=[str(lang), "en"], fallback=True)
        try:
            translation.install(unicode=(True if sys.stdout.encoding.lower().startswith("utf") else False))
        except:
            translation.install(unicode=False)


        self.connector = Connector()
        self.mainWindow = MainWindow(self.connector)
        self.connWindow = ConnectionManager()
        self.mainloop = self.Loop(self)
        self.connectSignals()

        self.checkClipboard = False
        default = self.refreshConnections()
        self.connData = None
        self.captchaProcessing = False
        self.serverStatus = {"freespace":0}

        self.core = None # pyLoadCore if started
        self.connectionLost = False

        if True: # when used if first, minimizing not working correctly..
            self.tray = TrayIcon()
            self.tray.show()
            self.notification = Notification(self.tray)
            self.connect(self, SIGNAL("showMessage"), self.notification.showMessage)
            self.connect(self.tray.exitAction, SIGNAL("triggered()"), self.slotQuit)
            self.connect(self.tray.showAction, SIGNAL("toggled(bool)"), self.mainWindow.setVisible)
            self.connect(self.mainWindow, SIGNAL("hidden"), self.tray.mainWindowHidden)

        if not first:
            self.connWindow.show()
        else:
            self.connWindow.edit.setData(default)
            data = self.connWindow.edit.getData()
            self.slotConnect(data)

    def startMain(self):
        """
            start all refresh threads and show main window
        """
        if not self.connector.connectProxy():
            self.init()
            return
        self.connect(self.connector, SIGNAL("connectionLost"), self.slotConnectionLost)
        self.restoreMainWindow()
        self.mainWindow.show()
        self.initQueue()
        self.initPackageCollector()
        self.mainloop.start()
        self.clipboard = self.app.clipboard()
        self.connect(self.clipboard, SIGNAL('dataChanged()'), self.slotClipboardChange)
        self.mainWindow.actions["clipboard"].setChecked(self.checkClipboard)

        self.mainWindow.tabs["settings"]["w"].setConnector(self.connector)
        self.mainWindow.tabs["settings"]["w"].loadConfig()
        self.tray.showAction.setDisabled(False)

    def stopMain(self):
        """
            stop all refresh threads and hide main window
        """
        self.tray.showAction.setDisabled(True)
        self.disconnect(self.clipboard, SIGNAL('dataChanged()'), self.slotClipboardChange)
        self.disconnect(self.connector, SIGNAL("connectionLost"), self.slotConnectionLost)
        self.mainloop.stop()
        self.mainWindow.saveWindow()
        self.mainWindow.hide()
        self.queue.stop()

    def connectSignals(self):
        """
            signal and slot stuff, yay!
        """
        self.connect(self.connector, SIGNAL("errorBox"), self.slotErrorBox)
        self.connect(self.connWindow, SIGNAL("saveConnection"), self.slotSaveConnection)
        self.connect(self.connWindow, SIGNAL("removeConnection"), self.slotRemoveConnection)
        self.connect(self.connWindow, SIGNAL("connect"), self.slotConnect)
        self.connect(self.mainWindow, SIGNAL("connector"), self.slotShowConnector)
        self.connect(self.mainWindow, SIGNAL("addPackage"), self.slotAddPackage)
        self.connect(self.mainWindow, SIGNAL("setDownloadStatus"), self.slotSetDownloadStatus)
        self.connect(self.mainWindow, SIGNAL("saveMainWindow"), self.slotSaveMainWindow)
        self.connect(self.mainWindow, SIGNAL("pushPackageToQueue"), self.slotPushPackageToQueue)
        self.connect(self.mainWindow, SIGNAL("restartDownload"), self.slotRestartDownload)
        self.connect(self.mainWindow, SIGNAL("removeDownload"), self.slotRemoveDownload)
        self.connect(self.mainWindow, SIGNAL("abortDownload"), self.slotAbortDownload)
        self.connect(self.mainWindow, SIGNAL("addContainer"), self.slotAddContainer)
        self.connect(self.mainWindow, SIGNAL("stopAllDownloads"), self.slotStopAllDownloads)
        self.connect(self.mainWindow, SIGNAL("setClipboardStatus"), self.slotSetClipboardStatus)
        self.connect(self.mainWindow, SIGNAL("changePackageName"), self.slotChangePackageName)
        self.connect(self.mainWindow, SIGNAL("pullOutPackage"), self.slotPullOutPackage)
        self.connect(self.mainWindow, SIGNAL("refreshStatus"), self.slotRefreshStatus)
        self.connect(self.mainWindow, SIGNAL("reloadAccounts"), self.slotReloadAccounts)
        self.connect(self.mainWindow, SIGNAL("Quit"), self.slotQuit)

        self.connect(self.mainWindow.mactions["exit"], SIGNAL("triggered()"), self.slotQuit)
        self.connect(self.mainWindow.captchaDock, SIGNAL("done"), self.slotCaptchaDone)

    def slotShowConnector(self):
        """
            emitted from main window (menu)
            hide the main window and show connection manager
            (to switch to other core)
        """
        self.quitInternal()
        self.stopMain()
        self.init()

    #def quit(self): #not used anymore?
    #    """
    #        quit gui
    #    """
    #    self.app.quit()

    def loop(self):
        """
            start application loop
        """
        sys.exit(self.app.exec_())

    def slotErrorBox(self, msg):
        """
            display a nice error box
        """
        msgb = QMessageBox(QMessageBox.Warning, "Error", msg)
        msgb.exec_()

    def initPackageCollector(self):
        """
            init the package collector view
            * columns
            * selection
            * refresh thread
            * drag'n'drop
        """
        view = self.mainWindow.tabs["collector"]["package_view"]
        view.setSelectionBehavior(QAbstractItemView.SelectRows)
        view.setSelectionMode(QAbstractItemView.ExtendedSelection)
        def dropEvent(klass, event):
            event.setDropAction(Qt.CopyAction)
            event.accept()
            view = event.source()
            if view == klass:
                items = view.selectedItems()
                for item in items:
                    if not hasattr(item.parent(), "getPackData"):
                        continue
                    target = view.itemAt(event.pos())
                    if not hasattr(target, "getPackData"):
                        target = target.parent()
                    klass.emit(SIGNAL("droppedToPack"), target.getPackData()["id"], item.getFileData()["id"])
                event.ignore()
                return
            items = view.selectedItems()
            for item in items:
                row = view.indexOfTopLevelItem(item)
                view.takeTopLevelItem(row)
        def dragEvent(klass, event):
            #view = event.source()
            #dragOkay = False
            #items = view.selectedItems()
            #for item in items:
            #    if hasattr(item, "_data"):
            #        if item._data["id"] == "fixed" or item.parent()._data["id"] == "fixed":
            #            dragOkay = True
            #    else:
            #        dragOkay = True
            #if dragOkay:
            event.accept()
            #else:
            #    event.ignore()
        view.dropEvent = dropEvent
        view.dragEnterEvent = dragEvent
        view.setDragEnabled(True)
        view.setDragDropMode(QAbstractItemView.DragDrop)
        view.setDropIndicatorShown(True)
        view.setDragDropOverwriteMode(True)
        view.connect(view, SIGNAL("droppedToPack"), self.slotAddFileToPackage)
        #self.packageCollector = PackageCollector(view, self.connector)
        self.packageCollector = view.model()

    def initQueue(self):
        """
            init the queue view
            * columns
            * progressbar
        """
        view = self.mainWindow.tabs["queue"]["view"]
        view.setSelectionBehavior(QAbstractItemView.SelectRows)
        view.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.queue = view.model()
        self.connect(self.queue, SIGNAL("updateCount"), self.slotUpdateCount)
        overview = self.mainWindow.tabs["overview"]["view"].model()
        overview.queue = self.queue
        self.connect(self.queue, SIGNAL("updateCount"), overview.queueChanged)
        self.queue.start()
    
    def slotUpdateCount(self, pc, fc):
        self.mainWindow.packageCount.setText("%i" % pc)
        self.mainWindow.fileCount.setText("%i" % fc)
    
    def refreshServerStatus(self):
        """
            refresh server status and overall speed in the status bar
        """
        s = self.connector.statusServer()
        if s.pause:
            self.mainWindow.status.setText(_("paused"))
        else:
            self.mainWindow.status.setText(_("running"))
        self.mainWindow.speed.setText(formatSpeed(s.speed))
        self.mainWindow.space.setText(formatSize(self.serverStatus["freespace"]))
        self.mainWindow.actions["toggle_status"].setChecked(not s.pause)

    def refreshLog(self):
        """
            update log window
        """
        offset = self.mainWindow.tabs["log"]["text"].logOffset
        lines = self.connector.getLog(offset)
        if not lines:
            return
        self.mainWindow.tabs["log"]["text"].logOffset += len(lines)
        for line in lines:
            self.mainWindow.tabs["log"]["text"].emit(SIGNAL("append(QString)"), line.strip("\n"))
        cursor = self.mainWindow.tabs["log"]["text"].textCursor()
        cursor.movePosition(QTextCursor.End, QTextCursor.MoveAnchor)
        self.mainWindow.tabs["log"]["text"].setTextCursor(cursor)

    def getConnections(self):
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
            data["type"] = conn.attribute("type", "remote")
            data["default"] = conn.attribute("default", "False")
            data["id"] = conn.attribute("id", uuid().hex)
            if data["default"] == "True":
                data["default"] = True
            else:
                data["default"] = False
            subs = self.parser.parseNode(conn, "dict")
            if not subs.has_key("name"):
                data["name"] = _("Unnamed")
            else:
                data["name"] = subs["name"].text()
            if data["type"] == "remote":
                if not subs.has_key("server"):
                    continue
                else:
                    data["host"] = subs["server"].text()
                    data["user"] = subs["server"].attribute("user", "admin")
                    data["port"] = int(subs["server"].attribute("port", "7227"))
                    data["password"] = subs["server"].attribute("password", "")
            ret.append(data)
        return ret

    def slotSaveConnection(self, data):
        """
            save connection to config file
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
        nameText = self.parser.xml.createTextNode(data["name"])
        nameNode.appendChild(nameText)
        connNode.appendChild(nameNode)
        if data["type"] == "remote":
            serverNode = self.parser.xml.createElement("server")
            serverNode.setAttribute("user", data["user"])
            serverNode.setAttribute("port", data["port"])
            serverNode.setAttribute("password", data["password"])
            hostText = self.parser.xml.createTextNode(data["host"])
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
        self.parser.saveData()
        self.refreshConnections()

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
        if data["type"] not in ("remote","internal"):

            coreparser = ConfigParser(self.configdir)
            if not coreparser.config:
                self.connector.setConnectionData("127.0.0.1", 7227, "anonymous", "anonymous", False)
            else:
                self.connector.setConnectionData("127.0.0.1", coreparser.get("remote","port"), "anonymous", "anonymous")

        elif data["type"] == "remote":
            self.connector.setConnectionData(data["host"], data["port"], data["user"], data["password"])

        elif data["type"] == "internal":
            from pyLoadCore import Core
            from module.ConfigParser import ConfigParser as CoreConfig
            import thread

            if not self.core:

                config = CoreConfig() #create so at least default config exists
                self.core = Core()
                self.core.startedInGui = True
                thread.start_new_thread(self.core.start, (False, False))
                while not self.core.running:
                    sleep(0.5)
                    
                self.connector.proxy = self.core.api
                self.connector.internal = True

                #self.connector.setConnectionData("127.0.0.1", config.get("remote","port"), "anonymous", "anonymous")
        
        self.startMain()
#        try:
#            host = data["host"]
#        except:
#            host = "127.0.0.1"

    def refreshConnections(self):
        """
            reload connetions and display them
        """
        self.parser.loadData()
        conns = self.getConnections()
        self.connWindow.emit(SIGNAL("setConnections"), conns)
        for conn in conns:
            if conn["default"]:
                return conn
        return None

    def slotSetDownloadStatus(self, status):
        """
            toolbar start/pause slot
        """
        if status:
            self.connector.unpauseServer()
        else:
            self.connector.pauseServer()

    def slotAddPackage(self, name, links, password=None):
        """
            emitted from main window
            add package to the collector
        """
        pack = self.connector.addPackage(name, links, Destination.Collector)
        if password:
            data = {"password": password}
            self.connector.setPackageData(pack, data)

    def slotAddFileToPackage(self, pid, fid): #TODO deprecated? gets called
        """
            emitted from collector view after a drop action
        """
        #self.connector.addFileToPackage(fid, pid)
        pass

    def slotAddContainer(self, path):
        """
            emitted from main window
            add container
        """
        filename = basename(path)
        #type = "".join(filename.split(".")[-1])
        fh = open(path, "r")
        content = fh.read()
        fh.close()
        self.connector.uploadContainer(filename, content)

    def slotSaveMainWindow(self, state, geo):
        """
            save the window geometry and toolbar/dock position to config file
        """
        mainWindowNode = self.parser.xml.elementsByTagName("mainWindow").item(0)
        if mainWindowNode.isNull():
            mainWindowNode = self.parser.xml.createElement("mainWindow")
            self.parser.root.appendChild(mainWindowNode)
        stateNode = mainWindowNode.toElement().elementsByTagName("state").item(0)
        geoNode = mainWindowNode.toElement().elementsByTagName("geometry").item(0)
        newStateNode = self.parser.xml.createTextNode(state)
        newGeoNode = self.parser.xml.createTextNode(geo)

        stateNode.removeChild(stateNode.firstChild())
        geoNode.removeChild(geoNode.firstChild())
        stateNode.appendChild(newStateNode)
        geoNode.appendChild(newGeoNode)

        self.parser.saveData()

    def restoreMainWindow(self):
        """
            load and restore main window geometry and toolbar/dock position from config
        """
        mainWindowNode = self.parser.xml.elementsByTagName("mainWindow").item(0)
        if mainWindowNode.isNull():
            return
        nodes = self.parser.parseNode(mainWindowNode, "dict")

        state = str(nodes["state"].text())
        geo = str(nodes["geometry"].text())

        self.mainWindow.restoreWindow(state, geo)
        self.mainWindow.captchaDock.hide()

    def slotPushPackageToQueue(self, id):
        """
            emitted from main window
            push the collector package to queue
        """
        self.connector.pushToQueue(id)

    def slotRestartDownload(self, id, isPack):
        """
            emitted from main window
            restart download
        """
        if isPack:
            self.connector.restartPackage(id)
        else:
            self.connector.restartFile(id)

    def slotRefreshStatus(self, id):
        """
            emitted from main window
            refresh download status
        """
        self.connector.recheckPackage(id)

    def slotRemoveDownload(self, id, isPack):
        """
            emitted from main window
            remove download
        """
        if isPack:
            self.connector.deletePackages([id])
        else:
            self.connector.deleteFiles([id])

    def slotAbortDownload(self, id, isPack):
        """
            emitted from main window
            remove download
        """
        if isPack:
            data = self.connector.getFileOrder(id) #less data to transmit
            self.connector.stopDownloads(data.values())
        else:
            self.connector.stopDownloads([id])

    def slotStopAllDownloads(self):
        """
            emitted from main window
            stop all running downloads
        """
        self.connector.stopAllDownloads()

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

            self.slotAddPackage(packagename, links)

    def slotSetClipboardStatus(self, status):
        """
            set clipboard checking
        """
        self.checkClipboard = status

    def slotChangePackageName(self, pid, name):
        """
            package name edit finished
        """
        self.connector.setPackageName(pid, str(name))

    def slotPullOutPackage(self, pid):
        """
            pull package out of the queue
        """
        self.connector.pullFromQueue(pid)

    def checkCaptcha(self):
        if self.connector.isCaptchaWaiting() and self.mainWindow.captchaDock.isFree():
            t = self.connector.getCaptchaTask(False)
            self.mainWindow.show()
            self.mainWindow.raise_()
            self.mainWindow.activateWindow()
            self.mainWindow.captchaDock.emit(SIGNAL("setTask"), t.tid, b64decode(t.data), t.type)
        elif not self.mainWindow.captchaDock.isFree():
            status = self.connector.getCaptchaTaskStatus(self.mainWindow.captchaDock.currentID)
            if not (status == "user" or status == "shared-user"):
                self.mainWindow.captchaDock.hide()
                self.mainWindow.captchaDock.processing = False
                self.mainWindow.captchaDock.currentID = None

    def slotCaptchaDone(self, cid, result):
        self.connector.setCaptchaResult(cid, str(result))

    def pullEvents(self):
        events = self.connector.getEvents(self.connector.connectionID)
        if not events:
            return
        for event in events:
            if event.eventname == "account":
                self.mainWindow.emit(SIGNAL("reloadAccounts"), False)
            elif event.eventname == "config":
                pass
            elif event.destination == Destination.Queue:
                self.queue.addEvent(event)
                try:
                    if event.eventname == "update" and event.type == ElementType.File:
                        info = self.connector.getFileData(event.id)
                        if info.statusmsg == "finished":
                            self.emit(SIGNAL("showMessage"), _("Finished downloading of '%s'") % info.name)
                        elif info.statusmsg == "failed":
                            self.emit(SIGNAL("showMessage"), _("Failed downloading '%s'!") % info.name)
                    if event.event == "insert" and event.type == ElementType.File:
                        info = self.connector.getLinkInfo(event[3])
                        self.emit(SIGNAL("showMessage"), _("Added '%s' to queue") % info.name)
                except:
                    print "can't send notification"
            elif event.destination == Destination.Collector:
                self.packageCollector.addEvent(event)

    def slotReloadAccounts(self, force=False):
        self.mainWindow.tabs["accounts"]["view"].model().reloadData(force)

    def slotQuit(self):
        self.tray.hide()
        self.quitInternal()
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
            m = QMessageBox(QMessageBox.Critical, _("Connection lost"), _("Lost connection to the core!"), QMessageBox.Ok)
            m.exec_()
            self.slotQuit()
    
    class Loop():
        def __init__(self, parent):
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
                self.parent.serverStatus["freespace"] = self.parent.connector.freeSpace()
            self.parent.refreshLog()
            self.parent.checkCaptcha()
            self.parent.pullEvents()

        def stop(self):
            self.timer.stop()


class TrayIcon(QSystemTrayIcon):
    def __init__(self):
        QSystemTrayIcon.__init__(self, QIcon(join(pypath, "icons", "logo-gui.png")))
        self.contextMenu = QMenu()
        self.showAction = QAction(_("Show"), self.contextMenu)
        self.showAction.setCheckable(True)
        self.showAction.setChecked(True)
        self.showAction.setDisabled(True)
        self.contextMenu.addAction(self.showAction)
        self.exitAction = QAction(QIcon(join(pypath, "icons", "close.png")), _("Exit"), self.contextMenu)
        self.contextMenu.addAction(self.exitAction)
        self.setContextMenu(self.contextMenu)

        self.connect(self, SIGNAL("activated(QSystemTrayIcon::ActivationReason)"), self.clicked)

    def mainWindowHidden(self):
        self.showAction.setChecked(False)

    def clicked(self, reason):
        if self.showAction.isEnabled():
            if reason == QSystemTrayIcon.Trigger:
                self.showAction.toggle()

class Notification(QObject):
    def __init__(self, tray):
        QObject.__init__(self)
        self.tray = tray
        self.usePynotify = False

        try:
            self.usePynotify = pynotify.init("icon-summary-body")
        except:
            print "init error"

    def showMessage(self, body):
        if self.usePynotify:
            n = pynotify.Notification("pyload", body, join(pypath, "icons", "logo.png"))
            try:
                n.set_hint_string("x-canonical-append", "")
            except:
                pass
            n.show()
        else:
            self.tray.showMessage("pyload", body)

if __name__ == "__main__":
    renameProcess('pyLoadGui')
    app = main()
    app.loop()

