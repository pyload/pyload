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
"""

import re
from base64 import standard_b64decode

from Crypto.Cipher import AES

from module.plugins.Account import Account

def decrypt(data):
    data = standard_b64decode(data)
    key = standard_b64decode("L3hpTDJGaFNPVVlnc2FUdg==")

    obj = AES.new(key, AES.MODE_ECB)

    return obj.decrypt(data)


def parse(data):
    ret = {}
    for line in data.splitlines():
        line = line.strip()
        k, none, v = line.partition("=")
        ret[k] = v

    return ret

def loadSoap(req, soap):
    req.putHeader("User-Agent", "Mozilla/4.0 (compatible; MSIE 6.0; MS Web Services Client Protocol 2.0.50727.4952)")
    req.putHeader("SOAPAction", "\"urn:FileserveAPIWebServiceAction\"")

    ret = req.load("http://api.fileserve.com/api/fileserveAPIServer.php", post=soap, cookies=False, referer=False)

    req.clearHeaders()

    return ret

class FileserveCom(Account):
    __name__ = "FileserveCom"
    __version__ = "0.11"
    __type__ = "account"
    __description__ = """fileserve.com account plugin"""
    __author_name__ = ("mkaay")
    __author_mail__ = ("mkaay@mkaay.de")

    LOGIN_RE = re.compile(r"<loginReturn.*?>(.*?)</loginReturn")
    SHORTEN_RE = re.compile(r"<downloadGetShortenReturn.*?>(.*?)</downloadGetShortenReturn")
    DIRECT_RE = re.compile(r"<downloadDirectLinkReturn.*?>(.*?)</downloadDirectLinkReturn")


    def loginApi(self, user, req, data=None):
        if not data:
            data = self.getAccountData(user)

        soap = "<?xml version=\"1.0\" encoding=\"utf-8\"?><soap:Envelope xmlns:soap=\"http://schemas.xmlsoap.org/soap/envelope/\" xmlns:soapenc=\"http://schemas.xmlsoap.org/soap/encoding/\" xmlns:tns=\"urn:FileserveAPI\" xmlns:types=\"urn:FileserveAPI/encodedTypes\" xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\" xmlns:xsd=\"http://www.w3.org/2001/XMLSchema\"><soap:Body soap:encodingStyle=\"http://schemas.xmlsoap.org/soap/encoding/\"><tns:login><username xsi:type=\"xsd:string\">%s</username><password xsi:type=\"xsd:string\">%s</password></tns:login></soap:Body></soap:Envelope>" % (
            user, data["password"])

        rep = loadSoap(req, soap)

        match = self.LOGIN_RE.search(rep)
        if not match:
            return False

        data = parse(decrypt(match.group(1)))

        self.logDebug("Login: %s" % data)

        return data


    def getShorten(self, req, token, fileid):
        soap = "<?xml version=\"1.0\" encoding=\"utf-8\"?><soap:Envelope xmlns:soap=\"http://schemas.xmlsoap.org/soap/envelope/\" xmlns:soapenc=\"http://schemas.xmlsoap.org/soap/encoding/\" xmlns:tns=\"urn:FileserveAPI\" xmlns:types=\"urn:FileserveAPI/encodedTypes\" xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\" xmlns:xsd=\"http://www.w3.org/2001/XMLSchema\"><soap:Body soap:encodingStyle=\"http://schemas.xmlsoap.org/soap/encoding/\"><tns:downloadGetShorten><token xsi:type=\"xsd:string\">%s</token><shorten xsi:type=\"xsd:string\">%s</shorten></tns:downloadGetShorten></soap:Body></soap:Envelope>" % (
        token, fileid)

        rep = loadSoap(req, soap)

        match = self.SHORTEN_RE.search(rep)
        data = parse(decrypt(match.group(1)))
        self.logDebug("Shorten: %s" % data)

        return data


    def getDirectLink(self, req, token):
        soap = "<?xml version=\"1.0\" encoding=\"utf-8\"?><soap:Envelope xmlns:soap=\"http://schemas.xmlsoap.org/soap/envelope/\" xmlns:soapenc=\"http://schemas.xmlsoap.org/soap/encoding/\" xmlns:tns=\"urn:FileserveAPI\" xmlns:types=\"urn:FileserveAPI/encodedTypes\" xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\" xmlns:xsd=\"http://www.w3.org/2001/XMLSchema\"><soap:Body soap:encodingStyle=\"http://schemas.xmlsoap.org/soap/encoding/\"><tns:downloadDirectLink><token xsi:type=\"xsd:string\">%s</token></tns:downloadDirectLink></soap:Body></soap:Envelope>" % token

        rep = loadSoap(req, soap)

        match = self.DIRECT_RE.search(rep)
        data = parse(decrypt(match.group(1)))
        self.logDebug("getDirect: %s" % data)

        return data


    def loadAccountInfo(self, user, req):
        data = self.loginApi(user, req)

        if data["user_type"] == "PREMIUM":
            validuntil = int(data["expiry_date"])
            return {"trafficleft": -1, "validuntil": validuntil}
        else:
            return {"premium": False, "trafficleft": None, "validuntil": None}


    def login(self, user, data, req):
        ret = self.loginApi(user, req, data)
        if not ret:
            self.wrongPassword()
        elif ret["error"] == "LOGIN_FAIL":
            self.wrongPassword()

