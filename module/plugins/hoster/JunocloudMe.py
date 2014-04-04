# -*- coding: utf-8 -*-
from module.plugins.hoster.XFileSharingPro import XFileSharingPro, create_getInfo

# testfile: http://junocloud.me/o4jbhy2uq7i1/test.iso.html
# (1 MB of urandom)
# sha1sum: 489ff675dcdd2c828c84a1d3ebe5b9aba50f2b76

class JunocloudMe(XFileSharingPro):
    __name__ = "JunocloudMe"
    __type__ = "hoster"
    __pattern__ = r"http://(?:\w*\.)*?junocloud.me/\w{12}"
    __version__ = "0.01"
    __description__ = """junocloud.me hoster plugin"""
    __author_name__ = ("duneyr")
    __author_mail__ = ("contact_me_at_github@nomail.com")

    #FILE_SIZE_PATTERN = r'(?P<S>[0-9]{1,}?) bytes'
    # not used in XFileSharingPro anyway (just as FILE_INFO_PATTERN)
    
    HOSTER_NAME = "junocloud.me"
    WAIT_PATTERN = r'.*?>(\d+)</span> seconds'

getInfo = create_getInfo(JunocloudMe)
