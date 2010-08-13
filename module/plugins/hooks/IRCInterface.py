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
    @author: jeix
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
        ("host", "str", "IRC-Server Address", "Enter your server here!"),
        ("port", "int", "IRC-Server Port", "6667"),
        ("ident", "str", "Clients ident", "pyload-irc"),
        ("realname", "str", "Realname", "pyload-irc"),
        ("nick", "str", "Nickname the Client will take", "pyLoad-IRC"),
        ("owner", "str", "Nickname the Client will accept commands from", "Enter your nick here!"),
        ("info_file", "bool", "Inform about every file finished", "False"),
        ("info_pack", "bool", "Inform about every package finished", "True")]
    __author_name__ = ("Jeix")
    __author_mail__ = ("Jeix@hasnomail.com")
    
    def __init__(self, core):
        Thread.__init__(self)
        Hook.__init__(self, core)
        self.setDaemon(True)
        self.sm = core.server_methods
        
    def coreReady(self):
        self.new_package = {}
        
        self.abort = False
        
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
        host = self.getConfig("host")
        self.sock.connect((host, self.getConfig("port")))
        nick = self.getConfig("nick")
        self.sock.send("NICK %s\r\n" % nick)
        self.sock.send("USER %s %s bla :%s\r\n" % (nick, host, nick))
        for t in self.getConfig("owner").split():
            if t.strip().startswith("#"):
                self.sock.send("JOIN %s\r\n" % t.strip())
        self.log.info("pyLoadIRC: Connected to %s!" % host)
        self.log.info("pyLoadIRC: Switching to listening mode!")
        try:        
            self.main_loop()
            
        except IRCError, ex:
            self.sock.send("QUIT :byebye\r\n")
            print_exc()
            self.sock.close()

            
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
        if not msg["origin"].split("!", 1)[0] in self.getConfig("owner").split():
            return
            
        if msg["target"].split("!", 1)[0] != self.getConfig("nick"):
            return
            
        if msg["action"] != "PRIVMSG":
            return
            
        # HANDLE CTCP ANTI FLOOD/BOT PROTECTION
        if msg["text"] == "\x01VERSION\x01":
            self.log.debug("Sending CTCP VERSION.")
            self.sock.send("NOTICE %s :%s\r\n" % (msg['origin'], "pyLoad! IRC Interface"))
            return
        elif msg["text"] == "\x01TIME\x01":
            self.log.debug("Sending CTCP TIME.")
            self.sock.send("NOTICE %s :%d\r\n" % (msg['origin'], time.time()))
            return
        elif msg["text"] == "\x01LAG\x01":
            self.log.debug("Received CTCP LAG.") # don't know how to answer
            return
         
        trigger = "pass"
        args = None
        
        temp = msg["text"].split()
        trigger = temp[0]
        if len(temp) > 1:
            args = temp[1:]
        
        handler = getattr(self, "event_%s" % trigger, self.event_pass)
        try:
            res = handler(args)
            for line in res:
                self.response(line, msg["origin"])
        except Exception, e:
            self.log.error("pyLoadIRC: "+ repr(e))
        
        
    def response(self, msg, origin=""):
        if origin == "":
            for t in self.getConfig("owner").split():
                self.sock.send("PRIVMSG %s :%s\r\n" % (t.strip(), msg))
        else:
            self.sock.send("PRIVMSG %s :%s\r\n" % (origin.split("!", 1)[0], msg))
        
        
#### Events
    def event_pass(self, args):
        return []
        
    def event_status(self, args):
        downloads = self.sm.status_downloads()
        if len(downloads) < 1:
            return ["INFO: There are no active downloads currently."]
            
        lines = []
        lines.append("ID - Name - Status - Speed - ETA - Progress")
        for data in downloads:
            lines.append("#%d - %s - %s - %s - %s - %s" %
                     (
                     data['id'],
                     data['name'],
                     data['status'],
                     "%d kb/s" % int(data['speed']),
                     "%d min" % int(data['eta'] / 60),
                     "%d/%d MB (%d%%)" % ((data['size']-data['kbleft']) / 1024, data['size'] / 1024, data['percent'])
                     )
                     )
        return lines
            
    def event_queue(self, args):
        # just forward for now
        return self.event_status(args)
        
    def event_collector(self, args):
        ps = self.sm.get_collector()
        if len(ps) == 0:
            return ["INFO: No packages in collector!"]
        
        lines = []
        for packdata in ps:
            lines.append('PACKAGE: Package "%s" with id #%d' % (packdata['package_name'], packdata['id']))
            for fileid in self.sm.get_package_files(packdata['id']):
                fileinfo = self.sm.get_file_info(fileid)
                lines.append('#%d FILE: %s (#%d)' % (packdata['id'], fileinfo["filename"], fileinfo["id"]))
                
        return lines
        
    def event_links(self, args):
        fids = self.sm.get_files()
        if len(fids) == 0:
            return ["INFO: No links."]
            
        lines = []
        for fid in fids:
            info = self.sm.get_file_info(fid)
            lines.append('LINK #%d: %s [%s]' % (fid, info["filename"], info["status_type"]))
            
        return lines
        
    def event_packages(self, args):
        pids = self.sm.get_packages()
        if len(pids) == 0:
            return ["INFO: No packages."]
            
        lines = []
        for pid in pids:
            data = self.sm.get_package_data(pid)
            lines.append('PACKAGE #%d: %s (%d links)' % (pid, data["package_name"], len(self.sm.get_package_files(pid))))
            
        return lines
        
    def event_info(self, args):
        if not args:
            return ['ERROR: Use info like this: info <id>']
            
        info = self.sm.get_file_info(int(args[0]))
        return ['LINK #%d: %s (%d) [%s bytes]' % (info['id'], info['filename'], info['size'], info['status_type'])]
        
    def event_packinfo(self, args):
        if not args:
            return ['ERROR: Use packinfo like this: packinfo <id>']
            
        lines = []
        packdata = self.sm.get_package_data(int(args[0]))
        lines.append('PACKAGE: Package "%s" with id #%d' % (packdata['package_name'], packdata['id']))
        for fileid in self.sm.get_package_files(packdata['id']):
            fileinfo = self.sm.get_file_info(fileid)
            lines.append('#%d LINK: %s (#%d)' % (packdata['id'], fileinfo["filename"], fileinfo["id"]))
            
        return lines
    
    def event_start(self, args):
        if not args:
            count = 0
            for packdata in self.sm.get_collector_packages():
                self.sm.push_package_2_queue(packdata['id'])
                count += 1

            return ["INFO: %d downloads started." % count]
            
        lines = []
        for val in args:
            id = int(val.strip())
            self.sm.push_package_2_queue(id)
            lines.append("INFO: Starting download #%d" % id)
        
        return lines
        
    def event_stop(self, args):
        if not args:
            self.sm.stop_downloads()
            return ["INFO: All downloads stopped."]
            
        lines = []
        for val in args:
            id = int(val.strip())
            self.sm.stop_download("", id)
            lines.append("INFO: Download #%d stopped." % id)
            
        return lines
        
    def event_add(self, args):
        if len(args) != 2:
            return ['ERROR: Add links like this: "add <package|id> <link>". '\
                     'This will add the link <link> to to the package <package> / the package with id <id>!']
            
        def get_pack_id(pack):
            if pack.isdigit():
                pack = int(pack)
                for packdata in self.sm.get_collector_packages():
                    if packdata['id'] == pack:
                        return pack
                return -1
                    
            for packdata in self.sm.get_collector_packages():
                if packdata['package_name'] == pack:
                    return packdata['id']
            return -1
            
            
        pack = args[0].strip()
        link = args[1].strip()
        count_added = 0
        count_failed = 0
                         
        # verify that we have a valid link
        #if not self.sm.is_valid_link(link):
            #return ["ERROR: Your specified link is not supported by pyLoad."]
                
        # get a valid package id (create new package if it doesn't exist)
        pack_id = get_pack_id(pack)
        if pack_id == -1:
            pack_id = self.sm.new_package(pack)

        # move link into package
        fid = self.sm.add_links_to_package(pack_id, [link])        
        return ["INFO: Added %s to Package %s [#%d]" % (link, pack, pack_id)]
        
    def event_del(self, args):
        if len(args) < 2:
            return ["ERROR: Use del command like this: del -p|-l <id> [...] (-p indicates that the ids are from packages, -l indicates that the ids are from links)"]
            
        if args[0] == "-p":
            ret = self.sm.del_packages(map(int, args[1:]))
            return ["INFO: Deleted %d packages!" % ret]
            
        elif args[0] == "-l":
            ret = self.sm.del_links(map(int, args[1:]))
            return ["INFO: Deleted %d links!" % ret]

        else:
            return ["ERROR: Use del command like this: del <-p|-l> <id> [...] (-p indicates that the ids are from packages, -l indicates that the ids are from links)"]
            
    def event_help(self, args):
        lines = []
        lines.append("The following commands are available:")
        lines.append("add <package|packid> <link> Adds link to package. (creates new package if it does not exist)")
        lines.append("collector                   Shows all packages in collector")
        lines.append("del -p|-l <id> [...]        Deletes all packages|links with the ids specified")
        lines.append("info <id>                   Shows info of the link with id <id>")
        lines.append("help                        Shows this help file")
        lines.append("links                       Shows all links in pyload")
        lines.append("packages                    Shows all packages in pyload")
        lines.append("packinfo <id>               Shows info of the package with id <id>")
        lines.append("queue                       Shows info about the queue")
        lines.append("start  [<id>...]            Starts the package with id <id> or all packages if no id is given")
        lines.append("status                      Show general download status")
        lines.append("stop [<id>...]              Stops the package with id <id> or all packages if no id is given")
        return lines
        
        
class IRCError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)