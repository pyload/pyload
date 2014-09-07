# -*- coding: utf-8 -*-

from pyload.plugins.hoster.XFileSharingPro import XFileSharingPro, create_getInfo


class DuploadOrg(XFileSharingPro):
    __name__ = "DuploadOrg"
    __type__ = "hoster"
    __version__ = "0.01"

    __pattern__ = r'http://(?:www\.)?dupload\.org/\w{12}'

    __description__ = """Dupload.grg hoster plugin"""
    __author_name__ = "stickell"
    __author_mail__ = "l.stickell@yahoo.it"

    HOSTER_NAME = "dupload.org"

    FILE_INFO_PATTERN = r'<h3[^>]*>(?P<N>.+) \((?P<S>[\d.]+) (?P<U>\w+)\)</h3>'


getInfo = create_getInfo(DuploadOrg)
