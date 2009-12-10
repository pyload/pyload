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
    
    @author: mkaay
    @version: v0.3
"""

SERVER_VERSION = "0.3"

import curses
import traceback
import string
import os
from time import sleep, time
import xmlrpclib
from threading import RLock, Thread
import sys
import os.path
from os import chdir
from os.path import dirname
from os.path import abspath
from os import sep
import ConfigParser

class pyLoadCli:
    menu_items = []
    
    def __init__(self, stdscr, server_url):
        self.stdscr = stdscr
        self.lock = RLock()
        self.lock.acquire()
        self.stop = False
        
        self.download_win = None
        self.collectorbox = None
        self.add_win = None
        self.proxy = None
        
        self.downloads = []
        self.tmp_bind = []
        self.current_dwin_rows = 0
        self.lock.release()
        
        self.connect(server_url)
        
        self.lock.acquire()
        
        curses.init_pair(1, curses.COLOR_BLUE, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(4, curses.COLOR_CYAN, curses.COLOR_BLACK)
        curses.init_pair(5, curses.COLOR_BLACK, curses.COLOR_WHITE        )
        
        self.screen = self.stdscr.subwin(23, 79, 0, 0)
        self.screen.box()
        self.screen.addstr(1, 48, "py", curses.color_pair(1))
        self.screen.addstr(1, 50, "Load", curses.color_pair(2))
        self.screen.addstr(1, 55, "Command Line Interface")
        self.lock.release()
        
        self.add_menu("Status", "s", None)
        self.add_menu("Collector", "c", self.collector_menu)
        self.add_menu("Add-Link", "l", self.show_addl_box)
        self.add_menu("New-Package", "p", self.show_newp_box)
        self.add_menu("Quit", "q", self.exit)
        
        self.init_download_win()
        self.update_downloads()
    
    def connect(self, server_url):
        self.lock.acquire()
        self.proxy = xmlrpclib.ServerProxy(server_url, allow_none=True)
        server_version = self.proxy.get_server_version()
        self.lock.release()
        if not server_version == SERVER_VERSION:
            raise Exception("server is version %s client accepts version %s" % (server_version, SERVER_VERSION))
    
    def refresh(self):
        self.lock.acquire()
        self.screen.refresh()
        self.lock.release()
    
    def init_download_win(self):
        self.lock.acquire()
        rows = 2
        if self.current_dwin_rows != 0:
            rows = self.current_dwin_rows*3 + 1
        self.download_win = self.screen.subwin(rows, 75, 3, 2)
        self.download_win.box()
        self.lock.release()
    
    def adjust_download_win_size(self, down_num, force=False):
        if self.current_dwin_rows != down_num or force:
            self.lock.acquire()
            self.download_win.erase()
            self.current_dwin_rows = down_num
            self.lock.release()
            self.init_download_win()
            self.screen.redrawwin()
    
    def update_downloads(self):
        self.lock.acquire()
        self.downloads = self.proxy.status_downloads()
        self.lock.release()
        self.adjust_download_win_size(len(self.downloads))
        self.show_downloads()
    
    def show_downloads(self):
        self.lock.acquire()
        self.download_win.redrawwin()
        for r, d in enumerate(self.downloads):
            r = r*3+1
            if d["status"] == "downloading":
                self.download_win.addstr(r, 2, d["name"], curses.color_pair(4))
                self.download_win.addstr(r, 35, "[", curses.color_pair(1))
                self.download_win.addstr(r, 36, "#" * (int(d["percent"])/4), curses.color_pair(2))
                self.download_win.addstr(r, 61, "]", curses.color_pair(1))
                self.download_win.addstr(r, 63, "%s%%" % d["percent"], curses.color_pair(3))
                self.download_win.addstr(r+1, 8, "Speed:", curses.color_pair(0))
                self.download_win.addstr(r+1, 15, "%s kb/s" % int(d["speed"]), curses.color_pair(3))
                self.download_win.addstr(r+1, 25, "Size:", curses.color_pair(0))
                self.download_win.addstr(r+1, 31, self.format_size(d["size"]), curses.color_pair(3))
                self.download_win.addstr(r+1, 38, "ETA:", curses.color_pair(0))
                self.download_win.addstr(r+1, 43, self.format_time(d['eta']), curses.color_pair(3))
                self.download_win.addstr(r+1, 52, "ID:", curses.color_pair(0))
                self.download_win.addstr(r+1, 55, str(d["id"]), curses.color_pair(3))
            elif d["status"] == "waiting":
                self.download_win.addstr(r, 2, d["name"], curses.color_pair(4))
                self.download_win.addstr(r+1, 4, "waiting: " + self.format_time(d["wait_until"]- time()), curses.color_pair(3))
        self.lock.release()
        self.refresh()
    
    def show_addl_box(self):
        self.lock.acquire()
        curses.echo()
        box = self.screen.subwin(4, 75, 18, 2)
        box.box()
        self.lock.release()
        box.addstr(1, 2, "URL: (type 'END' if done)")
        rows = []
        while True:
            box.move(2, 2)
            s = box.getstr()
            if s == "END":
                break
            else:
                rows.append(s)
            box.addstr(2, 2, " "*72)
        box.erase()
        self.lock.acquire()
        curses.noecho()
        for row in rows:
            if row[:7] == "http://" or self.proxy.file_exists(row):
                self.proxy.add_urls([row])
        self.lock.release()
    
    def show_newp_box(self):
        self.lock.acquire()
        curses.echo()
        box = self.screen.subwin(4, 75, 18, 2)
        box.box()
        self.lock.release()
        box.addstr(1, 2, "Package Name:")
        box.move(2, 2)
        s = box.getstr()
        box.erase()
        self.lock.acquire()
        curses.noecho()
        id = self.proxy.new_package(s)
        self.lock.release()
        self.show_package_edit(id)
    
    def show_package_edit(self, id):
        self.lock.acquire()
        self.tmp_bind = []
        data = self.proxy.get_package_data(id)
        pfiles = self.proxy.get_package_files(id)
        box = self.screen.subwin(7+len(pfiles[0:5]), 71, 4, 4)
        box.box()
        box.bkgdset(" ", curses.color_pair(0))
        self.lock.release()
        box.addstr(1, 2, "ID: %(id)s" % data)
        box.addstr(2, 2, "Name: %(package_name)s" % data)
        box.addstr(3, 2, "Folder: %(folder)s" % data)
        box.addstr(4, 2, "Files in Package:")
        for r, fid in enumerate(pfiles[0:5]):
            data = self.proxy.get_file_info(fid)
            box.addstr(5+r, 2, "#%(id)d - %(url)s" % data)
        box.move(len(pfiles[0:5])+5, 2)
        self.show_link_collector()
        curses.echo()
        fid = box.getstr()
        curses.noecho()
        self.proxy.move_file_2_package(int(fid), id)
        box.erase()
        self.hide_collector()
        self.redraw()
    
    def show_link_collector(self):
        self.lock.acquire()
        cfiles = self.proxy.get_collector_files()
        self.collectorbox = self.screen.subwin(len(cfiles[0:5])+2, 71, 14, 4)
        self.collectorbox.box()
        for r, fid in enumerate(cfiles[0:5]):
            data = self.proxy.get_file_info(fid)
            self.collectorbox.addstr(r+1, 2, "#%(id)d - %(url)s" % data)
        self.lock.release()
    
    def show_package_collector(self):
        show = True
        page = 0
        rows_pp = 6
        while show:
            self.lock.acquire()
            cpack = self.proxy.get_collector_packages()
            self.collectorbox = self.screen.subwin(2+len(cpack[rows_pp*page:rows_pp*(page+1)]), 71, 14, 4)
            self.collectorbox.box()
            for r, data in enumerate(cpack[rows_pp*page:rows_pp*(page+1)]):
                self.collectorbox.addstr(r+1, 2, "#%(id)d - %(package_name)s" % data)
            self.lock.release()
            self.refresh()
            c = self.collectorbox.getch()
            if c == ord("n"):
                if page <= float(len(cpack))/float(rows_pp)-1:
                    page = page+1
            elif c == ord("p"):
                page = page-1
                if page < 0:
                    page = 0
            elif c == ord("d"):
                curses.echo()
                id = self.collectorbox.getstr()
                curses.noecho()
                self.proxy.push_package_2_queue(int(id))
            else:
                show = False
            self.hide_collector()
    
    def hide_collector(self):
        self.lock.acquire()
        self.collectorbox.erase()
        self.lock.release()
        
    def collector_menu(self):
        menu = self.screen.subwin(4, 12, 2, 10)
        menu.box()
        menu.addstr(1, 1, "  inks    ")
        menu.addstr(2, 1, "  ackages ")
        menu.addstr(1, 2, "L", curses.A_BOLD | curses.A_UNDERLINE)
        menu.addstr(2, 2, "P", curses.A_BOLD | curses.A_UNDERLINE)
        c = menu.getch()
        menu.erase()
        self.redraw()
        if c == ord("l"):
            return
        elif c == ord("p"):
            self.show_package_collector()
    
    def update_status(self):
        self.update_downloads()
    
    def format_time(self, seconds):
        seconds = int(seconds)
        
        hours, seconds = divmod(seconds, 3600)
        minutes, seconds = divmod(seconds, 60)
        return "%.2i:%.2i:%.2i" % (hours, minutes, seconds)
    
    def format_size(self, size):
        return str(size / 1024) + " MB"
    
    def add_menu(self, name, key, func):
        self.lock.acquire()
        left = 2
        for item in self.menu_items:
            left += len(item[0]) + 1
        self.menu_items.append((name, key.lower(), func))
        self.screen.addstr(1, left, name)
        p = name.lower().find(key.lower())
        if not p == -1:
            self.screen.addstr(1, left+p, name[p], curses.A_BOLD | curses.A_UNDERLINE)
        self.lock.release()
    
    def get_menu_func(self, key):
        for item in self.menu_items:
            if ord(item[1]) == key:
                return item[2]
        return None
    
    def get_tmp_func(self, key):
        for item in self.tmp_bind:
            if item[0] == key:
                return item[1]
        return None
    
    def get_command(self):
        c = self.screen.getch()
        if c == curses.KEY_END:
            self.exit()
        else:
            f = self.get_menu_func(c)
            if not f:
                f = self.get_tmp_func(c)
            if f:
                f()
        self.refresh()
    
    def redraw(self):
        self.adjust_download_win_size(len(self.downloads), force=True)
    
    def exit(self):
        self.stop = True

class LoopThread(Thread):
    def __init__(self, func, ret_func=None, sleep_time=None):
        self.func = func
        self.ret_func = ret_func
        self.sleep_time = sleep_time
        self.running = True
        Thread.__init__(self)
    
    def run(self):
        while self.running:
            if self.sleep_time:
                sleep(self.sleep_time)
            ret = self.func()
            if self.ret_func:
                self.ret_func(ret)
    
    def stop(self):
        self.running = False
            
server_url = ""
def main(stdscr):
    global server_url
    cli = pyLoadCli(stdscr, server_url)
    refresh_loop = LoopThread(cli.update_status, sleep_time=1)
    refresh_loop.start()
    getch_loop = LoopThread(cli.get_command)
    getch_loop.start()
    try:
        while not cli.stop:
            sleep(1)
    finally:
        getch_loop.stop()
        refresh_loop.stop()
        return

if __name__=='__main__':
    if len(sys.argv) > 1:
        
        shortOptions = 'l'
        longOptions = ['local']

        opts, extraparams = __import__("getopt").getopt(sys.argv[1:], shortOptions, longOptions)
        for option, params in opts:
            if option in ("-l", "--local"):
                chdir(dirname(abspath(__file__)) + sep)
                config = ConfigParser.SafeConfigParser()
                config.read('config')
                
                ssl = ""
                if config.get("ssl", "activated") == "True":
                    ssl = "s"
                server_url = "http%s://%s:%s@%s:%s/" % (
                    ssl,
                    config.get("remote", "username"),
                    config.get("remote", "password"),
                    config.get("remote", "listenaddr"),
                    config.get("remote", "port")
                )
                
        if len(extraparams) == 1:
            server_url = sys.argv[1]
    else:
        print "URL scheme: http[s]://user:password@host:port/"
        server_url = raw_input("URL: ")
        
    curses.wrapper(main)
    sys.exit()
