# -*- coding: utf-8 -*-

import os
import sys

import pyload.utils.pylgettext as gettext

from getpass import getpass
from os import makedirs
from os.path import abspath, dirname, exists, join
from subprocess import PIPE, call

from pyload.utils import get_console_encoding, versiontuple


class SetupAssistant:
    """ pyLoads initial setup configuration assistant """

    def __init__(self, path, config):
        self.path = path
        self.config = config
        self.stdin_encoding = get_console_encoding(sys.stdin.encoding)


    def start(self):
        langs = self.config.getMetaData("general", "language")["type"].split(";")
        lang = self.ask(u"Choose setup language", "en", langs)
        gettext.setpaths([join(os.sep, "usr", "share", "pyload", "locale"), None])
        translation = gettext.translation("setup", join(self.path, "locale"), languages=[lang, "en"], fallback=True)
        translation.install(True)

        #Input shorthand for yes
        self.yes = _("y")
        #Input shorthand for no
        self.no = _("n")

        #        print
        #        print _("Would you like to configure pyLoad via Webinterface?")
        #        print _("You need a Browser and a connection to this PC for it.")
        #        viaweb = self.ask(_("Start initial webinterface for configuration?"), "y", bool=True)
        #        if viaweb:
        #            try:
        #                from pyload.manager.thread import ServerThread
        #                ServerThread.setup = self
        #                import pyload.webui as webinterface
        #                webinterface.run_simple()
        #                return False
        #            except Exception, e:
        #                print "Setup failed with this error: ", e
        #                print "Falling back to commandline setup."

        print
        print
        print _("Welcome to the pyLoad Configuration Assistant.")
        print _("It will check your system and make a basic setup in order to run pyLoad.")
        print
        print _("The value in brackets [] always is the default value,")
        print _("in case you don't want to change it or you are unsure what to choose, just hit enter.")
        print _(
            "Don't forget: You can always rerun this assistant with --setup or -s parameter, when you start pyload.py .")
        print _("If you have any problems with this assistant hit STRG-C,")
        print _("to abort and don't let him start with pyload.py automatically anymore.")
        print
        print
        raw_input(_("When you are ready for system check, hit enter."))
        print
        print

        basic, ssl, captcha, web, js = self.system_check()
        print
        print

        if not basic:
            print _("You need pycurl, sqlite and python 2.5, 2.6 or 2.7 to run pyLoad.")
            print _("Please correct this and re-run pyLoad.")
            print
            print _("Setup will now close.")
            print
            print
            raw_input(_("Press Enter to exit."))
            return False

        raw_input(_("System check finished, hit enter to see your status report."))
        print
        print
        print _("## Status ##")
        print

        avail = []
        if self.check_module("Crypto"):
            avail.append(_("container decrypting"))
        if ssl:
            avail.append(_("ssl connection"))
        if captcha:
            avail.append(_("automatic captcha decryption"))
        if web:
            avail.append(_("webinterface"))
        if js:
            avail.append(_("extended Click'N'Load"))

        string = ""

        for av in avail:
            string += ", " + av

        print _("AVAILABLE FEATURES:") + string[1:]
        print

        if len(avail) < 5:
            print _("MISSING FEATURES: ")

            if not self.check_module("Crypto"):
                print _("- no py-crypto available")
                print _("You need this if you want to decrypt container files.")
                print

            if not ssl:
                print _("- no SSL available")
                print _("This is needed if you want to establish a secure connection to core or webinterface.")
                print _("If you only want to access locally to pyLoad ssl is not usefull.")
                print

            if not captcha:
                print _("- no Captcha Recognition available")
                print _("Only needed for some hosters and as freeuser.")
                print

            if not js:
                print _("- no JavaScript engine found")
                print _("You will need this for some Click'N'Load links. Install Spidermonkey, ossp-js, pyv8 or rhino")
                print

            print
            print _("You can abort the setup now and fix some dependicies if you want.")

        print
        con = self.ask(_("Continue with setup?"), self.yes, bool=True)

        if not con:
            return False

        print
        print
        print _("CURRENT CONFIG PATH: %s") % abspath("")
        print
        print _("NOTE: If you use pyLoad on a server or the home partition lives on an iternal flash it may be a good idea to change it.")
        path = self.ask(_("Do you want to change the config path?"), self.no, bool=True)
        if path:
            print
            self.conf_path()
            #calls exit when changed

        print
        print _("Do you want to configure login data and basic settings?")
        print _("This is recommend for first run.")
        con = self.ask(_("Make basic setup?"), self.yes, bool=True)

        if con:
            print
            print
            self.conf_basic()

        if ssl:
            print
            print _("Do you want to configure ssl?")
            ssl = self.ask(_("Configure ssl?"), self.no, bool=True)
            if ssl:
                print
                print
                self.conf_ssl()

        if web:
            print
            print _("Do you want to configure webinterface?")
            web = self.ask(_("Configure webinterface?"), self.yes, bool=True)
            if web:
                print
                print
                self.conf_web()

        print
        print
        print _("Setup finished successfully!")
        print
        print
        raw_input(_("Hit enter to exit and restart pyLoad."))
        return True


    def system_check(self):
        """ make a systemcheck and return the results"""

        print _("## System Information ##")
        print
        print _("Platform: %s") % sys.platform
        print _("Operating System: %s") % os.name
        print _("Python: %s") % sys.version.replace("\n", "")
        print
        print

        print _("## System Check ##")
        print

        if sys.version_info[:2] > (2, 7):
            print _("Your python version is to new, Please use Python 2.6/2.7")
            python = False
        elif sys.version_info[:2] < (2, 5):
            print _("Your python version is to old, Please use at least Python 2.5")
            python = False
        else:
            print _("Python Version: OK")
            python = True

        curl = self.check_module("pycurl")
        self.print_dep("pycurl", curl)

        sqlite = self.check_module("sqlite3")
        self.print_dep("sqlite3", sqlite)

        basic = python and curl and sqlite

        print

        crypto = self.check_module("Crypto")
        self.print_dep("pycrypto", crypto)

        ssl = self.check_module("OpenSSL")
        self.print_dep("py-OpenSSL", ssl)

        print

        pil = self.check_module("PIL.Image")
        self.print_dep("PIL/Pillow", pil)

        if os.name == "nt":
            tesser = self.check_prog([join(pypath, "tesseract", "tesseract.exe"), "-v"])
        else:
            tesser = self.check_prog(["tesseract", "-v"])

        self.print_dep("tesseract", tesser)

        captcha = pil and tesser

        print

        try:
            import jinja2

            v = jinja2.__version__
            if v and versiontuple(v) < (2, 5, 0):
                jinja = False
            else:
                jinja = True
        except:
            jinja = False

        jinja = self.print_dep("jinja2", jinja)

        beaker = self.check_module("beaker")
        self.print_dep("beaker", beaker)

        bjoern = self.check_module("bjoern")
        self.print_dep("bjoern", bjoern)

        web = sqlite and beaker

        from pyload.utils import JsEngine
        js = True if JsEngine.ENGINE else False
        self.print_dep(_("JS engine"), js)

        if not jinja:
            print
            print
            print _("WARNING: Your installed jinja2 version %s seems too old.") % jinja2.__version__
            print _("You can safely continue but if the webinterface is not working,")
            print _("please upgrade or uninstall it, because pyLoad self-includes jinja2 libary.")

        return basic, ssl, captcha, web, js


    def conf_basic(self):
        print _("## Basic Setup ##")

        print
        print _("The following logindata is valid for CLI and webinterface.")
        
        from pyload.database import DatabaseBackend

        db = DatabaseBackend(None)
        db.setup()
        print _("NOTE: Consider a password of 10 or more symbols if you expect to access from outside your local network (ex. internet).")
        print
        username = self.ask(_("Username"), "User")
        password = self.ask("", "", password=True)
        db.addUser(username, password)
        db.shutdown()

        print
        print _("External clients (GUI, CLI or other) need remote access to work over the network.")
        print _("However, if you only want to use the webinterface you may disable it to save ram.")
        self.config["remote"]["activated"] = self.ask(_("Enable remote access"), self.no, bool=True)

        print
        langs = self.config.getMetaData("general", "language")
        self.config["general"]["language"] = self.ask(_("Choose pyLoad language"), "en", langs["type"].split(";"))

        print
        self.config["general"]["download_folder"] = self.ask(_("Download folder"), "Downloads")
        print
        self.config["download"]["max_downloads"] = self.ask(_("Max parallel downloads"), "3")
        print
        reconnect = self.ask(_("Use Reconnect?"), self.no, bool=True)
        self.config["reconnect"]["activated"] = reconnect
        if reconnect:
            self.config["reconnect"]["method"] = self.ask(_("Reconnect script location"), "./reconnect.sh")


    def conf_web(self):
        print _("## Webinterface Setup ##")

        print
        self.config["webinterface"]["activated"] = self.ask(_("Activate webinterface?"), self.yes, bool=True)
        print
        print _("Listen address, if you use 127.0.0.1 or localhost, the webinterface will only accessible locally.")
        self.config["webinterface"]["host"] = self.ask(_("Address"), "0.0.0.0")
        self.config["webinterface"]["port"] = self.ask(_("Port"), "8000")
        print
        print _("pyLoad offers several server backends, now following a short explanation.")
        print "- builtin:", _("Default server; best choice if you plan to use pyLoad just for you.")
        print "- threaded:", _("Support SSL connection and can serve simultaneously more client flawlessly.")
        print "- fastcgi:", _(
            "Can be used by apache, lighttpd, etc.; needs to be properly configured before.")
        if os.name != "nt":
            print "- lightweight:", _("Very fast alternative to builtin; requires libev and bjoern packages.")

        print
        print _("NOTE: In some rare cases the builtin server is not working, if you notice problems with the webinterface")
        print _("come back here and change the builtin server to the threaded one here.")

        if os.name == "nt":
            servers = ["builtin", "threaded", "fastcgi"]
            default = "threaded"
        else:
            servers = ["builtin", "threaded", "fastcgi", "lightweight"]
            default = "lightweight" if self.check_module("bjoern") else "builtin"

        self.config["webinterface"]["server"] = self.ask(_("Server"), default, servers)


    def conf_ssl(self):
        print _("## SSL Setup ##")
        print
        print _("Execute these commands from pyLoad config folder to make ssl certificates:")
        print
        print "openssl genrsa -out ssl.key 1024"
        print "openssl req -new -key ssl.key -out ssl.csr"
        print "openssl req -days 36500 -x509 -key ssl.key -in ssl.csr > ssl.crt "
        print
        print _("If you're done and everything went fine, you can activate ssl now.")

        self.config["ssl"]["activated"] = self.ask(_("Activate SSL?"), self.yes, bool=True)


    def set_user(self):
        gettext.setpaths([join(os.sep, "usr", "share", "pyload", "locale"), None])
        translation = gettext.translation("setup", join(self.path, "locale"),
            languages=[self.config["general"]["language"], "en"], fallback=True)
        translation.install(True)

        from pyload.database import DatabaseBackend

        db = DatabaseBackend(None)
        db.setup()

        noaction = True
        try:
            while True:
                print _("Select action")
                print _("1 - Create/Edit user")
                print _("2 - List users")
                print _("3 - Remove user")
                print _("4 - Quit")
                action = raw_input("[1]/2/3/4: ")
                if not action in ("1", "2", "3", "4"):
                    continue
                elif action == "1":
                    print
                    username = self.ask(_("Username"), "User")
                    password = self.ask("", "", password=True)
                    db.addUser(username, password)
                    noaction = False
                elif action == "2":
                    print
                    print _("Users")
                    print "-----"
                    users = db.listUsers()
                    noaction = False
                    for user in users:
                        print user
                    print "-----"
                    print
                elif action == "3":
                    print
                    username = self.ask(_("Username"), "")
                    if username:
                        db.removeUser(username)
                        noaction = False
                elif action == "4":
                    break
        finally:
            if not noaction:
                db.shutdown()


    def conf_path(self, trans=False):
        if trans:
            gettext.setpaths([join(os.sep, "usr", "share", "pyload", "locale"), None])
            translation = gettext.translation("setup", join(self.path, "locale"),
                languages=[self.config["general"]["language"], "en"], fallback=True)
            translation.install(True)

        print _("Setting new config path, current configuration will not be transfered!")
        path = self.ask(_("CONFIG PATH"), abspath(""))
        try:
            path = join(pypath, path)
            if not exists(path):
                makedirs(path)
            f = open(join(pypath, "pyload", "config", "configdir"), "wb")
            f.write(path)
            f.close()
            print
            print
            print _("pyLoad config path changed, setup will now close!")
            print
            print
            raw_input(_("Press Enter to exit."))
            sys.exit()
        except Exception, e:
            print _("Setting config path failed: %s") % str(e)


    def print_dep(self, name, value):
        """Print Status of dependency"""
        if value:
            print _("%s: OK") % name
        else:
            print _("%s: MISSING") % name


    def check_module(self, module):
        try:
            __import__(module)
            return True
        except:
            return False


    def check_prog(self, command):
        pipe = PIPE
        try:
            call(command, stdout=pipe, stderr=pipe)
            return True
        except:
            return False


    def ask(self, qst, default, answers=[], bool=False, password=False):
        """produce one line to asking for input"""
        if answers:
            info = "("

            for i, answer in enumerate(answers):
                info += (", " if i != 0 else "") + str((answer == default and "[%s]" % answer) or answer)

            info += ")"
        elif bool:
            if default == self.yes:
                info = "([%s]/%s)" % (self.yes, self.no)
            else:
                info = "(%s/[%s])" % (self.yes, self.no)
        else:
            info = "[%s]" % default

        if password:
            p1 = True
            p2 = False
            pwlen = 8
            while p1 != p2:
                # getpass(_("Password: ")) will crash on systems with broken locales (Win, NAS)
                sys.stdout.write(_("Password: "))
                p1 = getpass("")

                if len(p1) < pwlen:
                    print _("Password too short! Use at least %s symbols." % pwlen)
                    continue
                elif not p1.isalnum():
                    print _("Password must be alphanumeric.")
                    continue

                sys.stdout.write(_("Password (again): "))
                p2 = getpass("")

                if p1 == p2:
                    return p1
                else:
                    print _("Passwords did not match.")

        while True:
            try:
                input = raw_input(qst + " %s: " % info)
            except KeyboardInterrupt:
                print "\nSetup interrupted"
                sys.exit()

            input = input.decode(self.stdin_encoding)

            if input.strip() == "":
                input = default

            if bool:
                # yes, true, t are inputs for booleans with value true
                if input.lower().strip() in [self.yes, _("yes"), _("true"), _("t"), "yes"]:
                    return True
                # no, false, f are inputs for booleans with value false
                elif input.lower().strip() in [self.no, _("no"), _("false"), _("f"), "no"]:
                    return False
                else:
                    print _("Invalid Input")
                    continue

            if not answers:
                return input

            else:
                if input in answers:
                    return input
                else:
                    print _("Invalid Input")
