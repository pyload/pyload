# -*- coding: utf-8 -*-

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from os.path import join
import logging

def whatsThisFormat(title, text):
    #html = "<b>" + title + "</b><br><br>" + text
    html = "<table><tr><td><b>" + title + "</b></td></tr></table>" + "<table><tr><td>" + text + "</td></tr></table>"
    return html

class WhatsThisButton(QPushButton):
    def __init__(self, text="?"):
        QPushButton.__init__(self, text)
        self.text = text
        self.setDefault(False)
        self.setAutoDefault(False)
        self.setFocusPolicy(Qt.NoFocus)
        self.updateSize()
        self.connect(self, SIGNAL("clicked()"), QWhatsThis.enterWhatsThisMode)

    def updateSize(self):
        width  = self.fontMetrics().boundingRect(self.text).width()
        height = self.fontMetrics().boundingRect(self.text).height()
        s = width
        if height > s:
            s = height
        s += 4  # border
        self.setFixedSize(s, s)

class WtDialogButtonBox(QDialogButtonBox):
    def __init__(self, orientation=Qt.Horizontal, parent=None):
        QDialogButtonBox.__init__(self, orientation, parent)
        self.wtBtn = WhatsThisButton()
        self.l = QHBoxLayout()
        self.l.setContentsMargins(0, 0, 0, 0)
        self.l.setSpacing(0)
        self.l.addWidget(self.wtBtn)
        self.spacer = QSpacerItem(self.wtBtn.width(), self.wtBtn.width())
        self.l.addSpacerItem(self.spacer)
        self.l.addWidget(self)

    def layout(self):
        return self.l

    def hideWhatsThisButton(self, hide=True):
        self.wtBtn.setHidden(hide)
        if hide:
            self.spacer.changeSize(0, 0)
        else:
            self.spacer.changeSize(self.wtBtn.width(), self.wtBtn.width())

    def updateWhatsThisButton(self):
        if not self.wtBtn.isHidden():
            self.wtBtn.updateSize()
            self.spacer.changeSize(self.wtBtn.width(), self.wtBtn.width())

class LineView(QLineEdit):
    def __init__(self, contents=""):
        QLineEdit.__init__(self, contents)
        # read-only
        self.setReadOnly(True)
        # set background color
        self.pal = QPalette(self.palette())
        newcolor = QColor(QLabel().palette().color(QPalette.Active, QLabel().backgroundRole()))
        self.pal.setColor(QPalette.Active, self.backgroundRole(), newcolor)
        self.pal.setColor(QPalette.Inactive, self.backgroundRole(), newcolor)
        self.setPalette(self.pal)
        # remove from taborder
        self.setFocusPolicy(Qt.NoFocus)
        # prohibit text selection
        self.connect(self, SIGNAL("selectionChanged()"), self.deselect)
        # disable context menu
        self.setContextMenuPolicy(Qt.NoContextMenu)

class MessageBox(QDialog):
    """
        icon:               btnSet:
          N NoIcon            OK
          Q Question          OK_CANCEL
          I Information       YES_NO
          W Warning
          C Critical
    """

    def __init__(self, parent, text, icon, btnSet, noTranslation=False):
        QDialog.__init__(self, parent)
        self.log = logging.getLogger("guilog")

        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setWindowIcon(QIcon(join(pypath, "icons", "logo.png")))
        self.setContentsMargins(9, 9, 9, 9)

        if noTranslation:
            self.log.debug8("MessageBox.__init__: without language translation")
            global _; _ = unicode   # language translation dummy

        # icon and window title
        title = _("pyLoad Client")
        self.iconLabel = QLabel()
        tmpIcon = QIcon()
        style = QApplication.style()
        iconSize = style.pixelMetric(QStyle.PM_MessageBoxIconSize, None, self)
        if icon == "Q":
            tmpIcon = style.standardIcon(QStyle.SP_MessageBoxQuestion, None, self)
        elif icon == "I":
            tmpIcon = style.standardIcon(QStyle.SP_MessageBoxInformation, None, self)
        elif icon == "W":
            tmpIcon = style.standardIcon(QStyle.SP_MessageBoxWarning, None, self)
            title += " - " + _("Warning")
        elif icon == "C":
            tmpIcon = style.standardIcon(QStyle.SP_MessageBoxCritical, None, self)
            title += " - " + _("Error")
        withIcon = not tmpIcon.isNull()
        if withIcon:
            self.iconLabel.setPixmap(tmpIcon.pixmap(iconSize, iconSize))
            self.iconLabel.adjustSize()
            self.iconLabel.setFixedSize(self.iconLabel.size())
        else:
            self.iconLabel.setFixedSize(0, 0)
        self.setWindowTitle(title)

        # constants
        minWidth = 320  # minimum dialog width
        maxWidth = 1000 # maximum dialog width
        addWidth = 20   # extra width
        icon_x = 0
        icon_y = 0
        text_x = 13
        if not withIcon:
            text_x += 7
        text_y = 0
        buttonBox_v_spacer = 10

        # QTextEdit
        self.textEdit = QTextEdit()
        self.textEdit.setReadOnly(True)                                             # read-only
        self.textEditPal = QPalette(self.textEdit.palette())
        newcolor = QColor(QLabel().palette().color(QPalette.Active, QLabel().backgroundRole()))
        self.textEditPal.setColor(QPalette.Base, newcolor)
        self.textEdit.setPalette(self.textEditPal)                                  # set background color
        self.textEdit.setFocusPolicy(Qt.NoFocus)                                    # remove from taborder
        self.textEdit.setTextInteractionFlags(Qt.NoTextInteraction)                 # prohibit text selection
        self.textEdit.setContextMenuPolicy(Qt.NoContextMenu)                        # disable context menu
        self.textEdit.setFrameStyle(QFrame.NoFrame)                                 # remove frame
        self.textEdit.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)             # no vertical scrollbar
        self.textEdit.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)           # no horizontal scrollbar
        self.textEdit.setLineWrapMode(QTextEdit.NoWrap)
        self.textEdit.setText(text)
        self.textEdit.setFixedWidth(self.textEdit.document().size().width() + self.textEdit.contentsMargins().left() + self.textEdit.contentsMargins().right())
        self.textEdit.setFixedHeight(self.textEdit.document().size().height() + self.textEdit.contentsMargins().top() + self.textEdit.contentsMargins().bottom())

        # buttons
        self.buttonBox = QDialogButtonBox()
        if btnSet == "OK":
            self.okBtn = self.buttonBox.addButton(QDialogButtonBox.Ok)
            self.buttonBox.button(QDialogButtonBox.Ok).setText(_("OK"))
            self.connect(self.okBtn, SIGNAL("clicked()"), self.accept)
        elif btnSet == "OK_CANCEL":
            self.okBtn     = self.buttonBox.addButton(QDialogButtonBox.Ok)
            self.cancelBtn = self.buttonBox.addButton(QDialogButtonBox.Cancel)
            self.buttonBox.button(QDialogButtonBox.Ok).    setText(_("OK"))
            self.buttonBox.button(QDialogButtonBox.Cancel).setText(_("Cancel"))
            self.connect(self.okBtn,     SIGNAL("clicked()"), self.accept)
            self.connect(self.cancelBtn, SIGNAL("clicked()"), self.reject)
        elif btnSet == "YES_NO":
            self.yesBtn = self.buttonBox.addButton(QDialogButtonBox.Yes)
            self.noBtn  = self.buttonBox.addButton(QDialogButtonBox.No)
            self.buttonBox.button(QDialogButtonBox.Yes).setText(_("Yes"))
            self.buttonBox.button(QDialogButtonBox.No). setText(_("No"))
            self.connect(self.yesBtn, SIGNAL("clicked()"), self.accept)
            self.connect(self.noBtn,  SIGNAL("clicked()"), self.reject)

        # layout
        vboxIcon = QVBoxLayout()
        vboxIcon.setSpacing(0)
        vboxIcon.setMargin(0)
        vboxIcon.addStretch(1)
        vboxIcon.addWidget(self.iconLabel)
        self.grid = QGridLayout()
        self.grid.setSpacing(0)
        self.grid.setMargin(0)
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.grid.setColumnMinimumWidth(0, icon_x)
        self.grid.setRowMinimumHeight(0, icon_y)
        self.grid.addLayout(vboxIcon, 1, 1, 2, 1)
        self.grid.addWidget(self.textEdit, 2, 3, 2, 2)
        self.grid.setRowStretch(3, 1)
        self.grid.setColumnStretch(4, 1)
        self.grid.setColumnMinimumWidth(2, text_x)
        self.grid.setRowMinimumHeight(2, self.iconLabel.height() - text_y) # label 64x64
        self.grid.setRowMinimumHeight(4, buttonBox_v_spacer)
        self.grid.addWidget(self.buttonBox, 5, 3, 1, 5)
        self.setLayout(self.grid)

        # cosmetic widening
        self.adjustSize()
        if (self.width() + addWidth) > minWidth:
            self.setMinimumWidth(self.width() + addWidth)
            self.log.debug8("MessageBox.__init__: addWidth applied")
        else:
            self.setMinimumWidth(minWidth)
            self.log.debug8("MessageBox.__init__: minWidth applied")

        # line wrap
        if self.width() > maxWidth:
            self.textEdit.setFixedWidth(self.textEdit.width() - (self.width() - maxWidth))
            self.setFixedWidth(maxWidth)
            self.textEdit.setMinimumHeight(0)
            self.textEdit.setMaximumHeight(100000)
            self.textEdit.setLineWrapMode(QTextEdit.WidgetWidth)
            self.textEdit.clear()
            self.textEdit.setText(text) # setText again to update the document geometry
            self.textEdit.setFixedHeight(self.textEdit.document().size().height() + self.textEdit.contentsMargins().top() + self.textEdit.contentsMargins().bottom())
            self.log.debug8("MessageBox.__init__: maxWidth exceeded, using line wrap mode")

        self.adjustSize()
        self.setFixedSize(self.size())  # disallow resizing/maximizing

        if noTranslation:
            del _ # delete language translation dummy

    def exec_(self):
        d = QDialog.exec_(self)
        retval = True if d == QDialog.Accepted else False
        return retval
