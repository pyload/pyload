from captcha import OCR

class NetloadIn(OCR):
    def __init__(self):
        OCR.__init__(self)

    def get_captcha(self, image):
        self.load_image(image)
        self.to_greyscale()
        self.clean(3)
        self.clean(3)
        self.run_tesser()
        return self.result_captcha

if __name__ == '__main__':
    ocr = NetloadIn()
    print  ocr.get_captcha('captchas/netload/captcha.php10.png')
