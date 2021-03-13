# -*- coding: utf-8 -*-

from flask_babel import Babel
from flask_caching import Cache
from flask_compress import Compress
from flask_session import Session
from flask_themes2 import Themes as _Themes
from pyload import APPID


class Themes(_Themes):
    def init_app(self, app, path_prefix=""):
        return super().init_themes(app,
                                   app_identifier=APPID,
                                   theme_url_prefix=path_prefix + "/_themes")


babel = Babel()
cache = Cache()
compress = Compress()
session = Session()
themes = Themes()

EXTENSIONS = [babel, cache, compress, session]

THEMES = [themes]
