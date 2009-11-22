import sys
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
from xmlrpclib import ServerProxy
from time import time
import re

class Handler(BaseHTTPRequestHandler):
    
    def do_GET(self):
        global coreserver
        stdout = sys.stdout
        sys.stdout = self.wfile
        if self.path == "/":
            print "Server Runs"
        elif self.path == "/downloads":
            print self.get_downloads()
        elif re.search("/add=.?", self.path):
            if re.match(is_url, self.path.split("/add=")[1]):
                coreserver.add_urls([self.path.split("/add=")[1]])
                print "Link Added"
        else:
            try: 
                print open(self.path[1:], 'r').read()
            except IOError:
                self.send_error(404)
                
    def format_size(self, size):
        return str(size / 1024) + " MiB"

    def format_time(self,seconds):
        seconds = int(seconds)
        hours, seconds = divmod(seconds, 3600)
        minutes, seconds = divmod(seconds, 60)
        return "%.2i:%.2i:%.2i" % (hours, minutes, seconds)
                
    def get_downloads(self):
        data = coreserver.status_downloads()
        for download in data:
            print "<h3>%s</h3>" % download["name"]
            if download["status"] == "downloading":
                percent = download["percent"]
                z = percent / 4
                print "<h3>%s</h3>" % dl_name
                print "<font face='font-family:Fixedsys,Courier,monospace;'>[" + z * "#" + (25-z) * "&nbsp;" + "]</font>" + str(percent) + "%<br />"
                print "Speed: " + str(int(download['speed'])) + " kb/s"
                print "Size: " + self.format_size(download['size'])
                print "Finished in: " + self.format_time(download['eta'])
                print "ID: " + str(download['id'])
                dl_status = "[" + z * "#" + (25-z) * " " + "] " + str(percent) + "%" + " Speed: " + str(int(download['speed'])) + " kb/s" + " Size: " + self.format_size(download['size']) + " Finished in: " + self.format_time(download['eta'])  + " ID: " + str(download['id'])
            if download["status"] == "waiting":
                print "waiting: " + self.format_time(download["wait_until"]- time())
                
is_url = re.compile("^(((https?|ftp)\:\/\/)?([\w\.\-]+(\:[\w\.\&%\$\-]+)*@)?((([^\s\(\)\<\>\\\"\.\[\]\,@;:]+)(\.[^\s\(\)\<\>\\\"\.\[\]\,@;:]+)*(\.[a-zA-Z]{2,4}))|((([01]?\d{1,2}|2[0-4]\d|25[0-5])\.){3}([01]?\d{1,2}|2[0-4]\d|25[0-5])))(\b\:(6553[0-5]|655[0-2]\d|65[0-4]\d{2}|6[0-4]\d{3}|[1-5]\d{4}|[1-9]\d{0,3}|0)\b)?((\/[^\/][\w\.\,\?\'\\\/\+&%\$#\=~_\-@]*)*[^\.\,\?\"\'\(\)\[\]!;<>{}\s\x7F-\xFF])?)$",re.IGNORECASE)

coreserver = None

class WebServer():

    def start(self):
        try:
            global coreserver
            coreserver = ServerProxy("https://testuser:testpw@localhost:1337", allow_none=True)
            webserver = HTTPServer(('',8080),Handler)
            print 'server started at port 8080'
            webserver.serve_forever()
        except KeyboardInterrupt:
            webserver.socket.close()

if __name__ == "__main__":
    web = WebServer()
    web.start()

