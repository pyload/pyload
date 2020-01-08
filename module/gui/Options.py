# -*- coding: utf-8 -*-

import logging

from PyQt4.QtCore import Qt, SIGNAL
from PyQt4.QtGui import (QApplication, QCheckBox, QColor, QColorDialog, QComboBox, QDialog, QDialogButtonBox, QFont, QFontDialog,
                         QGridLayout, QGroupBox, QHBoxLayout, QIcon, QLabel, QLayout, QLineEdit, QPalette, QPushButton, QRadioButton,
                         QSpinBox, QVBoxLayout)

from os.path import join

from module.gui.Tools import whatsThisFormat, WtDialogButtonBox, LineView

class NotificationOptions(QDialog):
    """
        notification options dialog
    """
    def __init__(self, parent):
        QDialog.__init__(self, parent)
        self.log = logging.getLogger("guilog")

        self.settings = {}

        self.setAttribute(Qt.WA_DeleteOnClose, False)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setWindowTitle(_("Options"))
        self.setWindowIcon(QIcon(join(pypath, "icons", "logo.png")))

        self.cbPackageAdded       = QCheckBox(_("Package Added"))
        self.cbPackageFinished    = QCheckBox(_("Package Download Finished"))
        self.cbFinished           = QCheckBox(_("Download Finished"))
        self.cbOffline            = QCheckBox(_("Download Offline"))
        self.cbSkipped            = QCheckBox(_("Download Skipped"))
        self.cbTempOffline        = QCheckBox(_("Download Temporarily Offline"))
        self.cbFailed             = QCheckBox(_("Download Failed"))
        self.cbAborted            = QCheckBox(_("Download Aborted"))
        self.cbCaptcha            = QCheckBox(_("New Captcha Request"))
        self.cbCaptchaInteractive = QCheckBox(_("New Interactive Captcha Request"))

        vboxCb = QVBoxLayout()
        vboxCb.addWidget(self.cbPackageAdded)
        vboxCb.addWidget(self.cbPackageFinished)
        vboxCb.addWidget(self.cbFinished)
        vboxCb.addWidget(self.cbOffline)
        vboxCb.addWidget(self.cbSkipped)
        vboxCb.addWidget(self.cbTempOffline)
        vboxCb.addWidget(self.cbFailed)
        vboxCb.addWidget(self.cbAborted)
        vboxCb.addWidget(self.cbCaptcha)
        vboxCb.addWidget(self.cbCaptchaInteractive)

        self.cbEnableNotify = QGroupBox(_("Enable Desktop Notifications") + "     ")
        self.cbEnableNotify.setCheckable(True)
        self.cbEnableNotify.setLayout(vboxCb)

        self.buttons = WtDialogButtonBox(Qt.Horizontal, self)
        self.buttons.hideWhatsThisButton()
        self.okBtn     = self.buttons.addButton(QDialogButtonBox.Ok)
        self.cancelBtn = self.buttons.addButton(QDialogButtonBox.Cancel)
        self.buttons.button(QDialogButtonBox.Ok).setText(_("OK"))
        self.buttons.button(QDialogButtonBox.Cancel).setText(_("Cancel"))

        vbox = QVBoxLayout()
        vbox.addWidget(self.cbEnableNotify)
        vbox.addLayout(self.buttons.layout())
        self.setLayout(vbox)

        self.adjustSize()
        self.setFixedSize(self.width(), self.height())

        self.connect(self.okBtn,     SIGNAL("clicked()"), self.accept)
        self.connect(self.cancelBtn, SIGNAL("clicked()"), self.reject)
        self.defaultSettings()

    def defaultSettings(self):
        self.settings.clear()
        self.cbEnableNotify.setChecked(False)
        self.cbPackageAdded.setChecked(False)
        self.cbPackageFinished.setChecked(False)
        self.cbFinished.setChecked(False)
        self.cbOffline.setChecked(True)
        self.cbSkipped.setChecked(True)
        self.cbTempOffline.setChecked(True)
        self.cbFailed.setChecked(True)
        self.cbAborted.setChecked(False)
        self.cbCaptcha.setChecked(False)
        self.cbCaptchaInteractive.setChecked(False)
        self.checkBoxStates2dict()

    def checkBoxStates2dict(self):
        self.settings["EnableNotify"]       = self.cbEnableNotify.isChecked()
        self.settings["PackageAdded"]       = self.cbPackageAdded.isChecked()
        self.settings["PackageFinished"]    = self.cbPackageFinished.isChecked()
        self.settings["Finished"]           = self.cbFinished.isChecked()
        self.settings["Offline"]            = self.cbOffline.isChecked()
        self.settings["Skipped"]            = self.cbSkipped.isChecked()
        self.settings["TempOffline"]        = self.cbTempOffline.isChecked()
        self.settings["Failed"]             = self.cbFailed.isChecked()
        self.settings["Aborted"]            = self.cbAborted.isChecked()
        self.settings["Captcha"]            = self.cbCaptcha.isChecked()
        self.settings["CaptchaInteractive"] = self.cbCaptchaInteractive.isChecked()

    def dict2checkBoxStates(self):
        self.cbEnableNotify.setChecked       (self.settings["EnableNotify"])
        self.cbPackageAdded.setChecked       (self.settings["PackageAdded"])
        self.cbPackageFinished.setChecked    (self.settings["PackageFinished"])
        self.cbFinished.setChecked           (self.settings["Finished"])
        self.cbOffline.setChecked            (self.settings["Offline"])
        self.cbSkipped.setChecked            (self.settings["Skipped"])
        self.cbTempOffline.setChecked        (self.settings["TempOffline"])
        self.cbFailed.setChecked             (self.settings["Failed"])
        self.cbAborted.setChecked            (self.settings["Aborted"])
        self.cbCaptcha.setChecked            (self.settings["Captcha"])
        self.cbCaptchaInteractive.setChecked (self.settings["CaptchaInteractive"])

    def appFontChanged(self):
        self.buttons.updateWhatsThisButton()

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

        self.cbEnableFileLog = QGroupBox(_("Enable File Log") + "     ")
        self.cbEnableFileLog.setCheckable(True)
        self.cbEnableFileLog.setMinimumWidth(250)
        folderLabel = QLabel(_("Folder"))
        self.leFolder = QLineEdit()

        self.cbRotate = QGroupBox(_("Log Rotation") + "     ")
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

        self.buttons = WtDialogButtonBox(Qt.Horizontal)
        self.buttons.hideWhatsThisButton()
        self.okBtn     = self.buttons.addButton(QDialogButtonBox.Ok)
        self.cancelBtn = self.buttons.addButton(QDialogButtonBox.Cancel)
        self.buttons.button(QDialogButtonBox.Ok).setText(_("OK"))
        self.buttons.button(QDialogButtonBox.Cancel).setText(_("Cancel"))

        grid = QGridLayout()
        grid.addWidget(self.cbEnableFileLog, 0, 0)
        grid.setRowStretch(1, 1)
        grid.addLayout(self.buttons.layout(), 2, 0)
        self.setLayout(grid)

        self.adjustSize()
        #self.setFixedSize(self.width(), self.height())

        self.connect(self.okBtn,     SIGNAL("clicked()"), self.accept)
        self.connect(self.cancelBtn, SIGNAL("clicked()"), self.reject)
        self.defaultSettings()

    def exec_(self):
        # It does not resize very well when the font size has changed
        if self.font() != self.lastFont:
            self.lastFont = self.font()
            self.adjustSize()
        return QDialog.exec_(self)

    def defaultSettings(self):
        self.settings.clear()
        self.cbEnableFileLog.setChecked(False)
        self.leFolder.setText("Logs")
        self.cbRotate.setChecked(True)
        self.sbSize.setValue(100)
        self.sbCount.setValue(5)
        self.cbException.setChecked(True)
        self.dialogState2dict()

    def dialogState2dict(self):
        self.settings["file_log"]   = self.cbEnableFileLog.isChecked()
        self.settings["log_folder"] = unicode(self.leFolder.text())
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

    def appFontChanged(self):
        self.buttons.updateWhatsThisButton()

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
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setWindowTitle(_("Options"))
        self.setWindowIcon(QIcon(join(pypath, "icons", "logo.png")))

        self.cbEnable = QCheckBox(_("Enable"))
        self.lblFrom = QLabel(_("Local Port"))
        self.sbFromPort = QSpinBox()
        self.sbFromPort.setMinimum(1)
        self.sbFromPort.setMaximum(65535)
        lblTo = QLabel(_("Remote Port"))
        self.sbToPort = QSpinBox()
        self.sbToPort.setMinimum(1)
        self.sbToPort.setMaximum(65535)
        self.cbGetPort = QCheckBox(_("Get Remote Port from Server Settings"))
        lblSta = QLabel(_("Status"))
        self.lblStatus = LineView("Unknown")
        self.lblStatus.setAlignment(Qt.AlignHCenter)
        wt = _(
        "This should usually stay on port 9666. At least Firefox with FlashGot only works reliable with its default address setting:<br>"
        "http://127.0.0.1:9666/flashgot"
        )
        whatsThis = whatsThisFormat(self.lblFrom.text(), wt)
        self.lblFrom.setWhatsThis(whatsThis)
        self.sbFromPort.setWhatsThis(whatsThis)
        whatsThis = whatsThisFormat(self.cbGetPort.text(), _("Needs") + " '" + _("Settings") + "'" + " (SETTINGS) " + _("permission on the server."))
        self.cbGetPort.setWhatsThis(whatsThis)

        self.hboxStatus = QHBoxLayout()
        self.hboxStatus.addWidget(lblSta)
        self.hboxStatus.addWidget(self.lblStatus)

        grid = QGridLayout()
        grid.addWidget(self.cbEnable,   0, 0, 1, 2)
        grid.addWidget(self.lblFrom,    1, 0)
        grid.addWidget(self.sbFromPort, 1, 1)
        grid.addWidget(lblTo,           2, 0)
        grid.addWidget(self.sbToPort,   2, 1)
        grid.addWidget(self.cbGetPort,  3, 0, 1, 3)
        grid.setColumnStretch(2, 1)
        grid.setRowMinimumHeight(4, 20)
        grid.addLayout(self.hboxStatus, 5, 0, 1, 3)
        grid.setRowStretch(6, 1)

        gb = QGroupBox(_("ClickNLoad Port Forwarding") + "     ")
        gb.setLayout(grid)

        self.buttons = WtDialogButtonBox(Qt.Horizontal, self)
        self.okBtn     = self.buttons.addButton(QDialogButtonBox.Ok)
        self.cancelBtn = self.buttons.addButton(QDialogButtonBox.Cancel)
        self.buttons.button(QDialogButtonBox.Ok).setText(_("OK"))
        self.buttons.button(QDialogButtonBox.Cancel).setText(_("Cancel"))

        vbox = QVBoxLayout()
        vbox.addWidget(gb)
        vbox.addLayout(self.buttons.layout())
        self.setLayout(vbox)

        self.setMinimumWidth(250)
        self.adjustSize()

        self.connect(self.okBtn,     SIGNAL("clicked()"), self.accept)
        self.connect(self.cancelBtn, SIGNAL("clicked()"), self.reject)
        self.connect(self.cbGetPort, SIGNAL("toggled(bool)"), self.sbToPort.setDisabled)

        # default settings
        self.settings["enabled"]  = False
        self.settings["fromIP"]   = "127.0.0.1"
        self.settings["toIP"]     = "999.999.999.999"
        self.settings["toPort"]   = 9666
        self.settings["getPort"]  = False
        self.defaultFromPort()

    def exec_(self):
        # It does not resize very well when the font size has changed
        if self.font() != self.lastFont:
            self.lastFont = self.font()
            self.adjustSize()
        return QDialog.exec_(self)

    def defaultFromPort(self):
        self.settings["fromPort"] = 9666
        self.dict2dialogState(True)

    def dialogState2dict(self):
        self.settings["enabled"]  = self.cbEnable.isChecked()
        self.settings["fromPort"] = self.sbFromPort.value()
        self.settings["toPort"]   = self.sbToPort.value()
        self.settings["getPort"]  = self.cbGetPort.isChecked()

    def dict2dialogState(self, error):
        self.cbEnable.setChecked(self.settings["enabled"])
        if (self.settings["fromPort"] < self.sbFromPort.minimum()) or (self.settings["fromPort"] > self.sbFromPort.maximum()):
            raise ValueError("fromPort out of range") # this is catched by main.loadOptionsFromConfig()
        self.sbFromPort.setValue(self.settings["fromPort"])
        #if (self.settings["toPort"] < self.sbToPort.minimum()) or (self.settings["toPort"] > self.sbToPort.maximum()):
        #    raise ValueError("toPort out of range")
        self.sbToPort.setValue(self.settings["toPort"])
        self.cbGetPort.setChecked(self.settings["getPort"])
        if not error:
            if self.settings["enabled"]:
                self.lblStatus.setText(_("Running"))
            else:
                self.lblStatus.setText(_("Not Running"))
        else:
            self.lblStatus.setText(_("ERROR"))

    def appFontChanged(self):
        self.buttons.updateWhatsThisButton()

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
        self.setWindowFlags(self.windowFlags() &~ Qt.WindowContextHelpButtonHint)
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

        self.cbEnabled = QGroupBox(_("Enable") + " " + _("Automatic Reloading") + "     ")
        self.cbEnabled.setCheckable(True)
        self.cbEnabled.setLayout(hboxCb)

        self.buttons = WtDialogButtonBox(Qt.Horizontal, self)
        self.okBtn     = self.buttons.addButton(QDialogButtonBox.Ok)
        self.cancelBtn = self.buttons.addButton(QDialogButtonBox.Cancel)
        self.buttons.button(QDialogButtonBox.Ok).setText(_("OK"))
        self.buttons.button(QDialogButtonBox.Cancel).setText(_("Cancel"))

        vbox = QVBoxLayout()
        vbox.addWidget(self.cbEnabled)
        vbox.addStretch(1)
        vbox.addLayout(self.buttons.layout())
        self.setLayout(vbox)

        self.setMinimumWidth(250)
        self.adjustSize()

        self.connect(self.okBtn,     SIGNAL("clicked()"), self.accept)
        self.connect(self.cancelBtn, SIGNAL("clicked()"), self.reject)
        self.defaultSettings()

    def exec_(self):
        # It does not resize very well when the font size has changed
        if self.font() != self.lastFont:
            self.lastFont = self.font()
            self.adjustSize()
        return QDialog.exec_(self)

    def defaultSettings(self):
        self.settings.clear()
        self.settings["enabled"]  = False
        self.settings["interval"] = 300
        self.dict2dialogState()

    def dialogState2dict(self):
        self.settings["enabled"] = self.cbEnabled.isChecked()
        self.settings["interval"] = self.sbInterval.value()

    def dict2dialogState(self):
        self.cbEnabled.setChecked(self.settings["enabled"])
        self.sbInterval.setValue(self.settings["interval"])

    def appFontChanged(self):
        self.buttons.updateWhatsThisButton()

class CaptchaOptions(QDialog):
    """
        captcha options dialog
    """
    def __init__(self, parent):
        QDialog.__init__(self, parent)
        self.log = logging.getLogger("guilog")

        wt = _(
        "Enables Captcha handling for this pyLoad Client.<br>"
        "- Captcha Button in the toolbar<br>"
        "- Required for Captcha Desktop Notifications<br><br>"
        )
        self.setWhatsThis(whatsThisFormat(_("Captchas"), wt))

        self.settings = {}

        self.setAttribute(Qt.WA_DeleteOnClose, False)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setWindowTitle(_("Options"))
        self.setWindowIcon(QIcon(join(pypath, "icons", "logo.png")))

        self.cbAdjSize                 = QCheckBox(_("Adjust window size to its content"))
        self.cbPopUpCaptcha            = QCheckBox(_("Pop up input dialog for non-interactive captchas"))
        self.cbPopUpCaptchaInteractive = QCheckBox(_("Pop up info about interactive captchas"))

        vboxCb = QVBoxLayout()
        vboxCb.addWidget(self.cbAdjSize)
        vboxCb.addWidget(self.cbPopUpCaptcha)
        vboxCb.addWidget(self.cbPopUpCaptchaInteractive)

        self.cbEnabled = QGroupBox(_("Enable Captchas"))
        self.cbEnabled.setCheckable(True)
        self.cbEnabled.setLayout(vboxCb)

        self.buttons = WtDialogButtonBox(Qt.Horizontal, self)
        self.okBtn     = self.buttons.addButton(QDialogButtonBox.Ok)
        self.cancelBtn = self.buttons.addButton(QDialogButtonBox.Cancel)
        self.buttons.button(QDialogButtonBox.Ok).setText(_("OK"))
        self.buttons.button(QDialogButtonBox.Cancel).setText(_("Cancel"))

        vbox = QVBoxLayout()
        vbox.addWidget(self.cbEnabled)
        vbox.addLayout(self.buttons.layout())
        self.setLayout(vbox)

        self.adjustSize()
        self.setFixedSize(self.width(), self.height())

        self.connect(self.okBtn,     SIGNAL("clicked()"), self.accept)
        self.connect(self.cancelBtn, SIGNAL("clicked()"), self.reject)
        self.defaultSettings()

    def defaultSettings(self):
        self.settings.clear()
        self.settings["Enabled"]                 = True
        self.settings["AdjSize"]                 = True
        self.settings["PopUpCaptcha"]            = False
        self.settings["PopUpCaptchaInteractive"] = False
        self.dict2dialogState()

    def dialogState2dict(self):
        self.settings["Enabled"]                 = self.cbEnabled.isChecked()
        self.settings["AdjSize"]                 = self.cbAdjSize.isChecked()
        self.settings["PopUpCaptcha"]            = self.cbPopUpCaptcha.isChecked()
        self.settings["PopUpCaptchaInteractive"] = self.cbPopUpCaptchaInteractive.isChecked()

    def dict2dialogState(self):
        self.cbEnabled.setChecked                 (self.settings["Enabled"])
        self.cbAdjSize.setChecked                 (self.settings["AdjSize"])
        self.cbPopUpCaptcha.setChecked            (self.settings["PopUpCaptcha"])
        self.cbPopUpCaptchaInteractive.setChecked (self.settings["PopUpCaptchaInteractive"])

    def appFontChanged(self):
        self.buttons.updateWhatsThisButton()

class IconThemeOptions(QDialog):
    """
        icon theme options dialog
    """
    def __init__(self, parent):
        QDialog.__init__(self, parent)
        self.log = logging.getLogger("guilog")

        self.settings = {}
        self.fontAwesomeColor = None
        self.lineAwesomeColor = None
        self.lastFont = None

        self.setAttribute(Qt.WA_DeleteOnClose, False)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setWindowTitle(_("Options"))
        self.setWindowIcon(QIcon(join(pypath, "icons", "logo.png")))

        self.rbClassic = QRadioButton("Classic")
        self.rbFontAwesome = QRadioButton("Font Awesome")
        self.rbLineAwesome = QRadioButton("Line Awesome")
        self.btnFontAwesome = QPushButton(_("Color"))
        self.btnLineAwesome = QPushButton(_("Color"))

        grid = QGridLayout()
        grid.addWidget(self.rbClassic,     0, 0)
        grid.addWidget(self.rbFontAwesome, 1, 0)
        grid.addWidget(self.rbLineAwesome, 2, 0)
        grid.setColumnMinimumWidth(1, 20)
        grid.addWidget(self.btnFontAwesome, 1, 2)
        grid.addWidget(self.btnLineAwesome, 2, 2)

        self.cbEnable = QGroupBox(_("Icon Theme"))
        self.cbEnable.setLayout(grid)

        self.noteLbl = QLabel()
        note = "<i>" + _("Takes effect on next login.") + "</i>"
        self.noteLbl.setText(note)

        self.buttons = WtDialogButtonBox(Qt.Horizontal, self)
        self.buttons.hideWhatsThisButton()

        self.okBtn     = self.buttons.addButton(QDialogButtonBox.Ok)
        self.cancelBtn = self.buttons.addButton(QDialogButtonBox.Cancel)
        self.buttons.button(QDialogButtonBox.Ok).setText(_("OK"))
        self.buttons.button(QDialogButtonBox.Cancel).setText(_("Cancel"))

        vbox = QVBoxLayout()
        vbox.addWidget(self.cbEnable)
        vbox.addWidget(self.noteLbl)
        vbox.addLayout(self.buttons.layout())
        self.setLayout(vbox)

        self.adjustSize()

        self.connect(self.okBtn,     SIGNAL("clicked()"), self.accept)
        self.connect(self.cancelBtn, SIGNAL("clicked()"), self.reject)
        self.connect(self.btnFontAwesome, SIGNAL("clicked()"), self.chooseFontAwesomeColor)
        self.connect(self.btnLineAwesome, SIGNAL("clicked()"), self.chooseLineAwesomeColor)

        self.defaultSettings()

    def chooseFontAwesomeColor(self):
        initCol = QColor()
        initCol.setRgba(self.fontAwesomeColor)
        col = QColorDialog.getColor(initCol, self, self.rbFontAwesome.text(), QColorDialog.DontUseNativeDialog)
        if not col.isValid():
            return
        self.fontAwesomeColor = col.rgba()

    def chooseLineAwesomeColor(self):
        initCol = QColor()
        initCol.setRgba(self.lineAwesomeColor)
        col = QColorDialog.getColor(initCol, self, self.rbLineAwesome.text(), QColorDialog.DontUseNativeDialog)
        if not col.isValid():
            return
        self.lineAwesomeColor = col.rgba()

    def exec_(self):
        # It does not resize very well when the font size has changed
        if self.font() != self.lastFont:
            self.lastFont = self.font()
            self.adjustSize()
        return QDialog.exec_(self)

    def defaultSettings(self):
        self.settings.clear()
        self.settings["Theme"] = "classic"
        defCol = QColor(128, 128, 128, 255).rgba() # integer
        self.settings["FontAwesomeColor"] = defCol
        self.settings["LineAwesomeColor"] = defCol
        self.dict2dialogState()

    def dialogState2dict(self):
        if self.rbClassic.isChecked():
            self.settings["Theme"] = "classic"
        elif self.rbFontAwesome.isChecked():
            self.settings["Theme"] = "fontAwesome"
        elif self.rbLineAwesome.isChecked():
            self.settings["Theme"] = "lineAwesome"
        self.settings["FontAwesomeColor"] = self.fontAwesomeColor
        self.settings["LineAwesomeColor"] = self.lineAwesomeColor

    def dict2dialogState(self):
        if self.settings["Theme"] == "classic":
            self.rbClassic.setChecked(True)
        elif self.settings["Theme"] == "fontAwesome":
            self.rbFontAwesome.setChecked(True)
        elif self.settings["Theme"] == "lineAwesome":
            self.rbLineAwesome.setChecked(True)
        self.fontAwesomeColor = self.settings["FontAwesomeColor"]
        self.lineAwesomeColor = self.settings["LineAwesomeColor"]

    def appFontChanged(self):
        self.buttons.updateWhatsThisButton()

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

        self.cbEnableCustomFonts = QGroupBox(_("Enable Custom Fonts") + "     ")
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

        self.buttons = WtDialogButtonBox(Qt.Horizontal)
        self.buttons.hideWhatsThisButton()
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
        vbox.addLayout(self.buttons.layout())
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

    def defaultSettings(self):
        self.settings.clear()
        self.slotResetBtn()

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
        self.emit(SIGNAL("appFontChanged"))

    def appFontChanged(self):
        self.buttons.updateWhatsThisButton()

class ColorFixOptions(QDialog):
    """
        color fix options dialog
    """
    def __init__(self, parent):
        QDialog.__init__(self, parent)
        self.log = logging.getLogger("guilog")

        wt = _(
        "This is a workaround for an issue with displaying disabled window elements on some systems.<br>"
        "If you can distinguish the buttons 'common button' and 'disabled button' by their coloring, "
        "then your system is probably not affected and you can turn of this option.<br><br>"
        "The default alpha channel value is 128"
        )
        self.setWhatsThis(whatsThisFormat(_("Color Fix"), wt))

        self.settings = {}
        self.lastFont = None
        self.defaultColors = {}
        self.getDefaultColors()

        self.setAttribute(Qt.WA_DeleteOnClose, False)
        self.setWindowFlags(self.windowFlags() &~ Qt.WindowContextHelpButtonHint)
        self.setWindowTitle(_("Options"))
        self.setWindowIcon(QIcon(join(pypath, "icons", "logo.png")))

        btnEnabled = QPushButton(_("common button"))
        btnEnabled.setFocusPolicy(Qt.NoFocus)
        btnDisabled = QPushButton(_("disabled button"))
        btnDisabled.setPalette(QPalette(QApplication.palette()))
        btnDisabled.setEnabled(False)

        lblPv = QLabel(_("Preview"))
        lblPv.setAlignment(Qt.AlignCenter)

        self.btnPvDisabled = QPushButton(_("disabled button fixed"))    # Note: This is actually an enabled button
        self.btnPvDisabled.setFocusPolicy(Qt.NoFocus)

        lbl1 = QLabel(_("Alpha channel value"))
        self.sbAlpha = QSpinBox()
        self.sbAlpha.setMinimum(30)
        self.sbAlpha.setMaximum(255)

        hboxSb = QHBoxLayout()
        hboxSb.addWidget(lbl1)
        hboxSb.addWidget(self.sbAlpha)
        hboxSb.addStretch(1)

        vboxSbPv = QVBoxLayout()
        vboxSbPv.addWidget(lblPv)
        vboxSbPv.addWidget(self.btnPvDisabled)
        vboxSbPv.addLayout(hboxSb)

        self.cbEnabled = QGroupBox(_("Fix disabled window elements") + "     ")
        self.cbEnabled.setCheckable(True)
        self.cbEnabled.setLayout(vboxSbPv)

        self.buttons = WtDialogButtonBox(Qt.Horizontal, self)
        self.okBtn     = self.buttons.addButton(QDialogButtonBox.Ok)
        self.cancelBtn = self.buttons.addButton(QDialogButtonBox.Cancel)
        self.buttons.button(QDialogButtonBox.Ok).setText(_("OK"))
        self.buttons.button(QDialogButtonBox.Cancel).setText(_("Cancel"))

        vbox = QVBoxLayout()
        vbox.addWidget(btnEnabled)
        vbox.addWidget(btnDisabled)
        vbox.addWidget(self.cbEnabled)
        vbox.addStretch(1)
        vbox.addLayout(self.buttons.layout())
        self.setLayout(vbox)

        self.setMinimumWidth(250)
        self.adjustSize()

        self.connect(self.sbAlpha,   SIGNAL("valueChanged(int)"), self.slotSetPreviewButtonAlpha)
        self.connect(self.okBtn,     SIGNAL("clicked()"), self.accept)
        self.connect(self.cancelBtn, SIGNAL("clicked()"), self.reject)
        self.defaultSettings()

    def getDefaultColors(self):
        p = QApplication.palette()
        self.defaultColors["window"]          = int(p.color(QPalette.Disabled, QPalette.Window          ).rgba())
        self.defaultColors["windowText"]      = int(p.color(QPalette.Disabled, QPalette.WindowText      ).rgba())
        self.defaultColors["base"]            = int(p.color(QPalette.Disabled, QPalette.Base            ).rgba())
        self.defaultColors["alternateBase"]   = int(p.color(QPalette.Disabled, QPalette.AlternateBase   ).rgba())
        self.defaultColors["text"]            = int(p.color(QPalette.Disabled, QPalette.Text            ).rgba())
        self.defaultColors["button"]          = int(p.color(QPalette.Disabled, QPalette.Button          ).rgba())
        self.defaultColors["buttonText"]      = int(p.color(QPalette.Disabled, QPalette.ButtonText      ).rgba())
        self.defaultColors["brightText"]      = int(p.color(QPalette.Disabled, QPalette.BrightText      ).rgba())
        self.defaultColors["link"]            = int(p.color(QPalette.Disabled, QPalette.Link            ).rgba())
        self.defaultColors["highlight"]       = int(p.color(QPalette.Disabled, QPalette.Highlight       ).rgba())
        self.defaultColors["highlightedText"] = int(p.color(QPalette.Disabled, QPalette.HighlightedText ).rgba())

    def setDefaultColors(self):
        p = QApplication.palette()
        c = QColor(); c.setRgba(self.defaultColors["window"]);          p.setColor(QPalette.Disabled, QPalette.Window          , c)
        c = QColor(); c.setRgba(self.defaultColors["windowText"]);      p.setColor(QPalette.Disabled, QPalette.WindowText      , c)
        c = QColor(); c.setRgba(self.defaultColors["base"]);            p.setColor(QPalette.Disabled, QPalette.Base            , c)
        c = QColor(); c.setRgba(self.defaultColors["alternateBase"]);   p.setColor(QPalette.Disabled, QPalette.AlternateBase   , c)
        c = QColor(); c.setRgba(self.defaultColors["text"]);            p.setColor(QPalette.Disabled, QPalette.Text            , c)
        c = QColor(); c.setRgba(self.defaultColors["button"]);          p.setColor(QPalette.Disabled, QPalette.Button          , c)
        c = QColor(); c.setRgba(self.defaultColors["buttonText"]);      p.setColor(QPalette.Disabled, QPalette.ButtonText      , c)
        c = QColor(); c.setRgba(self.defaultColors["brightText"]);      p.setColor(QPalette.Disabled, QPalette.BrightText      , c)
        c = QColor(); c.setRgba(self.defaultColors["link"]);            p.setColor(QPalette.Disabled, QPalette.Link            , c)
        c = QColor(); c.setRgba(self.defaultColors["highlight"]);       p.setColor(QPalette.Disabled, QPalette.Highlight       , c)
        c = QColor(); c.setRgba(self.defaultColors["highlightedText"]); p.setColor(QPalette.Disabled, QPalette.HighlightedText , c)
        QApplication.setPalette(p)

    def slotSetPreviewButtonAlpha(self, alpha):
        p = self.btnPvDisabled.palette()
        c = p.button().color()
        c.setAlpha(alpha)
        p.setColor(QPalette.Active,   QPalette.Button, c)
        p.setColor(QPalette.Disabled, QPalette.Button, c)
        c = p.buttonText().color()
        c.setAlpha(alpha)
        p.setColor(QPalette.Active,   QPalette.ButtonText, c)
        p.setColor(QPalette.Disabled, QPalette.ButtonText, c)
        self.btnPvDisabled.setPalette(p)

    def exec_(self):
        # It does not resize very well when the font size has changed
        if self.font() != self.lastFont:
            self.lastFont = self.font()
            self.adjustSize()
        return QDialog.exec_(self)

    def defaultSettings(self):
        self.settings.clear()
        self.settings["enabled"] = True # must be enabled by default!
        self.settings["alpha"] = 128
        self.dict2dialogState()

    def dialogState2dict(self):
        self.settings["enabled"] = self.cbEnabled.isChecked()
        self.settings["alpha"] = self.sbAlpha.value()

    def dict2dialogState(self):
        self.cbEnabled.setChecked(self.settings["enabled"])
        self.sbAlpha.setValue(self.settings["alpha"])

    def applySettings(self):
        def modified_color(color):
            #return QColor(255, 0 ,0)
            color.setAlpha(self.settings["alpha"])
            return color
        if self.settings["enabled"]:
            p = QApplication.palette()
            p.setColor(QPalette.Disabled, QPalette.  Window            , modified_color(p.window          ().color()))
            p.setColor(QPalette.Disabled, QPalette.  WindowText        , modified_color(p.windowText      ().color()))
            p.setColor(QPalette.Disabled, QPalette.  Base              , modified_color(p.base            ().color()))
            p.setColor(QPalette.Disabled, QPalette.  AlternateBase     , modified_color(p.alternateBase   ().color()))
            p.setColor(QPalette.Disabled, QPalette.  Text              , modified_color(p.text            ().color()))
            p.setColor(QPalette.Disabled, QPalette.  Button            , modified_color(p.button          ().color()))
            p.setColor(QPalette.Disabled, QPalette.  ButtonText        , modified_color(p.buttonText      ().color()))
            p.setColor(QPalette.Disabled, QPalette.  BrightText        , modified_color(p.brightText      ().color()))
            p.setColor(QPalette.Disabled, QPalette.  Link              , modified_color(p.link            ().color()))
            p.setColor(QPalette.Disabled, QPalette.  Highlight         , modified_color(p.highlight       ().color()))
            p.setColor(QPalette.Disabled, QPalette.  HighlightedText   , modified_color(p.highlightedText ().color()))
            QApplication.setPalette(p)
        else:
            self.setDefaultColors()

    def appFontChanged(self):
        self.buttons.updateWhatsThisButton()

class TrayOptions(QDialog):
    """
        tray options dialog
    """
    def __init__(self, parent):
        QDialog.__init__(self, parent)
        self.log = logging.getLogger("guilog")

        self.settings = {}

        self.setAttribute(Qt.WA_DeleteOnClose, False)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setWindowTitle(_("Options"))
        self.setWindowIcon(QIcon(join(pypath, "icons", "logo.png")))

        self.cbRestoreGeo    = QCheckBox(_("Restore normal window geometry on show"))
        self.cbMinimize2Tray = QCheckBox(_("Hide in tray when minimized"))
        self.cbClose2Tray    = QCheckBox(_("Hide in tray on close button click"))
        self.lblIconFile     = QLabel(_("Icon size"))
        self.cobIconFile     = QComboBox()
        self.lblIconFileNote = QLabel("<i>" + _("Takes effect on next login.") + "</i>")
        self.lblUrl          = QLabel()

        whatsThis = (self.cbRestoreGeo.text(),
                     _("Additional tweak.<br><br>Can be required on some Ubuntu/Unity desktop environments (Compiz window manager)."))
        self.cbRestoreGeo.setWhatsThis(whatsThisFormat(*whatsThis))
        self.cobIconFile.addItem("24x24")
        self.cobIconFile.addItem("64x64")
        desctext = "<i>" + _("Hints for some desktop environments: ") + "</i>"
        urltext  = "Options.txt"
        url      = "https://github.com/snilt/pyload/blob/forkreadme/Options.txt"
        self.lblUrl.setTextFormat(Qt.RichText)
        self.lblUrl.setText(desctext + "<a href=\"" + url + "\">" + urltext + "</a>")
        self.lblUrl.setToolTip(url)
        self.lblUrl.setTextInteractionFlags(Qt.TextBrowserInteraction)
        self.lblUrl.setOpenExternalLinks(True)

        hboxIconFile = QHBoxLayout()
        hboxIconFile.addWidget(self.lblIconFile)
        hboxIconFile.addWidget(self.cobIconFile)
        hboxIconFile.addWidget(self.lblIconFileNote)
        hboxIconFile.addStretch(1)

        vboxCb = QVBoxLayout()
        vboxCb.addWidget(self.cbRestoreGeo)
        vboxCb.addWidget(self.cbMinimize2Tray)
        vboxCb.addWidget(self.cbClose2Tray)
        vboxCb.addLayout(hboxIconFile)
        vboxCb.addWidget(self.lblUrl)

        self.cbEnableTray = QGroupBox(_("Enable Tray Icon") + "     ")
        self.cbEnableTray.setCheckable(True)
        self.cbEnableTray.setLayout(vboxCb)

        self.buttons = WtDialogButtonBox(Qt.Horizontal, self)
        self.okBtn     = self.buttons.addButton(QDialogButtonBox.Ok)
        self.cancelBtn = self.buttons.addButton(QDialogButtonBox.Cancel)
        self.buttons.button(QDialogButtonBox.Ok).setText(_("OK"))
        self.buttons.button(QDialogButtonBox.Cancel).setText(_("Cancel"))

        vbox = QVBoxLayout()
        vbox.addWidget(self.cbEnableTray)
        vbox.addLayout(self.buttons.layout())
        self.setLayout(vbox)

        self.adjustSize()
        self.setFixedSize(self.width(), self.height())

        self.connect(self.okBtn,     SIGNAL("clicked()"), self.accept)
        self.connect(self.cancelBtn, SIGNAL("clicked()"), self.reject)
        self.defaultSettings()

    def defaultSettings(self):
        self.settings.clear()
        self.settings["EnableTray"]    = True
        self.settings["RestoreGeo"]    = False
        self.settings["Minimize2Tray"] = False
        self.settings["Close2Tray"]    = False
        self.settings["IconFile"]      = "24x24"
        self.dict2checkBoxStates()

    def checkBoxStates2dict(self):
        self.settings["EnableTray"]    = self.cbEnableTray.isChecked()
        self.settings["RestoreGeo"]    = self.cbRestoreGeo.isChecked()
        self.settings["Minimize2Tray"] = self.cbMinimize2Tray.isChecked()
        self.settings["Close2Tray"]    = self.cbClose2Tray.isChecked()
        self.settings["IconFile"]      = str(self.cobIconFile.currentText())

    def dict2checkBoxStates(self):
        self.cbEnableTray.setChecked    (self.settings["EnableTray"])
        self.cbRestoreGeo.setChecked    (self.settings["RestoreGeo"])
        self.cbMinimize2Tray.setChecked (self.settings["Minimize2Tray"])
        self.cbClose2Tray.setChecked    (self.settings["Close2Tray"])
        self.cobIconFile.setCurrentIndex(self.cobIconFile.findText(self.settings["IconFile"]))

    def appFontChanged(self):
        self.buttons.updateWhatsThisButton()

class WhatsThisOptions(QDialog):
    """
        whatsthis options dialog
    """
    def __init__(self, parent):
        QDialog.__init__(self, parent)
        self.log = logging.getLogger("guilog")

        self.defaultColors = (int(QApplication.palette().color(QPalette.Inactive, QPalette.ToolTipText).rgba()),
                              int(QApplication.palette().color(QPalette.Inactive, QPalette.ToolTipBase).rgba()))
        self.choosenColors = None

        self.settings = {}
        self.lastFont = None

        self.setAttribute(Qt.WA_DeleteOnClose, False)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setWindowTitle(_("Options"))
        self.setWindowIcon(QIcon(join(pypath, "icons", "logo.png")))

        self.btnText = QPushButton(_("Text color"))
        self.btnBack = QPushButton(_("Background color"))
        self.lvExample = LineView(_("What's This Preview"))
        self.lvExample.setAlignment(Qt.AlignCenter)
        vbox = QVBoxLayout()
        vbox.addWidget(self.btnText)
        vbox.addWidget(self.btnBack)

        self.cbEnable = QGroupBox(_("Enable Custom Colors") + "     ")
        self.cbEnable.setCheckable(True)
        self.cbEnable.setLayout(vbox)

        self.buttons = WtDialogButtonBox(Qt.Horizontal, self)
        self.buttons.hideWhatsThisButton()
        self.okBtn     = self.buttons.addButton(QDialogButtonBox.Ok)
        self.cancelBtn = self.buttons.addButton(QDialogButtonBox.Cancel)
        self.resetBtn  = self.buttons.addButton(QDialogButtonBox.Reset)
        self.buttons.button(QDialogButtonBox.Ok).setText(_("OK"))
        self.buttons.button(QDialogButtonBox.Cancel).setText(_("Cancel"))
        self.buttons.button(QDialogButtonBox.Reset).setText(_("Reset"))

        vbox = QVBoxLayout()
        vbox.addWidget(self.cbEnable)
        vbox.addWidget(self.lvExample)
        vbox.addSpacing(10)
        vbox.addLayout(self.buttons.layout())
        self.setLayout(vbox)

        self.adjustSize()

        self.connect(self.okBtn,     SIGNAL("clicked()"), self.accept)
        self.connect(self.cancelBtn, SIGNAL("clicked()"), self.reject)
        self.connect(self.resetBtn,  SIGNAL("clicked()"), self.resetBtnClicked)
        self.connect(self.cbEnable,  SIGNAL("toggled(bool)"), self.cbEnableToggled)
        self.connect(self.btnText,   SIGNAL("clicked()"),     self.chooseTextColor)
        self.connect(self.btnBack,   SIGNAL("clicked()"),     self.chooseBackgroundColor)
        self.defaultSettings()

    def resetBtnClicked(self):
        self.choosenColors = self.defaultColors
        self.setExampleColors(self.choosenColors[0], self.choosenColors[1])

    def cbEnableToggled(self, enabled):
        if enabled:
            self.setExampleColors(self.choosenColors[0], self.choosenColors[1])
        else:
            self.setExampleColors(self.defaultColors[0], self.defaultColors[1])
        self.resetBtn.setEnabled(enabled)

    def chooseTextColor(self):
        initCol = QColor()
        initCol.setRgba(self.choosenColors[0])
        col = QColorDialog.getColor(initCol, self, self.btnText.text(), QColorDialog.ShowAlphaChannel | QColorDialog.DontUseNativeDialog)
        if not col.isValid():
            return
        self.choosenColors = (int(col.rgba()), self.choosenColors[1])
        self.setExampleColors(int(col.rgba()), None)

    def chooseBackgroundColor(self):
        initCol = QColor()
        initCol.setRgba(self.choosenColors[1])
        col = QColorDialog.getColor(initCol, self, self.btnBack.text(), QColorDialog.ShowAlphaChannel | QColorDialog.DontUseNativeDialog)
        if not col.isValid():
            return
        self.choosenColors = (self.choosenColors[0], int(col.rgba()))
        self.setExampleColors(None, int(col.rgba()))

    def setExampleColors(self, textCol=None, backCol=None):
        p = QPalette(self.lvExample.palette())
        if textCol is not None:
            qCol = QColor()
            qCol.setRgba(textCol)
            p.setColor(QPalette.Active,   self.lvExample.foregroundRole(), qCol)
            p.setColor(QPalette.Inactive, self.lvExample.foregroundRole(), qCol)
        if backCol is not None:
            qCol = QColor()
            qCol.setRgba(backCol)
            p.setColor(QPalette.Active,   self.lvExample.backgroundRole(), qCol)
            p.setColor(QPalette.Inactive, self.lvExample.backgroundRole(), qCol)
        self.lvExample.setPalette(p)

    def exec_(self):
        # It does not resize very well when the font size has changed
        if self.font() != self.lastFont:
            self.lastFont = self.font()
            self.adjustSize()
        return QDialog.exec_(self)

    def defaultSettings(self):
        self.settings.clear()
        self.settings["Enabled"] = False
        (self.settings["TextColor"], self.settings["BackColor"]) = self.defaultColors
        self.dict2dialogState()

    def dialogState2dict(self):
        self.settings["Enabled"] = self.cbEnable.isChecked()
        (self.settings["TextColor"], self.settings["BackColor"]) = self.choosenColors

    def dict2dialogState(self):
        self.cbEnable.setChecked(self.settings["Enabled"])
        if self.settings["Enabled"]:
            self.choosenColors = (self.settings["TextColor"], self.settings["BackColor"])
            self.setExampleColors(self.choosenColors[0], self.choosenColors[1])
        else:
            if self.choosenColors is None:
                self.choosenColors = (self.settings["TextColor"], self.settings["BackColor"])
            self.setExampleColors(self.defaultColors[0], self.defaultColors[1])

    def applySettings(self):
        if self.settings["Enabled"]:
            textCol = self.settings["TextColor"]
            backCol = self.settings["BackColor"]
        else:
            (textCol, backCol) = self.defaultColors
        p = QApplication.palette()
        qCol = QColor()
        qCol.setRgba(textCol)
        p.setColor(QPalette.Active,   QPalette.ToolTipText, qCol)
        p.setColor(QPalette.Inactive, QPalette.ToolTipText, qCol)
        qCol = QColor()
        qCol.setRgba(backCol)
        p.setColor(QPalette.Active,   QPalette.ToolTipBase, qCol)
        p.setColor(QPalette.Inactive, QPalette.ToolTipBase, qCol)
        QApplication.setPalette(p)

    def appFontChanged(self):
        self.buttons.updateWhatsThisButton()

class OtherOptions(QDialog):
    """
        other options dialog
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

        self.gb = QGroupBox(_("Other") + "     ")
        self.gb.setCheckable(False)

        self.cbRestoreUnmaximizedGeo = QGroupBox(_("Workaround for broken window geometry after unmaximize") + "     ")
        self.cbRestoreUnmaximizedGeo.setCheckable(True)
        wt = _("Due to a bug in the GUI framework (QTBUG-21371) on some platforms, the main window position and/or size does not "
               "get correctly restored when unmaximizing a maximized window that was hidden or loaded from previously saved settings.")
        self.cbRestoreUnmaximizedGeo.setWhatsThis(whatsThisFormat(self.cbRestoreUnmaximizedGeo.title(), wt))

        self.cbHideShowOnUnmax     = QCheckBox(_("Extra fix for show from tray"))
        self.cbSecondLastNormalGeo = QCheckBox(_("Apply second last known geometry"))
        self.cbHideShowOnStart     = QCheckBox(_("Extra fix on application start"))
        self.cbAlwaysRestore       = QCheckBox(_("Always restore geometry"))
        self.lblUrl                = QLabel()

        wt = _("Additional tweak, try enable this if<br>the size is correct but the position is slightly shifted<br>"
               "after showing the (previously maximized and hidden) application from tray and unmaximizing it again.<br><br>"
               "Can be required on some GNOME, Budgie, Cinnamon, MATE or LXDE desktop environments.")
        self.cbHideShowOnUnmax.setWhatsThis(whatsThisFormat(self.cbHideShowOnUnmax.text(), wt))
        wt = _("Additional tweak, try enable this if<br>- unmaximize has no effect<br>or<br>- position and/or size is totally wrong<br>"
               "after showing the (previously maximized and hidden) application from tray and unmaximizing it again.<br><br>"
               "Can be required on some Xfce desktop environments.")
        self.cbSecondLastNormalGeo.setWhatsThis(whatsThisFormat(self.cbSecondLastNormalGeo.text(), wt))
        wt = _("Additional tweak, try enable this if<br>- unmaximize has no effect<br>or<br>- position and/or size is totally wrong<br>"
               "after starting the application maximized (previously exited when maximized) and unmaximizing it.<br><br>"
               "Can be required on some Xfce desktop environments.")
        self.cbHideShowOnStart.setWhatsThis(whatsThisFormat(self.cbHideShowOnStart.text(), wt))
        wt = _("Additional tweak, try enable this if<br>the size is correct but the position is slightly shifted<br>"
               "after maximizing and then unmaximizing the application (without been hidden in between).<br><br>Usually not required.")
        self.cbAlwaysRestore.setWhatsThis(whatsThisFormat(self.cbAlwaysRestore.text(), wt))

        vboxCb1 = QVBoxLayout()
        vboxCb1.addWidget(self.cbHideShowOnUnmax)
        vboxCb1.addWidget(self.cbSecondLastNormalGeo)
        vboxCb1.addWidget(self.cbHideShowOnStart)
        vboxCb1.addWidget(self.cbAlwaysRestore)
        self.cbRestoreUnmaximizedGeo.setLayout(vboxCb1)

        self.cbRefreshGeo = QCheckBox(_("Fix for resize"))
        wt = _("Try enable this if the mainwindow gets slightly shifted when resizing it the first time after starting the "
               "application or when resizing it after showing the application from tray.<br><br>"
               "Can be required on some LXDE desktop environments.")
        self.cbRefreshGeo.setWhatsThis(whatsThisFormat(self.cbRefreshGeo.text(), wt))

        desctext = "<i>" + _("Hints for some desktop environments: ") + "</i>"
        urltext  = "Options.txt"
        url      = "https://github.com/snilt/pyload/blob/forkreadme/Options.txt"
        self.lblUrl.setTextFormat(Qt.RichText)
        self.lblUrl.setText(desctext + "<a href=\"" + url + "\">" + urltext + "</a>")
        self.lblUrl.setToolTip(url)
        self.lblUrl.setTextInteractionFlags(Qt.TextBrowserInteraction)
        self.lblUrl.setOpenExternalLinks(True)

        vboxGb = QVBoxLayout()
        vboxGb.addWidget(self.cbRestoreUnmaximizedGeo)
        vboxGb.addWidget(self.cbRefreshGeo)
        vboxGb.addWidget(self.lblUrl)
        self.gb.setLayout(vboxGb)

        self.buttons = WtDialogButtonBox(Qt.Horizontal, self)
        self.okBtn     = self.buttons.addButton(QDialogButtonBox.Ok)
        self.cancelBtn = self.buttons.addButton(QDialogButtonBox.Cancel)
        self.buttons.button(QDialogButtonBox.Ok).setText(_("OK"))
        self.buttons.button(QDialogButtonBox.Cancel).setText(_("Cancel"))

        vbox = QVBoxLayout()
        vbox.addWidget(self.gb)
        vbox.addLayout(self.buttons.layout())
        self.setLayout(vbox)

        self.adjustSize()
        #self.setFixedSize(self.width(), self.height())

        self.connect(self.okBtn,     SIGNAL("clicked()"), self.accept)
        self.connect(self.cancelBtn, SIGNAL("clicked()"), self.reject)
        self.defaultSettings()

    def exec_(self):
        # It does not resize very well when the font size has changed
        if self.font() != self.lastFont:
            self.lastFont = self.font()
            self.adjustSize()
        return QDialog.exec_(self)

    def defaultSettings(self):
        self.settings.clear()
        self.settings["RestoreUnmaximizedGeo"] = False
        self.settings["HideShowOnUnmax"]       = False
        self.settings["SecondLastNormalGeo"]   = False
        self.settings["HideShowOnStart"]       = False
        self.settings["AlwaysRestore"]         = False
        self.settings["RefreshGeo"]            = False
        self.dict2checkBoxStates()

    def checkBoxStates2dict(self):
        self.settings["RestoreUnmaximizedGeo"] = self.cbRestoreUnmaximizedGeo.isChecked()
        self.settings["HideShowOnUnmax"]       = self.cbHideShowOnUnmax.isChecked()
        self.settings["SecondLastNormalGeo"]   = self.cbSecondLastNormalGeo.isChecked()
        self.settings["HideShowOnStart"]       = self.cbHideShowOnStart.isChecked()
        self.settings["AlwaysRestore"]         = self.cbAlwaysRestore.isChecked()
        self.settings["RefreshGeo"]            = self.cbRefreshGeo.isChecked()

    def dict2checkBoxStates(self):
        self.cbRestoreUnmaximizedGeo.setChecked (self.settings["RestoreUnmaximizedGeo"])
        self.cbHideShowOnUnmax.setChecked       (self.settings["HideShowOnUnmax"])
        self.cbSecondLastNormalGeo.setChecked   (self.settings["SecondLastNormalGeo"])
        self.cbHideShowOnStart.setChecked       (self.settings["HideShowOnStart"])
        self.cbAlwaysRestore.setChecked         (self.settings["AlwaysRestore"])
        self.cbRefreshGeo.setChecked            (self.settings["RefreshGeo"])

    def appFontChanged(self):
        self.buttons.updateWhatsThisButton()

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

        self.gb = QGroupBox(_("Language") + "     ")
        self.gb.setLayout(vboxGp)

        self.buttons = WtDialogButtonBox(Qt.Horizontal, self)
        self.buttons.hideWhatsThisButton()
        self.okBtn     = self.buttons.addButton(QDialogButtonBox.Ok)
        self.cancelBtn = self.buttons.addButton(QDialogButtonBox.Cancel)
        self.buttons.button(QDialogButtonBox.Ok).setText(_("OK"))
        self.buttons.button(QDialogButtonBox.Cancel).setText(_("Cancel"))

        vbox = QVBoxLayout()
        vbox.addWidget(self.gb)
        vbox.addLayout(self.buttons.layout())
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

    def appFontChanged(self):
        self.buttons.updateWhatsThisButton()


