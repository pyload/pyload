# -*- coding: utf-8 -*-

from pyload.plugin.internal.DeadHoster import DeadHoster, create_getInfo


class FiredriveCom(DeadHoster):
    __name    = "FiredriveCom"
    __type    = "hoster"
    __version = "0.05"

    __pattern = r'https?://(?:www\.)?(firedrive|putlocker)\.com/(mobile/)?(file|embed)/(?P<ID>\w+)'

    __description = """Firedrive.com hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("Walter Purcaro", "vuolter@gmail.com")]


getInfo = create_getInfo(FiredriveCom)
