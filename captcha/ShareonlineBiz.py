from captcha import OCR
import urllib

class ShareonlineBiz(OCR):
    def __init__(self):
        OCR.__init__(self)
        
    def get_captcha(self, image):
        self.load_image(image)
        self.to_greyscale()
        self.image = self.image.resize((160, 50))
        self.pixels = self.image.load()
        self.threshold(1.85)
        self.eval_black_white(240)

        letters = self.split_captcha_letters()
        
        final = ""
        for letter in letters:
            self.image = letter
            self.run_tesser()
            final += self.result_captcha

        return final

if __name__ == '__main__':
    ocr = ShareonlineBiz()
    print  ocr.get_captcha('captcha.php3.jpeg')
