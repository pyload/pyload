from captcha import OCR
import urllib

class ShareonlineBiz(OCR):
    def __init__(self):
        OCR.__init__(self)
        
    def get_captcha(self, image):
        urllib.urlretrieve("http://www.share-online.biz/captcha.php", "captcha.jpeg") 
        self.load_image(image)
        #self.to_greyscale()
        #self.image.save('grey.jpeg')
        self.image.threshold(32500)
        #self.threshold(1.3)
        self.run_tesser()
        self.image.save('captcha_bla.jpeg')
        return self.result_captcha

if __name__ == '__main__':
    ocr = ShareonlineBiz()
    print  ocr.get_captcha('captcha.jpeg')
