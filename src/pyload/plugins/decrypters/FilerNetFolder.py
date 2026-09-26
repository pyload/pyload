import json

from pyload.core.network.http.exceptions import BadHeader

from ..base.decrypter import BaseDecrypter


class FilerNetFolder(BaseDecrypter):
    __name__ = "FilerNetFolder"
    __type__ = "decrypter"
    __version__ = "0.51"
    __status__ = "testing"

    __pattern__ = r"https?://filer\.net/folder/(?P<ID>\w+)"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        (
            "folder_per_package",
            "Default;Yes;No",
            "Create folder for each package",
            "Default",
        ),
    ]

    __description__ = """Filer.net folder decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [
        ("nath_schwarz", "nathan.notwhite@gmail.com"),
        ("stickell", "l.stickell@yahoo.it"),
        ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com"),
    ]

    # See https://filer.net/api
    API_URL = "https://filer.net/api/"

    def api_request(self, method, **kwargs):
        try:
            json_data = self.load(self.API_URL + method, get=kwargs, redirect=False)
        except BadHeader as exc:
            json_data = exc.content

        return json.loads(json_data)

    def decrypt(self, pyfile):
        folder_id = self.info["pattern"]["ID"]

        # Try new API first, fall back to old API
        api_data = self._get_folder_new(folder_id)
        if api_data is None:
            api_data = self._get_folder_old(folder_id)

        if api_data:
            pack_name = api_data.get("folder_name") or pyfile.package().name
            pack_links = [
                f"https://filer.net/get/{f['file_hash']}"
                for f in api_data.get("files", [])
            ]
            if pack_links:
                self.packages.append(
                    (
                        pack_name,
                        pack_links,
                        pack_name or pyfile.package().folder,
                    )
                )

    def _get_folder_new(self, folder_id):
        """New API: GET /api/folder/{hash}"""
        try:
            json_data = self.load(f"{self.API_URL}folder/{folder_id}", redirect=False)
            api_data = json.loads(json_data)
        except (BadHeader, json.JSONDecodeError):
            return None

        if "code" in api_data and api_data.get("code") == 200:
            data = api_data.get("data", {})
            return {
                "folder_name": data.get("folder_name"),
                "files": data.get("files", []),
            }
        return None

    def _get_folder_old(self, folder_id):
        """Old API: GET /api/folder/{hash}.json"""
        try:
            json_data = self.load(f"{self.API_URL}folder/{folder_id}.json", redirect=False)
            api_data = json.loads(json_data)
        except (BadHeader, json.JSONDecodeError):
            return None

        if api_data.get("code") == 200:
            data = api_data.get("data", {})
            return {
                "folder_name": data.get("folder_name"),
                "files": data.get("files", []),
            }
        return None
