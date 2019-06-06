# -*- coding: utf-8 -*-
# AUTHOR: vuolter

from flask_babel import Babel
from flask_debugtoolbar import DebugToolbarExtension
from flask_themes2 import Themes as _Themes

from pyload import APPID


class Themes(_Themes):
    def init_app(self, app):
        return super().init_themes(app, app_identifier=APPID)


babel = Babel()
debugtoolbar = DebugToolbarExtension()
themes = Themes()

EXTENSIONS = [babel, debugtoolbar, themes]
