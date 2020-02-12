# -*- coding: utf-8 -*-

from PyQt4.QtCore import QByteArray, QObject, Qt, QTimer, SIGNAL
from PyQt4.QtGui import (QAbstractSpinBox, QApplication, QColor, QDialog, QDialogButtonBox, QFrame, QGridLayout, QHBoxLayout, QIcon,
                         QLabel, QLineEdit, QPalette, QPixmap, QPlainTextEdit, QPushButton, QSpacerItem, QSpinBox, QStyle,
                         QTextCursor, QTextEdit, QVBoxLayout, QWhatsThis)

from os.path import join
from bisect import bisect_left, bisect_right
from functools import cmp_to_key
from datetime import datetime
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

class PlainTextEdit(QPlainTextEdit):
    def __init__(self):
        QPlainTextEdit.__init__(self)
        self.setMinimumHeight(30)
        self.append = True

    def slotAppendToggled(self, status):
        self.append = status

    def addText(self, text):
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.End, QTextCursor.MoveAnchor)
        self.setTextCursor(cursor)
        lineLength = cursor.block().length() - 1
        if lineLength > 0:
            self.insertPlainText("\n")
        self.insertPlainText(text)

    def insertFromMimeData(self, source):
        cursor = self.textCursor()
        if self.append:
            cursor.movePosition(QTextCursor.End, QTextCursor.MoveAnchor)
            self.setTextCursor(cursor)
            lineLength = cursor.block().length() - 1
            if lineLength > 0:
                self.insertPlainText("\n")
        QPlainTextEdit.insertFromMimeData(self, source)
        if self.append:
            self.insertPlainText("\n")

class SpinBox(QSpinBox):
    """
        - Cancel edit and lose focus when the ESC key is pressed
        - Lose focus when the RETURN or the ENTER key is pressed
    """
    def __init__(self):
        QSpinBox.__init__(self)
        self.log = logging.getLogger("guilog")

    def focusInEvent(self, event):
        self.lastValue = self.value()
        QAbstractSpinBox.focusInEvent(self, event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.setValue(self.lastValue)
            self.clearFocus()
        elif event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
                self.clearFocus()
        QAbstractSpinBox.keyPressEvent(self, event)

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

        # icon and window title
        if noTranslation:
            title = unicode("pyLoad Client")
        else:
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
            if noTranslation:
                title += " - " + unicode("Warning")
            else:
                title += " - " + _("Warning")
        elif icon == "C":
            tmpIcon = style.standardIcon(QStyle.SP_MessageBoxCritical, None, self)
            if noTranslation:
                title += " - " + unicode("Error")
            else:
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
        self.textEdit.setFixedWidth(self.textEdit.document().size().width() + self.textEdit.contentsMargins().left() +
                                    self.textEdit.contentsMargins().right())
        self.textEdit.setFixedHeight(self.textEdit.document().size().height() + self.textEdit.contentsMargins().top() +
                                     self.textEdit.contentsMargins().bottom())

        # buttons
        self.buttonBox = QDialogButtonBox()
        if btnSet == "OK":
            self.okBtn = self.buttonBox.addButton(QDialogButtonBox.Ok)
            if noTranslation:
                self.buttonBox.button(QDialogButtonBox.Ok).setText(unicode("OK"))
            else:
                self.buttonBox.button(QDialogButtonBox.Ok).setText(_("OK"))
            self.connect(self.okBtn, SIGNAL("clicked()"), self.accept)
        elif btnSet == "OK_CANCEL":
            self.okBtn     = self.buttonBox.addButton(QDialogButtonBox.Ok)
            self.cancelBtn = self.buttonBox.addButton(QDialogButtonBox.Cancel)
            if noTranslation:
                self.buttonBox.button(QDialogButtonBox.Ok).    setText(unicode("OK"))
                self.buttonBox.button(QDialogButtonBox.Cancel).setText(unicode("Cancel"))
            else:
                self.buttonBox.button(QDialogButtonBox.Ok).    setText(_("OK"))
                self.buttonBox.button(QDialogButtonBox.Cancel).setText(_("Cancel"))
            self.connect(self.okBtn,     SIGNAL("clicked()"), self.accept)
            self.connect(self.cancelBtn, SIGNAL("clicked()"), self.reject)
        elif btnSet == "YES_NO":
            self.yesBtn = self.buttonBox.addButton(QDialogButtonBox.Yes)
            self.noBtn  = self.buttonBox.addButton(QDialogButtonBox.No)
            if noTranslation:
                self.buttonBox.button(QDialogButtonBox.Yes).setText(unicode("Yes"))
                self.buttonBox.button(QDialogButtonBox.No). setText(unicode("No"))
            else:
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
            self.textEdit.setFixedHeight(self.textEdit.document().size().height() + self.textEdit.contentsMargins().top() +
                                         self.textEdit.contentsMargins().bottom())
            self.log.debug8("MessageBox.__init__: maxWidth exceeded, using line wrap mode")

        self.adjustSize()
        self.setFixedSize(self.size())  # disallow resizing/maximizing

    def exec_(self):
        d = QDialog.exec_(self)
        retval = True if d == QDialog.Accepted else False
        return retval

class IconThemes(QObject):
    def __init__(self, newConfigFile, parser):
        self.log = logging.getLogger("guilog")
        self.newConfigFile = newConfigFile
        self.parser = parser

    def loadTheme(self):
        # load the theme options from the config file
        from module.gui.Options import IconThemeOptions
        from module.lib.SafeEval import const_eval as literal_eval
        opt_dlg = IconThemeOptions(None) # for error checking
        if not self.newConfigFile:
            mainWindowNode = self.parser.xml.elementsByTagName("mainWindow").item(0)
            if not mainWindowNode.isNull():
                nodes = self.parser.parseNode(mainWindowNode, "dict")
                if nodes.get("optionsIconTheme"):
                    optionsIconTheme = str(nodes["optionsIconTheme"].text())
                    def base64ToDict(b64):
                        try:
                            d = literal_eval(str(QByteArray.fromBase64(b64)))
                        except Exception:
                            d = None
                        if d and not isinstance(d, dict):
                            d = None
                        return d
                    d = base64ToDict(optionsIconTheme)
                    if d is not None:
                        try:              opt_dlg.settings = d; opt_dlg.dict2dialogState()
                        except Exception: opt_dlg.defaultSettings(); d = None
        theme = opt_dlg.settings["Theme"]
        c = QColor(); c.setRgba(opt_dlg.settings["FontAwesomeColor"]); fontAwesomeColor = c.getRgb()  # int to tuple
        c = QColor(); c.setRgba(opt_dlg.settings["LineAwesomeColor"]); lineAwesomeColor = c.getRgb()  # int to tuple
        # load the theme
        appIconSet = {}
        if theme == "classic":
            self.loadClassic(appIconSet)
        elif theme == "fontAwesome":
            self.loadFontAwesome(appIconSet, fontAwesomeColor)
        elif theme == "lineAwesome":
            self.loadLineAwesome(appIconSet, lineAwesomeColor)
        return appIconSet

    @classmethod
    def loadClassic(self, appIconSet):
        p = join(pypath, "icons")
        appIconSet["start"]         = QIcon(join(p, "toolbar_start.png"))
        appIconSet["stop"]          = QIcon(join(p, "toolbar_stop.png"))
        appIconSet["stop_nopause"]  = QIcon(join(p, "toolbar_stop_nopause.png"))
        appIconSet["pause"]         = QIcon(join(p, "toolbar_pause.png"))
        appIconSet["add"]           = QIcon(join(p, "toolbar_add.png"))
        appIconSet["clipboard"]     = QIcon(join(p, "clipboard.png"))
        appIconSet["restart"]       = QIcon(join(p, "toolbar_refresh.png"))
        appIconSet["remove"]        = QIcon(join(p, "toolbar_remove.png"))
        appIconSet["pull_small"]    = QIcon(join(p, "pull_small.png"))
        appIconSet["push_small"]    = QIcon(join(p, "push_small.png"))
        appIconSet["add_small"]     = QIcon(join(p, "add_small.png"))
        appIconSet["edit_small"]    = QIcon(join(p, "edit_small.png"))
        appIconSet["abort_small"]   = QIcon(join(p, "abort_small.png"))
        appIconSet["restart_small"] = QIcon(join(p, "refresh_small.png"))
        appIconSet["remove_small"]  = QIcon(join(p, "remove_small.png"))

    def loadFontAwesome(self, appIconSet, color):
        # glyph-name-to-char mapping, parse the css file in no time
        from codecs import unicode_escape_decode
        iconcodes = {}
        iname = None
        with open(join(pypath, "icons", "fontawesome-free-5.11.1-web", "css", "fontawesome.css")) as css:
            for line in css:
                if iname is None:
                    if line.startswith(".fa-") and line.endswith(":before {\n"):
                        iname = line.split(":")[0].split("-", 1)[1]
                else:
                    icode = line.split(":")[1].split(";")[0].strip()
                    if icode.startswith('"') and icode.endswith('"'):
                        icode = icode[1:-1]
                    icode = "\\u" + icode[1:]
                    icode = unicode_escape_decode(icode)[0]
                    iconcodes[unicode(iname)] = icode
                    iname = None
        # assign the icons
        t = self.ttfGlyph2QIcon
        ic = iconcodes
        fr = join(pypath, "icons", "fontawesome-free-5.11.1-web", "webfonts", "fa-regular-400.ttf")
        fs = join(pypath, "icons", "fontawesome-free-5.11.1-web", "webfonts", "fa-solid-900.ttf")
        ###                                   size    name             scale  x    y  color
        appIconSet["start"]         = t(ic,fr, 64,  "play-circle",      -9,   1,   1, color)
        appIconSet["stop"]          = t(ic,fr, 64,  "stop-circle",      -9,   1,   1, color)
        appIconSet["stop_nopause"]  = t(ic,fr, 64,  "dot-circle",       -9,   1,   1, color)
        appIconSet["pause"]         = t(ic,fr, 64,  "pause-circle",     -9,   1,   1, color)
        appIconSet["add"]           = t(ic,fr, 64,  "plus-square",      -9,   0,  -1, color)
        appIconSet["clipboard"]     = t(ic,fr, 64,  "clipboard",       -12,  -1,  -2, color)
        appIconSet["restart"]       = t(ic,fs, 64,  "redo-alt",        -20,   0,   0, color)
        appIconSet["remove"]        = t(ic,fr, 64,  "trash-alt",       -14,   0,  -2, color)
        appIconSet["pull_small"]    = t(ic,fs, 64,  "eject",           -14,  -1,  -3, color)
        appIconSet["push_small"]    = t(ic,fs, 64,  "download",        -14,  -2,  -2, color)
        appIconSet["add_small"]     = t(ic,fr, 68,  "plus-square",      -1,   1,  -1, color)
        appIconSet["edit_small"]    = t(ic,fs, 64,  "pencil-alt",      -13,   1,   0, color)
        appIconSet["abort_small"]   = t(ic,fs, 64,  "times",             0,   0,  -4, color)
        appIconSet["restart_small"] = t(ic,fs, 64,  "redo-alt",         -9,   0,   0, color)
        appIconSet["remove_small"]  = t(ic,fr, 64,  "trash-alt",        -2,   1,  -1, color)

    def loadLineAwesome(self, appIconSet, color):
        # glyph-name-to-char mapping, parse the css file in no time
        from codecs import unicode_escape_decode
        iconcodes = {}
        with open(join(pypath, "icons", "line-awesome", "css", "line-awesome.css")) as css:
            for line in css:
                    if not line.startswith(".la-") or (line.find(":before {") == -1):
                        continue
                    iname = line.split(":")[0].split("-", 1)[1]
                    icode = line.split("content:")[1].split(";")[0].strip()
                    if icode.startswith('"') and icode.endswith('"'):
                        icode = icode[1:-1]
                    icode = "\\u" + icode[1:]
                    icode = unicode_escape_decode(icode)[0]
                    iconcodes[unicode(iname)] = icode
        # assign the icons
        t = self.ttfGlyph2QIcon
        ic = iconcodes
        f = join(pypath, "icons", "line-awesome", "fonts", "line-awesome.ttf")
        ###                                  size    name          scale  x    y  color
        appIconSet["start"]         = t(ic,f, 64,  "play",           0,   1,  -5, color)
        appIconSet["stop"]          = t(ic,f, 64,  "stop",           0,   1,  -5, color)
        appIconSet["stop_nopause"]  = t(ic,f, 60,  "minus-square",  -4,   1,  -4, color)
        appIconSet["pause"]         = t(ic,f, 64,  "pause",         -4,  -1,  -5, color)
        appIconSet["add"]           = t(ic,f, 64,  "plus",           0,   0,  -6, color)
        appIconSet["clipboard"]     = t(ic,f, 64,  "clipboard",     -4,   2,  -5, color)
        appIconSet["restart"]       = t(ic,f, 64,  "refresh",       -9,   0,  -5, color)
        appIconSet["remove"]        = t(ic,f, 64,  "minus",          0,   0,  -6, color)
        appIconSet["pull_small"]    = t(ic,f, 64,  "eject",         18,   0,  -5, color)
        appIconSet["push_small"]    = t(ic,f, 64,  "download",      22,   0, -10, color)
        appIconSet["add_small"]     = t(ic,f, 64,  "plus",          12,   0,  -7, color)
        appIconSet["edit_small"]    = t(ic,f, 64,  "pencil-square",  8,   2, -10, color)
        appIconSet["abort_small"]   = t(ic,f, 64,  "times",          7,  -1,  -7, color)
        appIconSet["restart_small"] = t(ic,f, 64,  "refresh",        6,   0,  -7, color)
        appIconSet["remove_small"]  = t(ic,f, 64,  "minus",         12,   0,  -7, color)

    @classmethod
    def ttfGlyph2QIcon(self, iconcodes, fontfile, size, name, scale, offsetX, offsetY, color):
        # convert ttf glyph to QIcon
        from PIL import Image, ImageFont, ImageDraw, ImageQt
        iconcode = iconcodes[name]
        img = Image.new("RGBA", (size, size), color=color)
        draw = ImageDraw.Draw(img)
        font = ImageFont.truetype(fontfile, size + scale)
        width, height = draw.textsize(iconcode, font=font)
        draw.text(((size - width) / 2 + offsetX, (size - height) / 2 + offsetY), iconcode, font=font, fill=color)
        bbox = img.getbbox()
        if bbox is None:
            raise Exception
        alpha = Image.new("L", (size, size), 0)
        draw = ImageDraw.Draw(alpha)
        draw.text(((size - width) / 2 + offsetX, (size - height) / 2 + offsetY), iconcode, font=font, fill=255)
        img = Image.new("RGBA", (size,size), color)
        img.putalpha(alpha)
        if bbox:
            img = img.crop(bbox)
        borderWidth  = int((size - (bbox[2] - bbox[0])) / 2)
        borderHeight = int((size - (bbox[3] - bbox[1])) / 2)
        iconImg = Image.new("RGBA", (size, size), (0,0,0,0))
        iconImg.paste(img, (borderWidth, borderHeight))
        pix = QPixmap.fromImage(ImageQt.ImageQt(iconImg))
#       return QIcon(IconEngine(pix))
        return QIcon(pix)

#class IconEngine(QIconEngine):
#    def __init__(self, pix):
#        QIconEngine.__init__(self)
#        self.pix = pix
#
#    def paint(self, painter, rect, mode, state):
#        self.pix = self.pix.scaled(rect.size(), Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
#        painter.drawPixmap(rect, self.pix)
#
#    def pixmap(self, size, mode, state):
#        pixmap = QPixmap(size)
#        pixmap.fill(Qt.transparent)
#        p = QPainter(pixmap)
#        self.paint(p, pixmap.rect(), mode, state)
#        return pixmap

class WidgetDisable(QObject):
    def __init__(self, widget, msec=300):
        QObject.__init__(self, None)
        self.cname = self.__class__.__name__
        self.log = logging.getLogger("guilog")
        self.widget = widget
        self.widget.setEnabled(False)
        self.enableTime = self.time_msec() + msec

    @classmethod
    def time_msec(self):
        return int((datetime.utcnow() - datetime(1970, 1, 1)).total_seconds() * 1000)

    def Enable(self):
        t = self.time_msec()
        if t > self.enableTime:
            delay = 0
        else:
            delay = self.enableTime - t
        self.log.debug8("%s.Enable:   enableTime:%d   time:%d   delay:%d" % (self.cname, self.enableTime, t, delay))
        QTimer.singleShot(delay, lambda: self.widget.setEnabled(True))
        self.deleteLater()

def longestSubsequence(seq, mode='strictly', order='increasing', key=None, index=False):
    """
    Return the longest increasing subsequence of `seq`.
      https://stackoverflow.com/questions/3992697/longest-increasing-subsequence

    Parameters
    ----------
    seq : sequence object
        Can be any sequence, like `str`, `list`, `numpy.array`.
    mode : {'strict', 'strictly', 'weak', 'weakly'}, optional
        If set to 'strict', the subsequence will contain unique elements.
        Using 'weak' an element can be repeated many times.
        Modes ending in -ly serve as a convenience to use with `order` parameter,
        because `longest_sequence(seq, 'weakly', 'increasing')` reads better.
        The default is 'strict'.
    order : {'increasing', 'decreasing'}, optional
        By default return the longest increasing subsequence, but it is possible
        to return the longest decreasing sequence as well.
    key : function, optional
        Specifies a function of one argument that is used to extract a comparison
        key from each list element (e.g., `str.lower`, `lambda x: x[0]`).
        The default value is `None` (compare the elements directly).
    index : bool, optional
        If set to `True`, return the indices of the subsequence, otherwise return
        the elements. Default is `False`.

    Returns
    -------
    elements : list, optional
        A `list` of elements of the longest subsequence.
        Returned by default and when `index` is set to `False`.
    indices : list, optional
        A `list` of indices pointing to elements in the longest subsequence.
        Returned when `index` is set to `True`.
    """

    bisect = bisect_left if mode.startswith('strict') else bisect_right

    # compute keys for comparison just once
    rank = seq if key is None else map(key, seq)
    if order == 'decreasing':
        rank = map(cmp_to_key(lambda x,y: 1 if x<y else 0 if x==y else -1), rank)
    rank = list(rank)

    if not rank: return []

    lastoflength = [0] # end position of subsequence with given length
    predecessor = [None] # penultimate element of l.i.s. ending at given position

    for i in range(1, len(seq)):
        # seq[i] can extend a subsequence that ends with a lesser (or equal) element
        j = bisect([rank[k] for k in lastoflength], rank[i])
        # update existing subsequence of length j or extend the longest
        try: lastoflength[j] = i
        except Exception: lastoflength.append(i)
        # remember element before seq[i] in the subsequence
        predecessor.append(lastoflength[j-1] if j > 0 else None)

    # trace indices [p^n(i), ..., p(p(i)), p(i), i], where n=len(lastoflength)-1
    def trace(i):
        if i is not None:
            #yield from trace(predecessor[i])
            for t in trace(predecessor[i]):
                yield t
            yield i
    indices = trace(lastoflength[-1])

    return list(indices) if index else [seq[i] for i in indices]
