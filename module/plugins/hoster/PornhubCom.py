# -*- coding: utf-8 -*-

import re

from module.plugins.Hoster import Hoster


class PornhubCom(Hoster):
    __name__ = "PornhubCom"
    __type__ = "hoster"
    __version__ = "0.5"

    __pattern__ = r'http://(?:www\.)?pornhub\.com/view_video\.php\?viewkey=[\w\d]+'

    __description__ = """Pornhub.com hoster plugin"""
    __author_name__ = "jeix"
    __author_mail__ = "jeix@hasnomail.de"


    def process(self, pyfile):
        self.download_html()
        if not self.file_exists():
            self.offline()

        pyfile.name = self.get_file_name()
        self.download(self.get_file_url())

    def download_html(self):
        url = self.pyfile.url
        self.html = self.load(url)

    def get_file_url(self):
        """ returns the absolute downloadable filepath
        """
        if not self.html:
            self.download_html()

        url = "http://www.pornhub.com//gateway.php"
        video_id = self.pyfile.url.split('=')[-1]
        # thanks to jD team for this one  v
        post_data = "\x00\x03\x00\x00\x00\x01\x00\x0c\x70\x6c\x61\x79\x65\x72\x43\x6f\x6e\x66\x69\x67\x00\x02\x2f\x31\x00\x00\x00\x44\x0a\x00\x00\x00\x03\x02\x00"
        post_data += chr(len(video_id))
        post_data += video_id
        post_data += "\x02\x00\x02\x2d\x31\x02\x00\x20"
        post_data += "add299463d4410c6d1b1c418868225f7"

        content = self.req.load(url, post=str(post_data))

        new_content = ""
        for x in content:
            if ord(x) < 32 or ord(x) > 176:
                new_content += '#'
            else:
                new_content += x

        content = new_content

        return re.search(r'flv_url.*(http.*?)##post_roll', content).group(1)

    def get_file_name(self):
        if not self.html:
            self.download_html()

        m = re.search(r'<title[^>]+>([^<]+) - ', self.html)
        if m:
            name = m.group(1)
        else:
            matches = re.findall('<h1>(.*?)</h1>', self.html)
            if len(matches) > 1:
                name = matches[1]
            else:
                name = matches[0]

        return name + '.flv'

    def file_exists(self):
        """ returns True or False
        """
        if not self.html:
            self.download_html()

        if re.search(r'This video is no longer in our database or is in conversion', self.html) is not None:
            return False
        else:
            return True
