# -*- coding: utf-8 -*-

import flask

from .helpers import parse_userdata, parse_permissions


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
        status = api.statusServer()
        captcha = api.isCaptchaWaiting()

        # check if update check is available
        info = api.getInfoByPlugin("UpdateManager")
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
