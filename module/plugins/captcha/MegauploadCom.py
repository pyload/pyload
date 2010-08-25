from captcha import OCR

class MegauploadCom(OCR):
    __name__ = "MegauploadCom"
    def __init__(self):
        OCR.__init__(self)
        
    def get_captcha(self, image):
        self.load_image(image)
        self.run_tesser(True, True, False, True)
        return self.result_captcha

if __name__ == '__main__':
    ocr = MegauploadCom()
