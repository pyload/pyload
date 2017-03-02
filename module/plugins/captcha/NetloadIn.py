# -*- coding: utf-8 -*-

from ..internal.OCR import OCR


class NetloadIn(OCR):
    __name__ = "NetloadIn"
    __type__ = "ocr"
    __version__ = "0.17"
    __status__ = "testing"

    __description__ = """Netload.in ocr plugin"""
    __license__ = "GPLv3"
    __authors__ = [("pyLoad Team", "admin@pyload.org")]

    def recognize(self, image):
        self.load_image(image)
        self.to_greyscale()
        self.clean(3)
        self.clean(3)
        self.run_tesser(True, True, False, False)

        self.result_captcha = self.result_captcha.replace(
            " ", "")[:4]  # cut to 4 numbers

        return self.result_captcha
