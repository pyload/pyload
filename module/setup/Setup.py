#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 3 of the License,
    or (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
    See the GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program; if not, see <http://www.gnu.org/licenses/>.
    
    @author: RaNaN
"""
from getpass import getpass
import module.common.pylgettext as gettext
import os
from os import makedirs
from os.path import abspath, dirname, exists, join
from subprocess import PIPE, call
import sys
from sys import exit
from module.utils import get_console_encoding
from module.setup.System_Checks import System_Checks
from module.setup.Questions import Questions, Ask
class Setup():
    """
    pyLoads initial setup configuration assistent
    """

    def __init__(self, path, config):
        self.path = path
        self.config = config
        self.stdin_encoding = get_console_encoding(sys.stdin.encoding)
        self.yes = "yes"
        self.no = "no"
        self.lang = None
        self.page = 0
        
        
    def start(self):
        self.ask_lang()
        checker = System_Checks()
        result_s, result_b = checker.check_basic()
        if not result_b:
            print result_s
        
        print ""
        print _("Would you like to configure pyLoad via Webinterface?")
        print _("You need a Browser and a connection to this PC for it.")
        print _("Url would be: http://hostname:8000/")
        viaweb = self.ask_cli(_("Start initial webinterface for configuration?"), self.yes, bool=True)
        if viaweb:
            self.start_web()
        else:
            self.start_cli()


    def ask_lang(self):
        if self.lang == None:
            langs = self.config.getMetaData("general", "language").type.split(";")
            self.lang = self.ask_cli(u"Choose your Language / Wähle deine Sprache", "en", langs)
            gettext.setpaths([join(os.sep, "usr", "share", "pyload", "locale"), None])
            translation = gettext.translation("setup", join(self.path, "locale"), languages=[self.lang, "en"], fallback=True)
            translation.install(True)

            #l10n Input shorthand for yes
            self.yes = _("y")
            #l10n Input shorthand for no
            self.no = _("n")

    def get_page_next(self):
        self.__print_start()
        if self.page == 0:
            # system check
            self.basic, self.ssl, self.captcha, self.web, self.js = self.system_check()
            if not basic:
                self.__print( _("You need pycurl, sqlite and python 2.5, 2.6 or 2.7 to run pyLoad."))
                self.__print( _("Please correct this and re-run pyLoad."))
                self.__print( _("Setup will now close."))
                self.__print_end()
                return False
            self.__print("")
            self.__print(_("## Status ##"))
            self.__print("")

            avail = []
            if self.check_module("Crypto"): avail.append(_("container decrypting"))
            if ssl: avail.append(_("ssl connection"))
            if captcha: avail.append(_("automatic captcha decryption"))
            if web: avail.append(_("Webinterface"))
            if js: avail.append(_("extended Click'N'Load"))

            string = ""
            for av in avail:
                string += ", " + av
            # List available Features
            self.__print(_("Features available:") + string[1:])
            self.__print("")

        return self.printer
            
    def __print(self, text):
        if self.web == True:
            self.printer += "<br />" + text
        else:
            print text
            
    def __print_start(self):
        if self.web == True:
            self.printer = ""
        else:
            print ""

    def __print_end(self):
        if self.web == True:
            self.printer = ""
        else:
            raw_input()

    def ask(self, qst, default, answers=[], bool=False, password=False):
        if self.web == True:
            self.ask_web(qst, default, answers, bool, password)
        else:
            self.ask_cli(qst, default, answers, bool, password)


    def start_cli(self):


        for ask in Questions.questions:
            if ask.webonly: continue
            for line in ask.sqt:
                print line
            if default == None:
                raw_input()
        
        print _("Welcome to the pyLoad Configuration Assistent.")
        print _("It will check your system and make a basic setup in order to run pyLoad.")
        print ""
        print _("The value in brackets [] always is the default value,")
        print _("in case you don't want to change it or you are unsure what to choose, just hit enter.")
        print _(
            "Don't forget: You can always rerun this assistent with --setup or -s parameter, when you start pyLoadCore.")
        print _("If you have any problems with this assistent hit STRG-C,")
        print _("to abort and don't let him start with pyLoadCore automatically anymore.")
        print ""
        print _("When you are ready for system check, hit enter.")
        raw_input()

        #self.get_page_next()






        if len(avail) < 5:
            print _("Features missing: ")
            print

            if not self.check_module("Crypto"):
                print _("no py-crypto available")
                print _("You need this if you want to decrypt container files.")
                print ""

            if not ssl:
                print _("no SSL available")
                print _("This is needed if you want to establish a secure connection to core or webinterface.")
                print _("If you only want to access locally to pyLoad ssl is not useful.")
                print ""

            if not captcha:
                print _("no Captcha Recognition available")
                print _("Only needed for some hosters and as freeuser.")
                print ""

            if not js:
                print _("no JavaScript engine found")
                print _("You will need this for some Click'N'Load links. Install Spidermonkey, ossp-js, pyv8 or rhino")

            print _("You can abort the setup now and fix some dependencies if you want.")

        con = self.ask(_("Continue with setup?"), self.yes, bool=True)

        if not con:
            return False

        print ""
        print _("Do you want to change the config path? Current is %s") % abspath("")
        print _(
            "If you use pyLoad on a server or the home partition lives on an internal flash it may be a good idea to change it.")
        path = self.ask(_("Change config path?"), self.no, bool=True)
        if path:
            self.conf_path()
            #calls exit when changed

        print ""
        print _("Do you want to configure login data and basic settings?")
        print _("This is recommend for first run.")
        con = self.ask(_("Make basic setup?"), self.yes, bool=True)

        if con:
            self.conf_basic()

        if ssl:
            print ""
            print _("Do you want to configure ssl?")
            ssl = self.ask(_("Configure ssl?"), self.no, bool=True)
            if ssl:
                self.conf_ssl()

        if web:
            print ""
            print _("Do you want to configure webinterface?")
            web = self.ask(_("Configure webinterface?"), self.yes, bool=True)
            if web:
                self.conf_web()

        print ""
        print _("Setup finished successfully.")
        print _("Hit enter to exit and restart pyLoad")
        raw_input()
        return True
    
        
    def start_web(self):
        print ""
        print _("Webinterface running for setup.")
        # TODO start browser?
        try:
            from module.web import ServerThread
            ServerThread.setup = self
            from module.web import webinterface
            webinterface.run_simple()
            self.web = True
            return True
        except Exception, e:
            print "Webinterface failed with this error: ", e
            print "Falling back to commandline setup."
            self.start_cli()



    def conf_basic(self):
        print ""
        print _("## Basic Setup ##")

        print ""
        print _("The following logindata is valid for CLI, GUI and webinterface.")

        from module.database import DatabaseBackend

        db = DatabaseBackend(None)
        db.setup()
        username = self.ask(_("Username"), "User")
        password = self.ask("", "", password=True)
        db.addUser(username, password)
        db.shutdown()

        print ""
        print _("External clients (GUI, CLI or other) need remote access to work over the network.")
        print _("However, if you only want to use the webinterface you may disable it to save ram.")
        self.config["remote"]["activated"] = self.ask(_("Enable remote access"), self.yes, bool=True)

        print ""
        langs = self.config.getMetaData("general", "language")
        self.config["general"]["language"] = self.ask(_("Language"), "en", langs.type.split(";"))

        self.config["general"]["download_folder"] = self.ask(_("Downloadfolder"), "Downloads")
        self.config["download"]["max_downloads"] = self.ask(_("Max parallel downloads"), "3")
        #print _("You should disable checksum proofing, if you have low hardware requirements.")
        #self.config["general"]["checksum"] = self.ask(_("Proof checksum?"), "y", bool=True)

        reconnect = self.ask(_("Use Reconnect?"), self.no, bool=True)
        self.config["reconnect"]["activated"] = reconnect
        if reconnect:
            self.config["reconnect"]["method"] = self.ask(_("Reconnect script location"), "./reconnect.sh")


    def conf_web(self):
        print ""
        print _("## Webinterface Setup ##")

        print ""
        self.config["webinterface"]["activated"] = self.ask(_("Activate webinterface?"), self.yes, bool=True)
        print ""
        print _("Listen address, if you use 127.0.0.1 or localhost, the webinterface will only accessible locally.")
        self.config["webinterface"]["host"] = self.ask(_("Address"), "0.0.0.0")
        self.config["webinterface"]["port"] = self.ask(_("Port"), "8000")
        print ""
        print _("pyLoad offers several server backends, now following a short explanation.")
        print "builtin:", _("laggy, but useful if RAM ")
        print "threaded:", _("Default server, this server offers SSL and is a good alternative to builtin.")
        print "fastcgi:", _(
            "Can be used by apache, lighttpd, requires you to configure them, which is not too easy job.")
        print "lightweight:", _("Very fast alternative written in C, requires libev and linux knowledge.")
        print "\t", _("Get it from here: https://github.com/jonashaag/bjoern, compile it")
        print "\t", _("and copy bjoern.so to module/lib")

        print
        print _(
            "Attention: In some rare cases the builtin server is not working, if you notice problems with the webinterface")
        print _("come back here and change the builtin server to the threaded one here.")

        self.config["webinterface"]["server"] = self.ask(_("Server"), "threaded",
            ["builtin", "threaded", "fastcgi", "lightweight"])

    def conf_ssl(self):
        print ""
        print _("## SSL Setup ##")
        print ""
        print _("Execute these commands from pyLoad config folder to make ssl certificates:")
        print ""
        print "openssl genrsa -out ssl.key 1024"
        print "openssl req -new -key ssl.key -out ssl.csr"
        print "openssl req -days 36500 -x509 -key ssl.key -in ssl.csr > ssl.crt "
        print ""
        print _("If you're done and everything went fine, you can activate ssl now.")
        self.config["ssl"]["activated"] = self.ask(_("Activate SSL?"), self.yes, bool=True)

    def set_user(self):
        gettext.setpaths([join(os.sep, "usr", "share", "pyload", "locale"), None])
        translation = gettext.translation("setup", join(self.path, "locale"),
            languages=[self.config["general"]["language"], "en"], fallback=True)
        translation.install(True)

        from module.database import DatabaseBackend

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
                    print ""
                    username = self.ask(_("Username"), "User")
                    password = self.ask("", "", password=True)
                    db.addUser(username, password)
                    noaction = False
                elif action == "2":
                    print ""
                    print _("Users")
                    print "-----"
                    users = db.getAllUserData()
                    noaction = False
                    for user in users.itervalues():
                        print user.name
                    print "-----"
                    print ""
                elif action == "3":
                    print ""
                    username = self.ask(_("Username"), "")
                    if username:
                        db.removeUser(username)
                        noaction = False
                elif action == "4":
                    db.syncSave()
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

        print _("Setting new configpath, current configuration will not be transferred!")
        path = self.ask(_("Configpath"), abspath(""))
        try:
            path = join(pypath, path)
            if not exists(path):
                makedirs(path)
            f = open(join(pypath, "module", "config", "configdir"), "wb")
            f.write(path)
            f.close()
            print _("Configpath changed, setup will now close, please restart to go on.")
            print _("Press Enter to exit.")
            raw_input()
            exit()
        except Exception, e:
            print _("Setting config path failed: %s") % str(e)






    def ask_cli(self, qst, default, answers=[], bool=False, password=False):
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
            while p1 != p2:
                # getpass(_("Password: ")) will crash on systems with broken locales (Win, NAS)
                sys.stdout.write(_("Password: "))
                p1 = getpass("")

                if len(p1) < 4:
                    print _("Password too short. Use at least 4 symbols.")
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
                exit()

            input = input.decode(self.stdin_encoding)

            if input.strip() == "":
                input = default

            if bool:
                #l10n yes, true,t are inputs for booleans with value true
                if input.lower().strip() in [self.yes, _("yes"), _("true"), _("t"), "yes"]:
                    return True
                #l10n no, false,f are inputs for booleans with value false
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


if __name__ == "__main__":
    test = Setup(join(abspath(dirname(__file__)), ".."), None)
    test.start()
