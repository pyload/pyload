# -*- coding: utf-8 -*-

import flask

from .helpers import parse_permissions, parse_userdata


#: do we really need this?!
def pre_processor():
    user = parse_userdata()
    perms = parse_permissions()
    status = {}
    captcha = False
    update = False
    plugins = False

    api = flask.current_app.config["PYLOAD_API"]

    if user["is_authenticated"]:
        status = api.status_server()
        captcha = api.is_captcha_waiting()

        # check if update check is available
        info = api.get_info_by_plugin("UpdateManager")
        if info:
            update = info["pyload"] == "True"
            plugins = info["plugins"] == "True"

    return {
        "user": user,
        "status": status,
        "captcha": captcha,
        "perms": perms,
        "url": flask.request.url,
        "update": update,
        "plugins": plugins,
    }


CONTEXT_PROCESSORS = [pre_processor]
