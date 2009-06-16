import Image
import ImageOps
import subprocess

class Ocr(object):
    def __init__(self, image):
        self.image = Image.open(image)
        self.image_name = 'captcha_clean.png'
        self.result_captcha = ''


    def threshold(self, value):
        self.image = self.image.point(lambda a: a * value +10)

    def run_gocr(self):
        self.image.save(self.image_name)
        cmd = ['gocr', self.image_name]
        self.result_captcha = subprocess.Popen(cmd, stdout=subprocess.PIPE).communicate()[0].replace('\n','')

    def get_captcha(self):
        pass
        
if __name__ == '__main__':
    ocr = Ocr('gigasize-com/7.jpg')
    print  ocr.get_captcha()
