from captcha import OCR

class NetloadIn(OCR):
    def __init__(self):
        OCR.__init__(self)

    def get_captcha(self, image):
        self.load_image(image)
        self.to_greyscale()
        self.clean(3)
        self.clean(3)
        self.logger.debug("Start tesseract")
        self.run_tesser()
        self.logger.debug("Finished tesseract")        

        self.correct({
        ("$", "g"): "5",
        })

        return self.result_captcha

if __name__ == '__main__':
    import urllib
    ocr = NetloadIn()
    urllib.urlretrieve("http://netload.in/share/includes/captcha.php", "captcha.png")

    print  ocr.get_captcha('captcha.png')
