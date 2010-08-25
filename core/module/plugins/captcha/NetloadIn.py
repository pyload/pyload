from captcha import OCR

class NetloadIn(OCR):
    __name__ = "NetloadIn"
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

if __name__ == '__main__':
    import urllib
    ocr = NetloadIn()
    urllib.urlretrieve("http://netload.in/share/includes/captcha.php", "captcha.png")

    print  ocr.get_captcha('captcha.png')
