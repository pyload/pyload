# -*- coding: utf-8 -*-

import flask_babel
import flask_debugtoolbar
import flask_themes2


class Themes(flask_themes2.Themes):
    def init_app(self, app):
        return super().init_themes(app, app_identifier="pyload")


babel = flask_babel.Babel()
debugtoolbar = flask_debugtoolbar.DebugToolbarExtension()
themes = Themes()

EXTENSIONS = [babel, debugtoolbar, themes]
