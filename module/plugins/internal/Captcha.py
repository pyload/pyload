# -*- coding: utf-8 -*-

from __future__ import with_statement

import os
import time

from module.plugins.internal.Plugin import Plugin
from module.plugins.internal.misc import encode


class Captcha(Plugin):
    __name__    = "Captcha"
    __type__    = "captcha"
    __version__ = "0.48"
    __status__  = "stable"

    __description__ = """Base anti-captcha plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    def __init__(self, pyfile):
        self._init(pyfile.m.core)

        self.pyfile = pyfile
        self.task   = None  #: captchaManager task

        self.init()


    def _log(self, level, plugintype, pluginname, messages):
        messages = (self.__name__,) + messages
        return self.pyfile.plugin._log(level, plugintype, self.pyfile.plugin.__name__, messages)


    def recognize(self, image):
        """
        Extend to build your custom anti-captcha ocr
        """
        pass


    def decrypt(self, url, get={}, post={}, ref=False, cookies=True, decode=False, req=None,
                input_type='jpg', output_type='textual', ocr=True, timeout=120):
        img = self.load(url, get=get, post=post, ref=ref, cookies=cookies, decode=decode, req=req or self.pyfile.plugin.req)
        return self.decrypt_image(img, input_type, output_type, ocr, timeout)


    def decrypt_image(self, img, input_type='jpg', output_type='textual', ocr=False, timeout=120):
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
        :param ocr: if True, ocr is not used

        :return: result of decrypting
        """
        result   = ""
        time_ref = ("%.2f" % time.time())[-6:].replace(".", "")

        with open(os.path.join("tmp", "captcha_image_%s_%s.%s" % (self.pyfile.plugin.__name__, time_ref, input_type)), "wb") as img_f:
            img_f.write(encode(img))

        if ocr:
            if isinstance(ocr, basestring):
                _OCR = self.pyload.pluginManager.loadClass("captcha", ocr)  #: Rename `captcha` to `ocr` in 0.4.10
                result = _OCR(self.pyfile).recognize(img_f.name)
            else:
                result = self.recognize(img_f.name)

        if not result:
            captchaManager = self.pyload.captchaManager

            try:
                self.task = captchaManager.newTask(img, input_type, img_f.name, output_type)

                captchaManager.handleCaptcha(self.task)

                self.task.setWaiting(max(timeout, 50))  #@TODO: Move to `CaptchaManager` in 0.4.10
                while self.task.isWaiting():
                    self.pyfile.plugin.check_status()
                    time.sleep(1)

            finally:
                captchaManager.removeTask(self.task)

            if self.task.error:
                self.fail(self.task.error)

            elif not self.task.result:
                self.pyfile.plugin.retry_captcha(msg=_("No captcha result obtained in appropriate time"))

            result = self.task.result

        if not self.pyload.debug:
            self.remove(img_f.name, trash=False)

        # self.log_info(_("Captcha result: ") + result)  #@TODO: Remove from here?

        return result


    def invalid(self):
        if not self.task:
            return

        self.log_warning(_("Invalid captcha"))
        self.task.invalid()


    def correct(self):
        if not self.task:
            return

        self.log_info(_("Correct captcha"))
        self.task.correct()
