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

SERVER_VERSION = "0.4.20"

from time import sleep
from uuid import uuid4 as uuid

from module.gui import USE_QT5
if USE_QT5:
    from PyQt5.QtGui import *
    from PyQt5.QtCore import *
    from PyQt5.QtWidgets import *
else:
    from PyQt4.QtCore import pyqtSignal, QMutex, QObject, Qt
    from PyQt4.QtGui import QDialog, QDialogButtonBox, QGridLayout, QIcon, QLabel, QLineEdit

import logging
import socket
from os.path import join

from module.remote.thriftbackend.ThriftClient import ThriftClient, WrongLogin, NoSSL, NoConnection
from thrift.Thrift import TException
from module.gui.Tools import MessageBox, WtDialogButtonBox

class Connector(QObject):
    """
        manages the connection to the pyload core via thrift
    """
    connectTimeoutSGL = pyqtSignal(object)
    msgBoxErrorSGL    = pyqtSignal(object)
    connectionLostSGL = pyqtSignal()

    def __init__(self, firstAttempt):
        QObject.__init__(self)
        self.firstAttempt = firstAttempt
        self.log = logging.getLogger("guilog")

        self.mutex = QMutex()
        self.connectionID = None
        self.host = None
        self.port = None
        self.user = None
        self.password = None
        self.ssl = None
        self.running = True
        self.internal = False
        self.pwBox = AskForUserAndPassword()
        self.proxy = self.Dummy()

    def setConnectionData(self, host, port, user, password):
        """
            set connection data for connection attempt, called from slotConnect
        """
        self.host     = host
        self.port     = port
        self.user     = user
        self.password = password

    def connectProxy(self):
        """
            initialize thrift rpc client,
            check for ssl, check auth,
            setup dispatcher,
            connect error signals,
            check server version
        """
        self.timeoutTimerStart()
        firstAttempt = self.firstAttempt
        self.firstAttempt = False

        if self.internal:
            return True
        if not self.host:
            return False

        # Quick test if the host responds, we probably do not want to wait until the default socket timeout kicks in (120sec)
        soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        soc.settimeout(5) #seconds
        gaierror = False
        timeout = False
        try:
            soc.connect((self.host, self.port))
        except socket.gaierror:
            gaierror = True
        except socket.timeout:
            timeout = True
        except Exception:
            self.log.debug9("Connector.connectProxy: Quick test: Failed to connect to the server for whatever reason")
        try:
            soc.shutdown(socket.SHUT_RD)
        except Exception:
            self.log.debug9("Connector.connectProxy: Quick test: Failed to shut down the read side of the server connection socket. Don't worry about it!")
        try:
            soc.shutdown(socket.SHUT_WR)
        except Exception:
            self.log.debug9("Connector.connectProxy: Quick test: Failed to shut down the write side of the server connection socket. Don't worry about it!")
        soc.close()
        if gaierror:
            if firstAttempt:
                return False
            self.messageBox_01(self.host, self.port)
            return False
        if timeout:
            if firstAttempt:
                return False
            if not self.messageBox_02(self.host, self.port):
                return False
            else:
                self.timeoutTimerStart()
        # login
        while True:
            err = None
            errlogin = False
            try:
                client = ThriftClient(self.host, self.port, self.user, self.password)
            except WrongLogin:
                errlogin = True
            except NoSSL:
                err = "nossl"
            except NoConnection:
                err = "noconn"

            if not errlogin:
                break

            # user and password popup
            if self.messageBox_03(self.host, self.port, self.user, self.password) == QDialog.Rejected:
                return False
            else:
                self.timeoutTimerStart()
            self.user = unicode(self.pwBox.userLE.text())
            self.password = unicode(self.pwBox.passwordLE.text())
            sleep(1) # some delay to let the dialog fade out

        if err is not None:
            if firstAttempt:
                return False
            if err == "nossl":
                self.messageBox_04(self.host, self.port)
            elif err == "noconn":
                self.messageBox_05(self.host, self.port)
            return False

        self.ssl = client.isSSLConnection() # remember if we are connected with SSL
        self.proxy = DispatchRPC(self.mutex, client)
        self.proxy.connectionLostSGL.connect(self.connectionLostSGL)

        # check server version
        server_version = self.proxy.getServerVersion()
        self.connectionID = uuid().hex
        if not server_version == SERVER_VERSION:
            if firstAttempt:
                return False
            self.messageBox_06(server_version, self.host, self.port)
            return False

        return True

    def isSSLConnection(self):
        if self.internal:
            return False
        return self.ssl

    def getOurUserData(self):
        return self.proxy.getUserData(self.user, self.password)

    def disconnectProxy(self):
        """
            close the sockets
        """
        if self.internal:
            return
        self.proxy.server.close()
        self.proxy = self.Dummy()

    def timeoutTimerStart(self):
        self.connectTimeoutSGL.emit(True)

    def timeoutTimerStop(self):
        self.connectTimeoutSGL.emit(False)

    def messageBox_01(self, host, port):
        self.timeoutTimerStop()
        err = _("Invalid hostname or address:")
        err += "\n" + host + ":" + str(port)
        self.msgBoxErrorSGL.emit(err)

    def messageBox_02(self, host, port):
        self.timeoutTimerStop()
        err = _("No response from host:")
        err += "\n" + host + ":" + str(port)
        err += "\n\n" + _("Wait longer?")
        msgb = MessageBox(None, err, "Q", "YES_NO")
        return msgb.exec_()

    def messageBox_03(self, host, port, user, password):
        self.timeoutTimerStop()
        pwboxtxt = _("Please enter correct login credentials for host:")
        pwboxtxt += "\n" + host + ":" + str(port)
        self.pwBox.textLabel.setText(pwboxtxt)
        self.pwBox.userLE.setText(user)
        self.pwBox.passwordLE.setText(password)
        return self.pwBox.exec_()

    def messageBox_04(self, host, port):
        self.timeoutTimerStop()
        err = _("No SSL support to connect to host:")
        err += "\n" + host + ":" + str(port)
        self.msgBoxErrorSGL.emit(err)

    def messageBox_05(self, host, port):
        self.timeoutTimerStop()
        err = _("Cannot connect to host:")
        err += "\n" + host + ":" + str(port)
        self.msgBoxErrorSGL.emit(err)

    def messageBox_06(self, server_version, host, port):
        self.timeoutTimerStop()
        err = _("Cannot connect to server:")
        err += "\n" + host + ":" + str(port)
        err += "\n" + (_("Server version is %s") % server_version) + ", " + _("but we need version %s") % SERVER_VERSION
        self.msgBoxErrorSGL.emit(err)

    def __getattr__(self, attr):
        """
            redirect rpc calls to dispatcher
        """
        return getattr(self.proxy, attr)

    class Dummy(object):
        """
            dummy rpc proxy, to prevent errors
        """
        def __nonzero__(self):
            return False

        def __getattr__(self, attr):
            def dummy(*args, **kwargs):
                return None
            return dummy

class AskForUserAndPassword(QDialog):
    """
        user and password popup
    """
    def __init__(self):
        QDialog.__init__(self)
        self.log = logging.getLogger("guilog")

        self.lastFont = None

        self.setAttribute(Qt.WA_DeleteOnClose, False)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setWindowTitle(_("pyLoad Client"))
        self.setWindowIcon(QIcon(join(pypath, "icons", "logo.png")))

        grid = QGridLayout()

        self.textLabel = QLabel()
        userLabel = QLabel(_("User") + ":")
        self.userLE = QLineEdit()
        pwLabel = QLabel(_("Password") + ":")
        self.passwordLE = QLineEdit()
        self.passwordLE.setEchoMode(QLineEdit.Password)
        self.buttons = WtDialogButtonBox(Qt.Horizontal)
        self.buttons.hideWhatsThisButton()
        self.okBtn = self.buttons.addButton(QDialogButtonBox.Ok)
        self.okBtn.setText(_("OK"))
        self.cancelBtn = self.buttons.addButton(QDialogButtonBox.Cancel)
        self.cancelBtn.setText(_("Cancel"))

        grid.addWidget(self.textLabel,        0, 0, 1, 2)
        grid.setRowMinimumHeight(1, 7)
        grid.addWidget(userLabel,             2, 0)
        grid.addWidget(self.userLE,           2, 1)
        grid.addWidget(pwLabel,               3, 0)
        grid.addWidget(self.passwordLE,       3, 1)
        grid.setRowMinimumHeight(4, 7)
        grid.setRowStretch(4, 1)
        grid.addLayout(self.buttons.layout(), 5, 0, 1, 2)
        self.setLayout(grid)

        self.setMinimumWidth(300)
        self.adjustSize()
        #self.setFixedHeight(self.height())

        self.okBtn.clicked.connect(self.accept)
        self.cancelBtn.clicked.connect(self.reject)

    def exec_(self):
        # It does not resize very well when the font size has changed
        if self.font() != self.lastFont:
            self.lastFont = self.font()
            self.adjustSize()
        return QDialog.exec_(self)

    def appFontChanged(self):
        self.buttons.updateWhatsThisButton()

class DispatchRPC(QObject):
    """
        wraps the thrift client, to catch critical exceptions (connection lost)
        adds thread safety
    """

    def __init__(self, mutex, server):
        QObject.__init__(self)
        self.log = logging.getLogger("guilog")
        self.mutex = mutex
        self.server = server

    def __getattr__(self, attr):
        """
            redirect and wrap call in Wrapper instance, locks dispatcher
        """
        self.mutex.lock()
        self.fname = attr
        f = self.Wrapper(getattr(self.server, attr), self.mutex, self)
        return f

    class Wrapper(object):
        """
            represents a rpc call
        """
        connectionLostSGL = pyqtSignal()

        def __init__(self, f, mutex, dispatcher):
            self.f = f
            self.mutex = mutex
            self.dispatcher = dispatcher

        def __call__(self, *args, **kwargs):
            """
                instance is called, rpc is executed
                exceptions are processed
                finally dispatcher is unlocked
            """
            lost = False
            try:
                return self.f(*args, **kwargs)
            except socket.error: #necessary?
                lost = True
            except TException:
                lost = True
            finally:
                self.mutex.unlock()
            if lost:
                from traceback import print_exc
                print_exc()
                self.dispatcher.connectionLostSGL.emit()
