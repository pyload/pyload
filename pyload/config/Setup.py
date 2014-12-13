# -*- coding: utf-8 -*-
# @author: vuolter

from __future__ import with_statement

import __builtin__

import os
import sys

from getpass import getpass
from os import chdir, makedirs, path
from subprocess import PIPE, call

from pyload.network.JsEngine import JsEngine
from pyload.utils import get_console_encoding, load_translation, safe_join, versiontuple


class SetupAssistant(object):
    """ pyLoads initial setup configuration assistant """

    def __init__(self, config):
        self.config         = config
        self.lang           = "en"
        self.stdin_encoding = get_console_encoding(sys.stdin.encoding)


    def start(self):
        print
        langs = sorted(self.config.getMetaData("general", "language")['type'].split(";"))
        self.lang = self.ask(u"Choose setup language", "en", langs)

        load_translation("setup", self.lang)

        #Input shorthand for yes
        self.yes = _("y")
        #Input shorthand for no
        self.no = _("n")

        #        print
        #        print _("Would you like to configure pyLoad via Webinterface?")
        #        print _("You need a Browser and a connection to this PC for it.")
        #        viaweb = self.ask(_("Start initial webinterface for configuration?"), "y", bool=True)
        #        ...

        print
        print
        print _("## Welcome to the pyLoad Configuration Assistant ##")
        print
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
            avail.append(_("- container decrypting"))
        if ssl:
            avail.append(_("- ssl connection"))
        if captcha:
            avail.append(_("- automatic captcha decryption"))
        if web:
            avail.append(_("- webinterface"))
        if js:
            avail.append(_("- extended Click'N'Load"))

        if avail:
            print _("AVAILABLE FEATURES:")
            for feature in avail:
                print feature
            print

        if len(avail) < 5:
            print _("MISSING FEATURES:")

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
        else:
            print _("NO MISSING FEATURES!")

        print
        print
        con = self.ask(_("Continue with setup?"), self.yes, bool=True)

        if not con:
            return False

        print
        print
        print _("CURRENT CONFIG PATH: %s") % configdir
        print
        print _("NOTE: If you use pyLoad on a server or the home partition lives on an iternal flash it may be a good idea to change it.")
        confpath = self.ask(_("Do you want to change the config path?"), self.no, bool=True)
        if confpath:
            print
            self.conf_path()
            print

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
        """ make a systemcheck and return the results """
        import platform

        print _("## System Information ##")
        print
        print _("Platform:    ") + platform.platform(aliased=True)
        print _("OS:          ") + platform.system() or "Unknown"
        print _("Python:      ") + sys.version.replace("\n", "")
        print
        print

        print _("## System Check ##")
        print

        if (2, 5) > sys.version_info > (2, 7):
            python = False
        else:
            python = True

        self.print_dep("python", python, false="NOT OK")

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

        pil = self.check_module("Image")
        self.print_dep("py-imaging", pil)

        if os.name == "nt":
            tesser = self.check_prog([path.join(pypath, "tesseract", "tesseract.exe"), "-v"])
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
        except Exception:
            jinja = False
            jinja_error = "MISSING"
        else:
            jinja_error = "NOT OK"

        self.print_dep("jinja2", jinja, false=jinja_error)

        beaker = self.check_module("beaker")
        self.print_dep("beaker", beaker)

        bjoern = self.check_module("bjoern")
        self.print_dep("bjoern", bjoern)

        web = sqlite and beaker

        js = True if JsEngine.find() else False
        self.print_dep(_("JS engine"), js)

        if not python:
            print
            print
            if sys.version_info > (2, 7):
                print _("WARNING: Your python version is too NEW!")
                print _("Please use Python version 2.6/2.7 .")
            else:
                print _("WARNING: Your python version is too OLD!")
                print _("Please use at least Python version 2.5 .")

        if not jinja and jinja_error == "NOT OK":
            print
            print
            print _("WARNING: Your installed jinja2 version %s is too OLD!") % jinja2.__version__
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
        print _("NOTE: Consider a password of 10 or more symbols if you expect to access to your local network from outside (ex. internet).")
        print
        username = self.ask(_("Username"), "User")
        password = self.ask("", "", password=True)
        db.addUser(username, password)
        db.shutdown()

        print
        print _("External clients (GUI, CLI or other) need remote access to work over the network.")
        print _("However, if you only want to use the webinterface you may disable it to save ram.")
        self.config.set("remote", "activated", self.ask(_("Enable remote access"), self.no, bool=True))

        print
        langs = sorted(self.config.getMetaData("general", "language")['type'].split(";"))
        self.config.set("general", "language", self.ask(_("Choose system language"), self.lang, langs))

        print
        self.config.set("general", "download_folder", self.ask(_("Download folder"), "Downloads"))
        print
        self.config.set("download", "max_downloads", self.ask(_("Max parallel downloads"), "3"))
        print
        reconnect = self.ask(_("Use Reconnect?"), self.no, bool=True)
        self.config.set("reconnect", "activated", reconnect)
        if reconnect:
            self.config.set("reconnect", "method", self.ask(_("Reconnect script location"), "./reconnect.sh"))


    def conf_web(self):
        print _("## Webinterface Setup ##")

        print
        print _("Listen address, if you use 127.0.0.1 or localhost, the webinterface will only accessible locally.")
        self.config.set("webui", "host", self.ask(_("Address"), "0.0.0.0"))
        self.config.set("webui", "port", self.ask(_("Port"), "8000"))
        print
        print _("pyLoad offers several server backends, now following a short explanation.")
        print "- auto:", _("Automatically choose the best webserver for your platform.")
        print "- builtin:", _("First choice if you plan to use pyLoad just for you.")
        print "- threaded:", _("Support SSL connection and can serve simultaneously more client flawlessly.")
        print "- fastcgi:", _(
            "Can be used by apache, lighttpd, etc.; needs to be properly configured before.")
        if os.name != "nt":
            print "- lightweight:", _("Very fast alternative to builtin; requires libev and bjoern packages.")

        print
        print _("NOTE: In some rare cases the builtin server not works correctly, so if you have troubles with the web interface")
        print _("run this setup assistant again and change the builtin server to the threaded.")

        if os.name == "nt":
            servers = ["auto", "builtin", "threaded", "fastcgi"]
        else:
            servers = ["auto", "builtin", "threaded", "fastcgi", "lightweight"]

        self.config.set("webui", "server", self.ask(_("Choose webserver"), "auto", servers))


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

        ssl = self.ask(_("Activate SSL?"), self.yes, bool=True)
        self.config.set("remote", "ssl", ssl)
        self.config.set("webui", "ssl", ssl)


    def set_user(self):
        load_translation("setup", self.config.get("general", "language"))

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


    def set_configdir(self, configdir, persistent=False):
        dirname = path.abspath(configdir)
        try:
            if not path.exists(dirname):
                makedirs(dirname, 0700)

            chdir(dirname)
            
            if persistent:
                c = path.join(rootdir, "config", "configdir")
                if not path.exists(c):
                    makedirs(c, 0700)

                with open(c, "wb") as f:
                    f.write(dirname)

        except IOError:
            return False

        else:
            __builtin__.configdir = dirname
            return dirname  #: return always abspath


    def conf_path(self):
        print _("Setting new config path.")
        print _("NOTE: Current configuration will not be transfered!")

        while True:
            confdir = self.ask(_("CONFIG PATH"), configdir)
            confpath = self.set_configdir(confdir)
            print
            if not confpath:
                print _("Failed to change the current config path!")
                print
            else:
                print _("pyLoad config path successfully changed.")
                break


    def print_dep(self, name, value, false="MISSING", true="OK"):
        """ Print Status of dependency """
        if value and isinstance(value, basestring):
            msg = "%(dep)-12s %(bool)s  (%(info)s)"
        else:
            msg = "%(dep)-12s %(bool)s"

        print msg % {'dep': name + ':',
                     'bool': _(true if value else false).upper(),
                     'info': ", ".join(value)}


    def check_module(self, module):
        try:
            __import__(module)
            return True
        except Exception:
            return False


    def check_prog(self, command):
        pipe = PIPE
        try:
            call(command, stdout=pipe, stderr=pipe)
            return True
        except Exception:
            return False


    def ask(self, qst, default, answers=[], bool=False, password=False):
        """ produce one line to asking for input """
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
                    print
                    continue

            if not answers or input in answers:
                return input
            else:
                print _("Invalid Input")
