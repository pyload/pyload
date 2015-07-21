# -*- coding: utf-8 -*-

from module.plugins.internal.Plugin import Plugin


class Captcha(Plugin):
    __name__    = "Captcha"
    __type__    = "captcha"
    __version__ = "0.01"
    __status__  = "stable"

    __description__ = """Base anti-captcha plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    def __init__(self, plugin):  #@TODO: pass pyfile instead plugin, so store plugin's html in its associated pyfile as data
        self.pyload = plugin.core
        self.info   = {}  #: Provide information in dict here

        self.plugin = plugin
        self.task   = None  #: captchaManager task

        self.init()


    def _log(self, type, args):
        return super(Captcha, self)._log(type, (self.plugin.__name__,) + args)


    def init(self):
        """
        Initialize additional data structures
        """
        pass


    def decrypt_image(self, url, get={}, post={}, ref=False, cookies=False, decode=False,
                      input_type='png', output_type='textual', try_ocr=True):
        image = self.load(url, get=get, post=post, ref=ref, cookies=cookies, decode=decode)
        return self.decrypt(image, input_type, output_type, try_ocr)


    def decrypt(self, data, input_type='png', output_type='textual', try_ocr=True):
        """
        Loads a captcha and decrypts it with ocr, plugin, user input

        :param url: url of captcha image
        :param get: get part for request
        :param post: post part for request
        :param cookies: True if cookies should be enabled
        :param input_type: Type of the Image
        :param output_type: 'textual' if text is written on the captcha\
        or 'positional' for captcha where the user have to click\
        on a specific region on the captcha
        :param try_ocr: if True, ocr is not used

        :return: result of decrypting
        """
        id = ("%.2f" % time.time())[-6:].replace(".", "")

        with open(os.path.join("tmp", "tmpCaptcha_%s_%s.%s" % (self.plugin.__name__, id, input_type)), "wb") as tmpCaptcha:
            tmpCaptcha.write(img)

        has_plugin = self.plugin.__name__ in self.pyload.pluginManager.ocrPlugins

        if self.pyload.captcha:
            Ocr = self.pyload.pluginManager.loadClass("ocr", self.plugin.__name__)
        else:
            Ocr = None

        if Ocr and try_ocr:
            time.sleep(random.randint(3000, 5000) / 1000.0)
            if self.pyfile.abort:
                self.abort()

            ocr = Ocr(self.pyfile)
            result = ocr.get_captcha(tmpCaptcha.name)
        else:
            captchaManager = self.pyload.captchaManager
            task = captchaManager.newTask(img, input_type, tmpCaptcha.name, output_type)
            self.task = task
            captchaManager.handleCaptcha(task)

            while task.isWaiting():
                if self.pyfile.abort:
                    captchaManager.removeTask(task)
                    self.abort()
                time.sleep(1)

            captchaManager.removeTask(task)

            if task.error and has_plugin:  #: Ignore default error message since the user could use try_ocr
                self.fail(_("Pil and tesseract not installed and no Client connected for captcha decrypting"))
            elif task.error:
                self.fail(task.error)
            elif not task.result:
                self.fail(_("No captcha result obtained in appropiate time by any of the plugins"))

            result = task.result
            self.log_debug("Received captcha result: %s" % result)

        if not self.pyload.debug:
            try:
                os.remove(tmpCaptcha.name)
            except Exception:
                pass

        return result


    def invalid(self):
        self.log_error(_("Invalid captcha"))
        if self.task:
            self.task.invalid()


    def correct(self):
        self.log_info(_("Correct captcha"))
        if self.task:
            self.task.correct()
