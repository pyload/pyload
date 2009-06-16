from captcha import Ocr

class Gigasize(Ocr):
    def __init__(self, image):
        Ocr.__init__(self, image)
        
    def get_captcha(self):
        self.threshold(2.8)
        self.run_gocr()
        return self.result_captcha

if __name__ == '__main__':
    ocr = Gigasize('gigasize-com/7.jpg')
    print  ocr.get_captcha()
