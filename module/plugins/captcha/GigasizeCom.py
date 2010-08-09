# -*- coding: utf-8 -*-
from captcha import OCR

class GigasizeCom(OCR):
    def __init__(self):
        OCR.__init__(self)
        
    def get_captcha(self, image):
        self.load_image(image)
        self.threshold(2.8)
        self.run_tesser(True, False, False, True)
        return self.result_captcha

if __name__ == '__main__':
    ocr = GigasizeCom()
    import urllib
    urllib.urlretrieve('http://www.gigasize.com/randomImage.php', "gigasize_tmp.jpg")
    
    print ocr.get_captcha('gigasize_tmp.jpg')
