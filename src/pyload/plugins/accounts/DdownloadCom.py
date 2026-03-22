import pycurl

from ..base.xfs_account import XFSAccount


class DdownloadCom(XFSAccount):
    __name__ = "DdownloadCom"
    __type__ = "account"
    __version__ = "0.09"
    __status__ = "testing"

    __description__ = """Ddownload.com account plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    PLUGIN_DOMAIN = "ddownload.com"
    PLUGIN_URL = "http://ddownload.com"

    PREMIUM_PATTERN = r">Premium Member<"
    TRAFFIC_LEFT_PATTERN = r'\s*<span id="trafficValue">(?P<S>-?\d+)</span>'
    TRAFFIC_LEFT_UNIT = "MB"
    VALID_UNTIL_PATTERN = r'class="expires">([\w ]+)<'

    def setup(self):
        super(DdownloadCom, self).setup()
        self.req.http.c.setopt(pycurl.USERAGENT, "pyLoad/{}".format(self.pyload.version))

    def parse_traffic(self, size, unit=None):  #: returns bytes
        self.log_debug(f"Size: {size}", f"Unit: {unit or 'N/D'}")
        # to match with ddownload's dashboard value, we need to convert the traffic value in a different way
        return int(int(size) / 1000 * 1024**3)
