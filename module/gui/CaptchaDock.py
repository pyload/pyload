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

import logging

class CaptchaDock(QDockWidget):
    """
        dock widget for captcha input
    """
    def __init__(self):
        QDockWidget.__init__(self, _("Captcha"))
        self.log = logging.getLogger("guilog")
        
        self.setObjectName("Captcha Dock")
        self.widget = CaptchaDockWidget(self)
        self.setWidget(self.widget)
        self.setAllowedAreas(Qt.BottomDockWidgetArea)
        #self.setFeatures(QDockWidget.NoDockWidgetFeatures)
        self.hide()
        self.processing = False
        self.currentID = None
        self.currentResultType = None
        self.connect(self, SIGNAL("setTask"), self.setTask)
    
    def isFree(self):
        return not self.processing
    
    def setTask(self, tid, data, type, resultType):
        self.processing = True
        self.currentID = tid
        self.currentResultType = resultType
        self.widget.emit(SIGNAL("setupCaptcha"), QByteArray(data), type)
        self.show()
    
    def closeEvent(self, event):
        self.hide()
        event.ignore()

class CaptchaDockWidget(QWidget):
    """
        widget for the input widgets
    """
    def __init__(self, dock):
        QWidget.__init__(self)
        self.log = logging.getLogger("guilog")
        self.dock = dock
        
        self.imgData       = None
        self.imgDataBuffer = None
        self.imgAnimation  = None
        
        self.setLayout(QHBoxLayout())
        layout = self.layout()
        
        self.imgLabel = QLabel()
        self.infoLabel = QLabel()
        self.lineEdit = QLineEdit()
        self.okayButton = QPushButton(_("OK"))
        
        layout.addStretch()
        layout.addWidget(self.imgLabel)
        layout.addWidget(self.infoLabel)
        layout.addWidget(self.lineEdit)
        layout.addWidget(self.okayButton)
        layout.addStretch()
        
        self.connect(self.okayButton, SIGNAL("clicked()"), self.slotSubmitText)
        self.connect(self.lineEdit, SIGNAL("returnPressed()"), self.slotSubmitText)
        self.imgLabel.mousePressEvent = self.slotSubmitPos
        self.connect(self, SIGNAL("setupCaptcha"), self.setupCaptcha)
        self.connect(self, SIGNAL("setMovie(QMovie *)"), self.imgLabel, SLOT("setMovie(QMovie *)"))
    
    def setupCaptcha(self, data, type):
        self.lineEdit.setText("")
        self.infoLabel.setText("")
        errMsg = None
        
        if self.imgAnimation != None and self.imgAnimation.isValid():
            self.imgAnimation.stop()
        if self.imgDataBuffer != None and self.imgDataBuffer.isOpen():
            self.imgDataBuffer.close()
        
        self.imgData = data
        self.imgDataBuffer = QBuffer(self.imgData)
        if self.imgDataBuffer.open(QIODevice.ReadOnly):
            self.imgAnimation = QMovie()
            self.imgAnimation.setCacheMode(QMovie.CacheAll)
            self.imgAnimation.setDevice(self.imgDataBuffer)
            if self.imgAnimation.isValid():
                self.emit(SIGNAL("setMovie(QMovie *)"), self.imgAnimation)
                self.imgAnimation.start()
                if self.dock.currentResultType == "textual":
                    self.infoLabel.hide()
                    self.lineEdit.show()
                    self.okayButton.show()
                    self.lineEdit.setFocus(Qt.OtherFocusReason)
                    self.imgLabel.unsetCursor()
                elif self.dock.currentResultType == "positional":
                    self.infoLabel.setText("Click on the image")
                    self.infoLabel.show()
                    self.lineEdit.hide()
                    self.okayButton.hide()
                    self.imgLabel.setCursor(Qt.CrossCursor)
                else:
                    errMsg = "setupCaptcha: Unknown resultType '" + str(self.dock.currentResultType) + "'"
                    self.imgAnimation.stop()
                    self.imgDataBuffer.close()
            else:
                self.imgDataBuffer.close()
                errMsg = "setupCaptcha: Could not load the captcha image (2)"
        else:
            self.imgDataBuffer.close()
            errMsg = "setupCaptcha: Could not load the captcha image (1)"
        
        if errMsg != None:
            self.log.error(errMsg)
            self.emit(SIGNAL("setMovie(QMovie *)"), QMovie())
            self.infoLabel.setText("*** ERROR ***")
            self.infoLabel.show()
            self.lineEdit.hide()
            self.okayButton.show()
    
    def slotSubmitText(self):
        text = str(self.lineEdit.text())
        tid = self.dock.currentID
        self.dock.currentID = None
        self.dock.currentResultType = None
        self.dock.emit(SIGNAL("done"), tid, text)
        self.dock.hide()
        self.dock.processing = False
    
    def slotSubmitPos(self, event):
        if self.dock.currentResultType == "positional":
            x = event.pos().x()
            y = event.pos().y()
            p = str(x) + ',' + str(y)
            tid = self.dock.currentID
            self.dock.currentID = None
            self.dock.currentResultType = None
            self.dock.emit(SIGNAL("done"), tid, p)
            self.dock.hide()
            self.dock.processing = False
