import urllib2
import urllib
import re
import time

plugin_name = "Rapidshare.com"
plugin_type = "hoster"
plugin_pattern = r"http://(?:www.)?rapidshare.com/files/"

def get_file_url(url):
    root_url = urllib2.urlopen(url).read()

    if re.search(r".*The File could not be found.*", root_url) != None or re.search(r"(<p>This limit is reached.</p>)", root_url) or re.search(r"(.*is momentarily not available.*)", root_url):
        return ("missing", url)
    else:
        last_url = urllib2.urlopen(re.search(r"<form action=\"(.*?)\"", root_url).group(1), urllib.urlencode({"dl.start" : "Free"})).read()
        if re.search(r".*is already downloading.*", last_url) != None:
            print "IP laed bereits Datei von Rapidshare"
            return ('wait', 10)
        else:
            try:
                wait_minutes = re.search(r"Or try again in about (\d+) minute", last_url).group(1)
                return ('wait', wait_minutes)

            except:
                if re.search(r".*Currently a lot of users.*", last_url) != None:
                    return ('wait', 2)
                else:
                    wait_seconds = re.search(r"var c=(.*);.*", last_url).group(1)
                    file_url = re.search(r".*name=\"dlf\" action=\"(.*)\" method=.*", last_url).group(1)
                    file_name = file_url.split('/')[-1]

                    for second in range(1, int(wait_seconds) + 1):
                        print "Noch " + str(int(wait_seconds) + 1 - second - 1) + " Sekunden zum Download von " + file_name
                        time.sleep(1)

                    return ("download", (file_url, file_name))
