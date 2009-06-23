from captcha import OCR
import urllib

class ShareonlineBiz(OCR):
    def __init__(self):
        OCR.__init__(self)
        
    def get_captcha(self, image):
        urllib.urlretrieve("http://www.share-online.biz/captcha.php", "captcha.jpeg") 
        self.load_image(image)
        self.to_greyscale()
        self.image = self.image.resize((160, 50))
        self.pixels = self.image.load()
        self.threshold(1.85)
        self.eval_black_white(240)
        self.derotate_by_average()

        letters = self.split_captcha_letters()
        
        final = ""
        i = 0
        for letter in letters:
            self.image = letter
            self.image.save(str(i) + ".jpeg")
            self.run_gocr()
            final += self.result_captcha
            i += 1

        return final

if __name__ == '__main__':
    ocr = ShareonlineBiz()
    print  ocr.get_captcha('captcha.jpeg')
