# -*- coding: utf-8 -*-

import flask

from .helpers import theme_template


def has_service(service_name):
    api = flask.current_app.config["PYLOAD_API"]
    try:
        plugin, func =  service_name.split(".")
    except ValueError:
        return False

    return api.has_service(plugin, func)

TEMPLATE_GLOBALS = [theme_template, has_service]
