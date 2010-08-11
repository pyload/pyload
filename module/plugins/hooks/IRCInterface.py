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
    @interface-version: 0.2
"""

from select import select
import socket
import sys
from threading import Thread
import time
from time import sleep
from traceback import print_exc

from module.plugins.Hook import Hook

class IRCInterface(Thread, Hook):
    __name__ = "IRCInterface"
    __version__ = "0.1"
    __description__ = """connect to irc and let owner perform different tasks"""
    __config__ = [("activated", "bool", "Activated", "False"),
        ("host", "str", "IRC-Server Address", ""),
        ("port", "int", "IRC-Server Port", "6667"),
        ("ident", "str", "Clients ident", "pyload-irc"),
        ("realname", "str", "Realname", "pyload-irc"),
        ("nick", "str", "Nickname the Client will take", "pyLoad-IRC"),
        ("owner", "str", "Nickname the Client will accept commands from", "Enter your nick here"),
        ("info_file", "bool", "Inform about every file finished", "False"),
        ("info_pack", "bool", "Inform about every package finished", "True")]
    __author_name__ = ("Jeix")
    __author_mail__ = ("Jeix@hasnomail.com")
    
    def __init__(self, core):
        Thread.__init__(self)
        Hook.__init__(self, core)
        self.setDaemon(True)
        
    def coreReady(self):
        self.new_package = {}
        
        self.abort = False
        
        self.host = self.getConfig("host") + ":" + str(self.getConfig("port"))
        self.owner = self.getConfig("owner")
        self.nick = self.getConfig("nick")
        
        #self.targets = irc_targets # where replies will go to
        #if len(self.targets) < 1:
        
        self.targets = [self.getConfig("owner")]
        
        self.links_added = 0

        self.start()
        
    def packageFinished(self, pypack):
        
        try:
            if self.getConfig("info_pack"):
                self.response(_("Package finished: %s") % pypack.name)
        except:
            pass
        
    def downloadFinished(self, pyfile):
        try:
            if self.getConfig("info_file"):
                self.response(_("Download finished: %s @ %s") % (pyfile.name, pyfile.pluginname) )
        except:
            pass
             
    def run(self):
        # connect to IRC etc.
        self.sock = socket.socket()
        temp = self.host.split(":", 1)
        self.sock.connect((temp[0], int(temp[1])))
        self.sock.send("NICK %s\r\n" % self.nick)
        self.sock.send("USER %s %s bla :%s\r\n" % (self.nick, self.host, self.nick))
        for t in self.targets:
            if t.startswith("#"):
                self.sock.send("JOIN %s\r\n" % t)
        self.log.info("pyLoadIRC: Connected to %s!" % self.host)
        self.log.info("pyLoadIRC: Switching to listening mode!")
        try:        
            self.main_loop()
            
        except IRCError, ex:
            self.sock.send("QUIT :byebye\r\n")
            print_exc()
            self.sock.close()
            sys.exit(1)

            
    def main_loop(self):
        readbuffer = ""
        while True:
            sleep(1)
            fdset = select([self.sock], [], [], 0)
            if self.sock not in fdset[0]:
                continue
            
            if self.abort:
                raise IRCError("quit")
            
            readbuffer += self.sock.recv(1024)
            temp = readbuffer.split("\n")
            readbuffer = temp.pop()

            for line in temp:
                line  = line.rstrip()
                first = line.split()

                if(first[0] == "PING"):
                    self.sock.send("PING %s\r\n" % first[1])
                    
                if first[0] == "ERROR":
                    raise IRCError(line)
                    
                msg = line.split(None, 3)
                if len(msg) < 4:
                    continue
                    
                msg = {
                    "origin":msg[0][1:],
                    "action":msg[1],
                    "target":msg[2],
                    "text":msg[3][1:]
                }
                
                self.handle_events(msg)
        
        
    def handle_events(self, msg):
        if msg["origin"].split("!", 1)[0] != self.owner:
            return
            
        if msg["target"].split("!", 1)[0] != self.nick:
            return
            
        if msg["action"] != "PRIVMSG":
            return
         
        trigger = "pass"
        args = None
        
        temp = msg["text"].split()
        trigger = temp[0]
        if len(temp) > 1:
            args = temp[1:]
        
        handler = getattr(self, "event_%s" % trigger, self.event_pass)
        try:
            handler(args)
        except Exception, e:
            self.log.error("pyLoadIRC: "+ repr(e))
        
        
    def response(self, msg):
        #print _(msg)
        for t in self.targets:
            self.sock.send("PRIVMSG %s :%s\r\n" % (t, msg))
        
        
#### Events
    def event_pass(self, args):
        pass
        
    def event_status(self, args):
        downloads = self.core.status_downloads()
        if len(downloads) < 1:
            self.response("INFO: There are no active downloads currently.")
            return
            
        self.response("ID - Name - Status - Speed - ETA - Progress")
        for data in downloads:
            self.response("#%d - %s - %s - %s - %s - %s" %
                     (
                     data['id'],
                     data['name'],
                     data['status'],
                     "%d kb/s" % int(data['speed']),
                     "%d min" % int(data['eta'] / 60),
                     "%d/%d MB (%d%%)" % ((data['size']-data['kbleft']) / 1024, data['size'] / 1024, data['percent'])
                     )
                     )
            
    def event_queue(self, args):
        # just forward for now
        self.event_status(args)
        
    def event_collector(self, args):
        ps = self.core.get_collector()
        if len(ps) == 0:
            self.response("INFO: No packages in collector!")
            return
        
        for packdata in ps:
            self.response('PACKAGE: Package "%s" with id #%d' % (packdata['package_name'], packdata['id']))
            for fileid in self.core.get_package_files(packdata['id']):
                fileinfo = self.core.get_file_info(fileid)
                self.response('#%d FILE: %s (#%d)' % (packdata['id'], fileinfo["filename"], fileinfo["id"]))
        
    def event_links(self, args):
        fids = self.core.get_files()
        if len(fids) == 0:
            self.response("INFO: No links.")
            return
            
        for fid in fids:
            info = self.core.get_file_info(fid)
            self.response('LINK #%d: %s [%s]' % (fid, info["filename"], info["status_type"]))
        
    def event_packages(self, args):
        pids = self.core.get_packages()
        if len(pids) == 0:
            self.response("INFO: No packages.")
            return
            
        for pid in pids:
            data = self.core.get_package_data(pid)
            self.response('PACKAGE #%d: %s (%d links)' % (pid, data["package_name"], len(self.core.get_package_files(pid))))
        
    def event_info(self, args):
        if not args:
            self.response('ERROR: Use info like this: info <id>')
            return
            
        info = self.core.get_file_info(int(args[0]))
        self.response('LINK #%d: %s (%d) [%s bytes]' % (info['id'], info['filename'], info['size'], info['status_type']))
        
    def event_packinfo(self, args):
        if not args:
            self.response('ERROR: Use packinfo like this: packinfo <id>')
            return
            
        packdata = self.core.get_package_data(int(args[0]))
        self.response('PACKAGE: Package "%s" with id #%d' % (packdata['package_name'], packdata['id']))
        for fileid in self.core.get_package_files(packdata['id']):
            fileinfo = self.core.get_file_info(fileid)
            self.response('#%d LINK: %s (#%d)' % (packdata['id'], fileinfo["filename"], fileinfo["id"]))
    
    def event_start(self, args):
        if not args:
            count = 0
            for packdata in self.core.get_collector_packages():
                self.core.push_package_2_queue(packdata['id'])
                count += 1
                
            self.response("INFO: %d downloads started." % count)
            return
            
        for val in args:
            id = int(val.strip())
            self.core.push_package_2_queue(id)
            self.response("INFO: Starting download #%d" % id)
        
    def event_stop(self, args):
        if not args:
            self.core.stop_downloads()
            self.response("INFO: All downloads stopped.")
            return
            
        for val in args:
            id = int(val.strip())
            self.core.stop_download("", id)
            self.response("INFO: Download #%d stopped." % id)
        
    def event_add(self, args):
        if len(args) != 2:
            self.response('ERROR: Add links like this: "add <package|id> <link>". '\
                     'This will add the link <link> to to the package <package> / the package with id <id>!')
            return
            
        def get_pack_id(pack):
            if pack.isdigit():
                pack = int(pack)
                for packdata in self.core.get_collector_packages():
                    if packdata['id'] == pack:
                        return pack
                return -1
                    
            for packdata in self.core.get_collector_packages():
                if packdata['package_name'] == pack:
                    return packdata['id']
            return -1
            
            
        pack = args[0].strip()
        link = args[1].strip()
        count_added = 0
        count_failed = 0
                         
        # verify that we have a valid link
        if not self.core.is_valid_link(link):
            self.response("ERROR: Your specified link is not supported by pyLoad.")
            return
                
        # get a valid package id (create new package if it doesn't exist)
        pack_id = get_pack_id(pack)
        if pack_id == -1:
            pack_id = self.core.new_package(pack)

        # move link into package
        fid = self.core.add_links_to_package(pack_id, [link])        
        self.response("INFO: Added %s to Package %s [#%d]" % (link, pack, pack_id))
        
    def event_del(self, args):
        if len(args) < 2:
            self.response("ERROR: Use del command like this: del -p|-l <id> [...] (-p indicates that the ids are from packages, -l indicates that the ids are from links)")
            return
            
        if args[0] == "-p":
            ret = self.core.del_packages(map(int, args[1:]))
            self.response("INFO: Deleted %d packages!" % ret)
            
        elif args[0] == "-l":
            ret = self.core.del_links(map(int, args[1:]))
            self.response("INFO: Deleted %d links!" % ret)

        else:
            self.response("ERROR: Use del command like this: del <-p|-l> <id> [...] (-p indicates that the ids are from packages, -l indicates that the ids are from links)")
            return
            
    def event_help(self, args):
        self.response("The following commands are available:")
        self.response("add <package|packid> <link> Adds link to package. (creates new package if it does not exist)")
        time.sleep(1)
        self.response("collector                   Shows all packages in collector")
        self.response("del -p|-l <id> [...]        Deletes all packages|links with the ids specified")
        time.sleep(1)
        self.response("info <id>                   Shows info of the link with id <id>")
        self.response("help                        Shows this help file")
        time.sleep(1)
        self.response("links                       Shows all links in pyload")
        self.response("packages                    Shows all packages in pyload")
        time.sleep(1)
        self.response("packinfo <id>               Shows info of the package with id <id>")
        self.response("queue                       Shows info about the queue")
        time.sleep(1)
        self.response("start  [<id>...]            Starts the package with id <id> or all packages if no id is given")
        self.response("status                      Show general download status")
        time.sleep(1)
        self.response("stop [<id>...]              Stops the package with id <id> or all packages if no id is given")
        
        
class IRCError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)