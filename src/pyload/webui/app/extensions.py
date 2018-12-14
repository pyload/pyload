# -*- coding: utf-8 -*-

from flask_babel import Babel
from flask_debugtoolbar import DebugToolbarExtension
from flask_themes2 import Themes as _Themes


class Themes(_Themes):
    def init_app(self, app):
        return super().init_themes(app, app_identifier="pyload")


babel = Babel()
debugtoolbar = DebugToolbarExtension()
themes = Themes()

EXTENSIONS = [babel, debugtoolbar, themes]
