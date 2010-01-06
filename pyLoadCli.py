#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#Copyright (C) 2009 RaNaN
#
#This program is free software; you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation; either version 3 of the License,
#or (at your option) any later version.
#
#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#See the GNU General Public License for more details.
#
#You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>.
#
###
import ConfigParser
import subprocess
import os
import os.path
from os import chdir
from os.path import join
from os.path import abspath
from os.path import dirname
from os import sep
from time import sleep
import sys
import time
import threading
import xmlrpclib

from module.XMLConfigParser import XMLConfigParser

class pyLoadCli:
    def __init__(self, server_url):
        self.core = xmlrpclib.ServerProxy(server_url, allow_none=True)
        self.getch = _Getch()
        self.input = ""
        self.pos = [0, 0, 0]
        self.inputline = 0
        self.menuline = 0

        self.new_package = {}

        try:
            self.core.get_server_version()
        except:
            print "pyLoadCore not running"
            exit()

        self.links_added = 0

        os.system("clear")
        self.println(1, blue("py") + yellow("Load") + white(" Command Line Interface"))
        self.println(2, "")


        self.file_list = {}

        self.thread = RefreshThread(self)
        self.thread.start()

        self.start()

    def start(self):
        while True:
            #inp = raw_input()
            inp = self.getch.impl()
            if ord(inp) == 3:
                os.system("clear")
                sys.exit() # ctrl + c
            elif ord(inp) == 13:
                try:
                    self.handle_input()
                except Exception, e:
                    self.println(2, red(str(e)))
                self.input = ""   #enter
                self.print_input()
            elif ord(inp) == 127:
                self.input = self.input[:-1] #backspace
                self.print_input()
            elif ord(inp) == 27: #ugly symbol
                pass
            else:
                self.input += inp
                self.print_input()

    def format_time(self, seconds):
        seconds = int(seconds)
        
        hours, seconds = divmod(seconds, 3600)
        minutes, seconds = divmod(seconds, 60)
        return "%.2i:%.2i:%.2i" % (hours, minutes, seconds)
    
    def format_size(self, size):
        return str(size / 1024) + " MiB"

    def println(self, line, content):
        print "\033[" + str(line) + ";0H\033[2K" + str(content) + "\033[" + str((self.inputline if self.inputline > 0 else self.inputline + 1) - 1) + ";0H"

    def print_input(self):
        self.println(self.inputline, white(" Input: ") + self.input)
        self.println(self.inputline + 1, "")
        self.println(self.inputline + 2, "")
        self.println(self.inputline + 3, "")
        self.println(self.inputline + 4, "")

    def refresh(self):
        """Handle incoming data"""
        data = self.core.status_downloads()
            #print updated information
        print "\033[J" #clear screen
        self.println(1, blue("py") + yellow("Load") + white(" Command Line Interface"))
        self.println(2, "")
        self.println(3, white("%s Downloads:" % (len(data))))
        line = 4
        speed = 0
        for download in data:
            if download["status"] == "downloading":
                percent = download["percent"]
                z = percent / 4
                speed += download['speed']
                self.println(line, cyan(download["name"]))
                line += 1
                self.println(line, blue("[") + yellow(z * "#" + (25-z) * " ") + blue("] ") + green(str(percent) + "%") + " Speed: " + green(str(int(download['speed'])) + " kb/s") + " Size: " + green(self.format_size(download['size'])) + " Finished in: " + green(self.format_time(download['eta']))  + " ID: " + green(str(download['id'])))
                line += 1
            if download["status"] == "waiting":
                self.println(line, cyan(download["name"]))
                line += 1
                self.println(line, "waiting: " + green(self.format_time(download["wait_until"]- time.time())))
                line += 1
        self.println(line, "")
        line += 1
        status = self.core.status_server()
        if status['pause']:
            self.println(line, "Status: " + red("paused") + " total Speed: " + red(str(int(speed)) + " kb/s") + " Files in queue: " + red(str(status["queue"])))
        else:
            self.println(line, "Status: " + red("running") + " total Speed: " + red(str(int(speed)) + " kb/s") + " Files in queue: " + red(str(status["queue"])))
        line += 1
        self.println(line, "")
        line += 1
        self.menuline = line
        
        self.build_menu()
        #
        self.file_list = data

    def build_menu(self):
        line = self.menuline
        self.println(line, white("Menu:"))
        line += 1 
        if self.pos[0] == 0:# main menu
            self.println(line, "")
            line += 1
            self.println(line, mag("1.") + " Add Links")
            line += 1
            self.println(line, mag("2.") + " Manage Links")
            line += 1
            self.println(line, mag("3.") + " (Un)Pause Server")
            line += 1
            self.println(line, mag("4.") + " Kill Server")
            line += 1
            self.println(line, mag("5.") + " Quit")
            line += 1
            self.println(line, "")
            line += 1
            self.println(line, "")
        elif self.pos[0] == 1:#add links    
            
            if self.pos[1] == 0:
                self.println(line, "")
                line += 1
                self.println(line, "Name your package.")
                line += 1
                self.println(line, "")
                line += 1
                self.println(line, "")
                line += 1
                self.println(line, "")
                line += 1
                self.println(line, "")
                line += 1
                self.println(line, mag("0.") + " back to main menu")
                line += 1
                self.println(line, "")
            
            else:
                self.println(line, "Package: %s" % self.new_package['name'])
                line += 1
                self.println(line, "Parse the links you want to add.")
                line += 1
                self.println(line, "Type "+mag("END")+" when done.")
                line += 1
                self.println(line, "Links added: " + mag(str(self.links_added)))
                line += 1
                self.println(line, "")
                line += 1
                self.println(line, "")
                line += 1
                self.println(line, mag("0.") + " back to main menu")
                line += 1
                self.println(line, "")
        elif self.pos[0] == 2:#remove links
            if self.pos[1] == 0:
                pack = self.core.get_queue()
                self.println(line, "Type d(number of package) to delete a package, or w/o d to look into it.")
                line += 1
                i = 0
                for id in range(self.pos[2], self.pos[2] + 5):
                    try:                
                        self.println(line, mag(str(pack[id]['id'])) + ": " + pack[id]['package_name'])
                        line += 1
                        i += 1
                    except Exception, e:
                        pass
                for x in range(5-i):
                    self.println(line, "")
                    line += 1
            
            else:
                links = self.core.get_package_files(self.pos[1])
                self.println(line, "Type the number of the link you want to delete or r(number) to restart.")
                line += 1
                i = 0
                for id in range(self.pos[2], self.pos[2] + 5):
                    try:
                        link = self.core.get_file_info(links[id])
                        
			if not link['status_filename']:
			    self.println(line, mag(str(link['id'])) + ": " + link['url'])
			else:
			    self.println(line, mag(str(link['id'])) + ": %s | %s | %s" % (link['filename'],link['status_type'],link['plugin']))
			line += 1
                        i += 1
                        
                    except Exception, e:
                        pass
                for x in range(5-i):
                    self.println(line, "")
                    line += 1
    
            self.println(line, mag("p") + " - previous" + " | " + mag("n") + " - next")
            line += 1
            self.println(line, mag("0.") + " back to main menu")
        
        self.inputline = line + 1
        self.print_input()

    def handle_input(self):
        inp = self.input.strip()
        if inp == "0":
            self.pos = [0, 0, 0]
            self.build_menu()
            return True

        if self.pos[0] == 0:
            if inp == "1":
                self.links_added = 0
                self.pos[0] = 1
            elif inp == "2":
                self.pos[0] = 2
                self.pos[1] = 0
            elif inp == "3":
                self.core.toggle_pause()
            elif inp == "4":
                self.core.kill()
                sys.exit()
            elif inp == "5":
                os.system('clear')
                sys.exit()
        
        elif self.pos[0] == 1: #add links
            if self.pos[1] == 0:
                self.new_package['name'] = inp
                self.new_package['links'] = []
                self.pos[1] = 1
            else:
                if inp == "END":
                    self.core.add_package(self.new_package['name'], self.new_package['links']) # add package
                    self.pos = [0, 0, 0]
                    self.links_added = 0
                else: #@TODO validation
                    self.new_package['links'].append(inp)
                    self.links_added += 1
                
        elif self.pos[0] == 2: #remove links
            if self.pos[1] == 0:
                if inp.startswith("d"):
                    self.core.del_packages([int(inp[1:])])
                elif inp != "p" and inp != "n":
                    self.pos[1] = int(inp)
                    self.pos[2] = 0
            elif inp.startswith('r'):
                self.core.restart_file(int(inp[1:]))
            elif inp != "p" and inp != "n":
                self.core.del_links([int(inp)])
                
            if inp == "p":
                self.pos[2] -= 5
            elif inp == "n":
                self.pos[2] += 5

        self.build_menu()

class RefreshThread(threading.Thread):
    def __init__(self, cli):
        threading.Thread.__init__(self)
        self.cli = cli
    
    def run(self):
        while True:
            sleep(1)
            try:
                self.cli.refresh()
            except Exception, e:
                self.cli.println(2, red(str(e)))
                self.cli.pos[1] = 0
                self.cli.pos[2] = 0
            
    



class _Getch:
    """
    Gets a single character from standard input.  Does not echo to
    the screen.
    """
    def __init__(self):
        try:
            self.impl = _GetchWindows()
        except ImportError:
            try:
                self.impl = _GetchMacCarbon()
            except(AttributeError, ImportError):
                self.impl = _GetchUnix()

    def __call__(self): return self.impl()


class _GetchUnix:
    def __init__(self):
        import tty
        import sys

    def __call__(self):
        import sys
        import tty
        import termios
        
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch


class _GetchWindows:
    def __init__(self):
        import msvcrt

    def __call__(self):
        import msvcrt
        return msvcrt.getch()

class _GetchMacCarbon:
    """
    A function which returns the current ASCII key that is down;
    if no ASCII key is down, the null string is returned.  The
    page http://www.mactech.com/macintosh-c/chap02-1.html was
    very helpful in figuring out how to do this.
    """
    def __init__(self):
        import Carbon
        Carbon.Evt #see if it has this (in Unix, it doesn't)

    def __call__(self):
        import Carbon
        if Carbon.Evt.EventAvail(0x0008)[0] == 0: # 0x0008 is the keyDownMask
            return ''
        else:
            #
            # The event contains the following info:
            # (what,msg,when,where,mod)=Carbon.Evt.GetNextEvent(0x0008)[1]
            #
            # The message (msg) contains the ASCII char which is
            # extracted with the 0x000000FF charCodeMask; this
            # number is converted to an ASCII character with chr() and
            # returned
            #
            (what, msg, when, where, mod) = Carbon.Evt.GetNextEvent(0x0008)[1]
            return chr(msg)

def blue(string):
    return "\033[1;34m" + string + "\033[0m"

def green(string):
    return "\033[1;32m" + string + "\033[0m"

def yellow(string):
    return "\033[1;33m" + string + "\033[0m"

def red(string):
    return "\033[1;31m" + string + "\033[0m"

def cyan(string):
    return "\033[1;36m" + string + "\033[0m"

def mag(string):
    return "\033[1;35m" + string + "\033[0m"

def white(string):
    return "\033[1;37m" + string + "\033[0m"

if __name__ == "__main__":

    if len(sys.argv) > 1:
        
        shortOptions = 'l'
        longOptions = ['local']

        opts, extraparams = __import__("getopt").getopt(sys.argv[1:], shortOptions, longOptions)
        for option, params in opts:
            if option in ("-l", "--local"):
                
                xmlconfig = XMLConfigParser(join(abspath(dirname(__file__)),"module","config","core.xml"), join(abspath(dirname(__file__)),"module","config","core_default.xml"))
                config = xmlconfig.getConfig()
                
                ssl= ""
                if config['ssl']['activated'] == "True":
                    ssl = "s"

                server_url = "http%s://%s:%s@%s:%s/" % (
                                        ssl,
                                        config['remote']['username'],
                                        config['remote']['password'],
                                        config['remote']['listenaddr'],
                                        config['remote']['port']
                                        )
        if len(extraparams) == 1:
            server_url = sys.argv[1]
    else:
        username = raw_input("Username: ")
        address = raw_input("Adress: ")
        ssl = raw_input("Use SSL? ([y]/n): ")
        if ssl == "y" or ssl == "":
            ssl = "s"
        else:
            ssl = ""
        port = raw_input("Port: ")
        from getpass import getpass
        password = getpass("Password: ")
        
        server_url = "http%s://%s:%s@%s:%s/" % (ssl, username, password, address, port)
    print server_url
    cli = pyLoadCli(server_url)
