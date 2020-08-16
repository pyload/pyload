# -*- coding: utf-8 -*-
import base64
import os
import time

from .plugin import BasePlugin


class BaseCaptcha(BasePlugin):
    __name__ = "BaseCaptcha"
    __type__ = "anticaptcha"
    __version__ = "0.56"
    __status__ = "stable"

    __description__ = """Base anti-captcha plugin"""
    __license__ = "GPLv3"
    __authors__ = [("Walter Purcaro", "vuolter@gmail.com")]

    def __init__(self, pyfile):
        self._init(pyfile.m.pyload)

        self.pyfile = pyfile
        self.task = None  #: captcha_manager task

        self.init()

    def _log(self, level, plugintype, pluginname, args, kwargs):
        args = (self.__name__,) + args
        return self.pyfile.plugin._log(
            level, plugintype, self.pyfile.plugin.__name__, args, kwargs
        )

    def recognize(self, image):
        """
        Extend to build your custom anti-captcha ocr.
        """
        raise NotImplementedError

    def decrypt(
        self,
        url,
        get={},
        post={},
        ref=False,
        cookies=True,
        req=None,
        input_type="jpg",
        output_type="textual",
        ocr=True,
        timeout=120,
    ):
        img = self.load(
            url,
            get=get,
            post=post,
            ref=ref,
            cookies=cookies,
            decode=False,
            req=req or self.pyfile.plugin.req,
        )
        return self.decrypt_image(img, input_type, output_type, ocr, timeout)

    def decrypt_image(
        self, img, input_type="jpg", output_type="textual", ocr=False, timeout=120
    ):
        """
        Loads a captcha and decrypts it with ocr, plugin, user input.

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
        time_ref = "{:.2f}".format(time.time())[-6:].replace(".", "")

        with open(
            os.path.join(
                self.pyload.tempdir,
                "captcha_image_{}_{}.{}".format(
                    self.pyfile.plugin.__name__, time_ref, input_type
                ),
            ),
            "wb",
        ) as img_f:
            img_f.write(img)

        if ocr:
            self.log_info(self._("Using OCR to decrypt captcha..."))

            if isinstance(ocr, str):
                _OCR = self.pyload.plugin_manager.load_class(
                    "anticaptcha", ocr
                )  #: Rename `captcha` to `ocr` in 0.6.x
                result = _OCR(self.pyfile).recognize(img_f.name)
            else:
                result = self.recognize(img_f.name)

                if not result:
                    self.log_warning(self._("No OCR result"))

        if not result:
            captcha_manager = self.pyload.captcha_manager
            timeout = max(timeout, 50)

            try:
                params = {
                    "src": "data:image/{};base64,{}".format(
                        input_type, base64.standard_b64encode(img)
                    ),
                    "file": img_f.name,
                    "captcha_plugin": self.__name__,
                    "plugin": self.pyfile.plugin.__name__,
                }
                self.task = captcha_manager.new_task(input_type, params, output_type)

                captcha_manager.handle_captcha(self.task, timeout)

                while self.task.is_waiting():
                    self.pyfile.plugin.check_status()
                    time.sleep(1)

            finally:
                captcha_manager.remove_task(self.task)

            result = self.task.result

            if self.task.error:
                if not self.task.handler and not self.pyload.is_client_connected():
                    self.log_warning(
                        self._("No Client connected for captcha decrypting")
                    )
                    self.fail(self._("No Client connected for captcha decrypting"))
                else:
                    self.pyfile.plugin.retry_captcha(msg=self.task.error)

            elif self.task.result:
                self.log_info(self._("Captcha result: `{}`").format(result))

            else:
                self.pyfile.plugin.retry_captcha(
                    msg=self._(
                        "No captcha result obtained in appropriate timing ({}s)"
                    ).format(timeout)
                )

        if not self.pyload.debug:
            self.remove(img_f.name, try_trash=False)

        return result

    def decrypt_interactive(self, params={}, timeout=120):
        captcha_manager = self.pyload.captcha_manager
        timeout = max(timeout, 50)

        try:
            params.update(
                {"captcha_plugin": self.__name__, "plugin": self.pyfile.plugin.__name__}
            )
            self.task = captcha_manager.new_task("interactive", params, "interactive")

            captcha_manager.handle_captcha(self.task, timeout)

            while self.task.is_waiting():
                self.pyfile.plugin.check_status()
                time.sleep(1)

        finally:
            captcha_manager.remove_task(self.task)

        result = self.task.result

        if self.task.error:
            if not self.task.handler and not self.pyload.is_client_connected():
                self.log_warning(self._("No Client connected for captcha decrypting"))
                self.fail(self._("No Client connected for captcha decrypting"))
            else:
                self.pyfile.plugin.retry_captcha(msg=self.task.error)

        elif self.task.result:
            self.log_info(self._("Captcha result: `{}`").format(result))

        else:
            self.pyfile.plugin.retry_captcha(
                msg=self._(
                    "No captcha result obtained in appropriate timing ({}s)"
                ).format(timeout)
            )

        return result

    def invalid(self, msg=""):
        if not self.task:
            return

        self.log_warning(self._("Invalid captcha"), msg, self.task.result)
        self.task.invalid()
        self.task = None

    def correct(self):
        if not self.task:
            return

        self.log_info(self._("Correct captcha"), self.task.result)
        self.task.correct()
        self.task = None
