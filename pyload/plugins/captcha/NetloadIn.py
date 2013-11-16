# -*- coding: utf-8 -*-

from OCR import OCR

class NetloadIn(OCR):
    __name__ = "NetloadIn"
    __type__ = "captcha"
    __version__ = 0.01
    __description__ = """Netload.in anti-captcha"""
    __author_name__ = ("pyload Team")
    __author_mail__ = ("admin<at>pyload.org")

    def __init__(self):
        OCR.__init__(self)

    def get_captcha(self, image, type):
        self.load_image(image)
        self.to_greyscale()
        self.clean(3)
        self.clean(3)
        self.run_tesser(True, True, False, False)
        
        self.result_captcha = self.result_captcha.replace(" ", "")[:4] # cut to 4 numbers
        
        return self.result_captcha

if __name__ == '__main__':
    import urllib
    ocr = NetloadInOCR()
    urllib.urlretrieve("http://netload.in/share/includes/captcha.php", "captcha.png")

    print  ocr.get_captcha('captcha.png')
