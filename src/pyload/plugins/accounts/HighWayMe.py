import json
import re

from pyload.core.network.http.exceptions import BadHeader

from ..base.multi_account import MultiAccount


class HighWayMe(MultiAccount):
    __name__ = "HighWayMe"
    __type__ = "account"
    __version__ = "0.13"
    __status__ = "testing"

    __config__ = [
        ("mh_mode", "all;listed;unlisted", "Filter downloaders to use", "all"),
        ("mh_list", "str", "Downloader list (comma separated)", ""),
        ("mh_interval", "int", "Reload interval in hours", 12),
    ]

    __description__ = """High-Way.me account plugin"""
    __license__ = "GPLv3"
    __authors__ = [
        ("EvolutionClip", "evolutionclip@live.de"),
        ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com"),
        ("Yaknar", "yaknar[AT]high-way[DOT]me"),
    ]

    #: Download Center API, authenticated with an API token (bearer). Tokens are created
    #: in the Download Center under "Sessions": https://cloud.high-way.me/#sessions
    API_URL = "https://cloud.high-way.me/center-api/"

    def api_request(self, method, api_key, get=None, post=None):
        self.req.http.set_header("Authorization", f"Bearer {api_key}")
        self.req.http.set_header("Accept", "application/json")

        try:
            json_data = self.load(self.API_URL + method, get=get, post=post)

        except BadHeader as exc:
            json_data = exc.content

        try:
            return json.loads(json_data)

        except ValueError:
            return {"error": "invalid_response", "message": "Invalid API response"}

    def grab_hosters(self, user, password, data):
        api_data = self.api_request("status.php", password)
        if "error" in api_data:
            self.log_error(api_data.get("message", api_data["error"]))
            return []

        hosters = []
        for item in api_data.get("items", []):
            if item.get("is_hoster") != 1:
                continue

            if not item.get("available") or not item.get("enabled"):
                continue

            #: `code` is the main domain, `link_wildcards` lists more domains
            #: as `*://domain/*|*://other/*`
            hosters.append(item.get("code") or "")
            for wildcard in (item.get("link_wildcards") or "").split("|"):
                m = re.match(r"(?:\*|https?)://(?:\*\.)?([^/*]+)", wildcard.strip())
                if m is not None:
                    hosters.append(m.group(1))

        return [hoster for hoster in hosters if hoster]

    def grab_info(self, user, password, data):
        validuntil = -1
        trafficleft = None
        premium = False

        api_data = self.api_request("transfers.php", password, get={"stats": 1})
        if "error" in api_data:
            self.log_error(api_data.get("message", api_data["error"]))

        else:
            premium = bool(api_data.get("premium"))
            if api_data.get("plan_expires_at"):
                validuntil = float(api_data["plan_expires_at"])

            #: File host traffic only, Usenet and torrents are not counted.
            #: `null` means fair use.
            total_available = (api_data.get("traffic") or {}).get("total_available")
            trafficleft = -1 if total_available is None else int(total_available)

        return {
            "premium": premium,
            "validuntil": validuntil,
            "trafficleft": trafficleft,
        }

    def signin(self, user, password, data):
        api_data = self.api_request("transfers.php", password, get={"stats": 1})
        if "error" in api_data:
            self.log_error(
                self._(
                    "Password for HighWayMe should be an API token "
                    "from the Download Center (Sessions)"
                )
            )
            self.log_error(api_data.get("message", api_data["error"]))
            self.fail_login()
