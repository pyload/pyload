# -*- coding: utf-8 -*-

from pyload.plugins.OCR import OCR


class NetloadIn(OCR):
    __name__ = "NetloadIn"
    __type__ = "ocr"
    __version__ = "0.1"

    __description__ = """Netload.in ocr plugin"""
    __author_name__ = "pyLoad Team"
    __author_mail__ = "admin@pyload.org"


    def __init__(self):
        OCR.__init__(self)

    def get_captcha(self, image):
        self.load_image(image)
        self.to_greyscale()
        self.clean(3)
        self.clean(3)
        self.run_tesser(True, True, False, False)

        self.result_captcha = self.result_captcha.replace(" ", "")[:4] # cut to 4 numbers

        return self.result_captcha
