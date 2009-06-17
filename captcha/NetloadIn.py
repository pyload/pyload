from captcha import Ocr

class NetloadIn(Ocr):
    def __init__(self, image):
        Ocr.__init__(self, image)

    def get_captcha(self):
        self.to_greyscale()
        self.clean(3)
        self.clean(3)
        self.run_tesser()
        return self.result_captcha

if __name__ == '__main__':
    ocr = NetloadIn('captchas/netload/captcha.php10.png')
    print  ocr.get_captcha()
