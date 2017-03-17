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
from os.path import join

class CaptchaDialog(QDialog):
    """
        captcha dialog
    """
    def __init__(self):
        QDialog.__init__(self)
        self.log = logging.getLogger("guilog")

        self.geo     = None
        self.adjSize = None

        self.processing        = False
        self.currentID         = None
        self.currentResultType = None
        self.imgData           = None
        self.imgDataBuffer     = None
        self.imgAnimation      = None

        #self.setModal(True)
        self.setAttribute(Qt.WA_DeleteOnClose, False)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setWindowTitle(_("Captcha"))
        self.setWindowIcon(QIcon(join(pypath, "icons", "logo.png")))

        self.imgLabel  = QLabel()
        self.infoLabel = QLabel()
        self.infoLabel.setAlignment(Qt.AlignCenter)
        self.lineEdit  = QLineEdit()

        self.buttons = QDialogButtonBox(Qt.Horizontal, self)
        self.submitBtn = self.buttons.addButton(QDialogButtonBox.Ok)
        self.ignoreBtn = self.buttons.addButton(QDialogButtonBox.Ignore)
        self.buttons.button(QDialogButtonBox.Ok).setText(_("Submit"))
        self.buttons.button(QDialogButtonBox.Ignore).setText(_("Ignore"))

        hbox = QHBoxLayout()
        hbox.addStretch()
        hbox.addWidget(self.imgLabel)
        hbox.addStretch()
        vbox = QVBoxLayout()
        vbox.addLayout(hbox)
        vbox.addWidget(self.infoLabel)
        vbox.addWidget(self.lineEdit)
        vbox.addSpacing(7)
        vbox.addStretch()
        vbox.addWidget(self.buttons)
        self.setLayout(vbox)

        self.connect(self.submitBtn, SIGNAL("clicked()"),       self.slotSubmitText)
        self.connect(self.lineEdit,  SIGNAL("returnPressed()"), self.slotSubmitText)
        self.connect(self.ignoreBtn, SIGNAL("clicked()"), self.ignore)
        self.imgLabel.mousePressEvent = self.slotSubmitPos

        self.connect(self, SIGNAL("setTask"), self.setTask)
        self.connect(self, SIGNAL("setMovie(QMovie *)"), self.imgLabel, SLOT("setMovie(QMovie *)"))
        self.connect(self, SIGNAL("show"), self.slotShow)
        self.connect(self, SIGNAL("setFree"), self.setFree)

        self.setMinimumWidth(250)

    def isFree(self):
        return not self.processing

    def setTask(self, tid, data, type, resultType):
        self.processing = True
        self.currentID = tid
        self.currentResultType = resultType

        self.lineEdit.setText("")
        self.infoLabel.setText("")
        errMsg = None

        if self.imgAnimation != None and self.imgAnimation.isValid():
            self.imgAnimation.stop()
        if self.imgDataBuffer != None and self.imgDataBuffer.isOpen():
            self.imgDataBuffer.close()

        self.imgData = QByteArray(data)
        self.imgDataBuffer = QBuffer(self.imgData)
        if self.imgDataBuffer.open(QIODevice.ReadOnly):
            self.imgAnimation = QMovie()
            self.imgAnimation.setCacheMode(QMovie.CacheAll)
            self.imgAnimation.setDevice(self.imgDataBuffer)
            if self.imgAnimation.isValid():
                self.emit(SIGNAL("setMovie(QMovie *)"), self.imgAnimation)
                self.imgAnimation.start()
                if self.currentResultType == "textual":
                    self.infoLabel.hide()
                    self.lineEdit.show()
                    self.submitBtn.show()
                    self.imgLabel.unsetCursor()
                elif self.currentResultType == "positional":
                    self.infoLabel.setText("Click on the image")
                    self.infoLabel.show()
                    self.lineEdit.hide()
                    self.submitBtn.hide()
                    self.imgLabel.setCursor(Qt.CrossCursor)
                else:
                    errMsg = "setupCaptcha: Unknown resultType '" + unicode(self.currentResultType) + "'"
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
            self.submitBtn.hide()

        self.slotShow()

    def setFree(self):
        self.currentID = None
        self.currentResultType = None
        self.hide()
        self.processing = False

    def setupNoCaptcha(self):
        pix = QApplication.style().standardIcon(QStyle.SP_MessageBoxInformation).pixmap(64, 64)
        self.imgLabel.setPixmap(pix)
        self.imgLabel.show()
        self.infoLabel.setText("<b>" + _("There is no captcha waiting.") + "</b>")
        self.infoLabel.show()
        self.lineEdit.hide()
        self.submitBtn.hide()
        self.imgLabel.unsetCursor()

    def slotShow(self):
        if self.isFree():
            self.setupNoCaptcha()
        self.restoreGeometry(self.geo)
        self.show()
        if self.adjSize:
            self.adjustSize()
        self.submitBtn.setFocus(Qt.OtherFocusReason)
        self.raise_()
        self.activateWindow()

    def slotSubmitText(self):
        text = unicode(self.lineEdit.text())
        if not text: # empty string, ignored by api or core
            return
        tid = self.currentID
        self.currentID = None
        self.currentResultType = None
        self.emit(SIGNAL("done"), tid, text)
        self.hide()
        self.processing = False

    def slotSubmitPos(self, event):
        if self.currentResultType == "positional":
            x = event.pos().x()
            y = event.pos().y()
            p = str(x) + ',' + str(y)
            tid = self.currentID
            self.currentID = None
            self.currentResultType = None
            self.emit(SIGNAL("done"), tid, p)
            self.hide()
            self.processing = False

    def ignore(self):
        self.hide()

    def closeEvent(self, event):
        self.hide()
        event.ignore()

    def hide(self):
        if not self.isHidden():
            self.geo = self.saveGeometry()
        QDialog.hide(self)

