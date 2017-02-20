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

class CaptchaDock(QDockWidget):
    """
        dock widget for captcha input
    """
    
    def __init__(self):
        QDockWidget.__init__(self, _("Captcha"))
        self.setObjectName("Captcha Dock")
        self.widget = CaptchaDockWidget(self)
        self.setWidget(self.widget)
        self.setAllowedAreas(Qt.BottomDockWidgetArea)
        self.setFeatures(QDockWidget.NoDockWidgetFeatures)
        self.hide()
        self.processing = False
        self.currentID = None
        self.connect(self, SIGNAL("setTask"), self.setTask)
    
    def isFree(self):
        return not self.processing
    
    def setTask(self, tid, img, imgType):
        self.processing = True
        data = QByteArray(img)
        self.currentID = tid
        self.widget.emit(SIGNAL("setImage"), data)
        self.widget.input.setText("")
        self.show()

class CaptchaDockWidget(QWidget):
    """
        widget for the input widgets
    """
    
    def __init__(self, dock):
        QWidget.__init__(self)
        self.dock = dock
        self.setLayout(QHBoxLayout())
        layout = self.layout()
        
        imgLabel = QLabel()
        captchaInput = QLineEdit()
        okayButton = QPushButton(_("OK"))
        cancelButton = QPushButton(_("Cancel"))
        
        layout.addStretch()
        layout.addWidget(imgLabel)
        layout.addWidget(captchaInput)
        layout.addWidget(okayButton)
        layout.addWidget(cancelButton)
        layout.addStretch()
        
        self.input = captchaInput
        
        self.connect(okayButton, SIGNAL("clicked()"), self.slotSubmit)
        self.connect(captchaInput, SIGNAL("returnPressed()"), self.slotSubmit)
        self.connect(self, SIGNAL("setImage"), self.setImg)
        self.connect(self, SIGNAL("setPixmap(const QPixmap &)"), imgLabel, SLOT("setPixmap(const QPixmap &)"))
    
    def setImg(self, data):
        pixmap = QPixmap()
        pixmap.loadFromData(data)
        self.emit(SIGNAL("setPixmap(const QPixmap &)"), pixmap)
        self.input.setFocus(Qt.OtherFocusReason)
    
    def slotSubmit(self):
        text = self.input.text()
        tid = self.dock.currentID
        self.dock.currentID = None
        self.dock.emit(SIGNAL("done"), tid, str(text))
        self.dock.hide()
        self.dock.processing = False

