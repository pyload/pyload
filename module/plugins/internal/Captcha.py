# -*- coding: utf-8 -*-

from __future__ import with_statement

import base64
import os
import time

from .Plugin import Plugin


class Captcha(Plugin):
    __name__ = "Captcha"
    __type__ = "captcha"
    __version__ = "0.56"
    __status__ = "stable"

    __description__ = """Base anti-captcha plugin"""
    __license__ = "GPLv3"
    __authors__ = [("Walter Purcaro", "vuolter@gmail.com")]

    def __init__(self, pyfile):
        self._init(pyfile.m.core)

        self.pyfile = pyfile
        self.task = None  #: captchaManager task

        self.init()

    def _log(self, level, plugintype, pluginname, messages):
        messages = (self.__name__,) + messages
        return self.pyfile.plugin._log(level, plugintype, self.pyfile.plugin.__name__, messages)

    def recognize(self, image):
        """
        Extend to build your custom anti-captcha ocr
        """
        pass

    def decrypt(self, url, get={}, post={}, ref=False, cookies=True, req=None,
                input_type='jpg', output_type='textual', ocr=True, timeout=120):
        img = self.load(
            url,
            get=get,
            post=post,
            ref=ref,
            cookies=cookies,
            decode=False,
            req=req or self.pyfile.plugin.req)
        return self.decrypt_image(img, input_type, output_type, ocr, timeout)

    def decrypt_image(self, img, input_type='jpg',
                      output_type='textual', ocr=False, timeout=120):
        """
        Loads a captcha and decrypts it with ocr, plugin, user input

        :param img: image raw data
        :param get: get part for request
        :param post: post part for request
        :param cookies: True if cookies should be enabled
        :param input_type: Type of the Image
        :param output_type: 'textual' if text is written on the captcha\
        or 'positional' for captcha where the user have to click\
        on a specific region on the captcha
        :param ocr: if True, builtin ocr is used. if string, the OCR plugin name is used

        :return: result of decrypting
        """
        result = None
        time_ref = ("%.2f" % time.time())[-6:].replace(".", "")

        with open(os.path.join("tmp", "captcha_image_%s_%s.%s" % (self.pyfile.plugin.__name__, time_ref, input_type)), "wb") as img_f:
            img_f.write(img)

        if ocr:
            self.log_info(_("Using OCR to decrypt captcha..."))

            if isinstance(ocr, basestring):
                _OCR = self.pyload.pluginManager.loadClass("captcha", ocr)  #: Rename `captcha` to `ocr` in 0.4.10
                result = _OCR(self.pyfile).recognize(img_f.name)
            else:
                result = self.recognize(img_f.name)

                if not result:
                    self.log_warning(_("No OCR result"))

        if not result:
            captchaManager = self.pyload.captchaManager
            timeout = max(timeout, 50)

            try:
                params = {'src': "data:image/%s;base64,%s" % (input_type, base64.standard_b64encode(img)),
                          'file': img_f.name,
                          'captcha_plugin': self.__name__,
                          'plugin': self.pyfile.plugin.__name__}
                self.task = captchaManager.newTask(input_type, params, output_type)

                captchaManager.handleCaptcha(self.task, timeout)

                while self.task.isWaiting():
                    self.pyfile.plugin.check_status()
                    time.sleep(1)

            finally:
                captchaManager.removeTask(self.task)

            result = self.task.result

            if self.task.error:
                if not self.task.handler and not self.pyload.isClientConnected():
                    self.log_warning(_("No Client connected for captcha decrypting"))
                    self.fail(_("No Client connected for captcha decrypting"))
                else:
                    self.pyfile.plugin.retry_captcha(msg=self.task.error)

            elif self.task.result:
                self.log_info(_("Captcha result: `%s`") % (result,))

            else:
                self.pyfile.plugin.retry_captcha(msg=_("No captcha result obtained in appropriate timing (%ss)") % timeout)

        if not self.pyload.debug:
            self.remove(img_f.name, trash=False)

        return result

    def decrypt_interactive(self, params={}, timeout=120):
        captchaManager = self.pyload.captchaManager
        timeout = max(timeout, 50)

        try:
            params.update({'captcha_plugin': self.__name__,
                           'plugin': self.pyfile.plugin.__name__})
            self.task = captchaManager.newTask("interactive", params, "interactive")

            captchaManager.handleCaptcha(self.task, timeout)

            while self.task.isWaiting():
                self.pyfile.plugin.check_status()
                time.sleep(1)

        finally:
            captchaManager.removeTask(self.task)

        result = self.task.result

        if self.task.error:
            if not self.task.handler and not self.pyload.isClientConnected():
                self.log_warning(_("No Client connected for captcha decrypting"))
                self.fail(_("No Client connected for captcha decrypting"))
            else:
                self.pyfile.plugin.retry_captcha(msg=self.task.error)

        elif self.task.result:
            self.log_info(_("Captcha result: `%s`") % (result,))

        else:
            self.pyfile.plugin.retry_captcha(msg=_("No captcha result obtained in appropriate timing (%ss)") % timeout)

        return result

    def invalid(self, msg=""):
        if not self.task:
            return

        self.log_warning(_("Invalid captcha"), msg, self.task.result)
        self.task.invalid()
        self.task = None

    def correct(self):
        if not self.task:
            return

        self.log_info(_("Correct captcha"), self.task.result)
        self.task.correct()
        self.task = None
