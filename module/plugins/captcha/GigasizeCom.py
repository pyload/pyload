from captcha import OCR

class GigasizeCom(OCR):
    def __init__(self):
        OCR.__init__(self)
        
    def get_captcha(self, image):
        self.load_image(image)
        self.threshold(2.8)
        self.run_gocr()
        return self.result_captcha

if __name__ == '__main__':
    ocr = GigasizeCom()
    print  ocr.get_captcha('gigasize-com/7.jpg')
