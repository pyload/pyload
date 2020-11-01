# -*- coding: utf-8 -*-

from flask_caching import Cache
from flask_themes2 import Themes as _Themes

from pyload import APPID


class Themes(_Themes):
    def init_app(self, app):
        return super().init_themes(app, app_identifier=APPID)


cache = Cache()
themes = Themes()

EXTENSIONS = [cache, themes]
