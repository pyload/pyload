# -*- coding: utf-8 -*-

from pyload.plugins.OCR import OCR


class NetloadIn(OCR):
    __name    = "NetloadIn"
    __type    = "ocr"
    __version = "0.10"

    __description = """Netload.in ocr plugin"""
    __license     = "GPLv3"
    __authors     = [("pyLoad Team", "admin@pyload.org")]


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
