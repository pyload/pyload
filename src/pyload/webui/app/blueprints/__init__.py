# -*- coding: utf-8 -*-
#       ____________
#   ___/       |    \_____________ _                 _ ___
#  /        ___/    |    _ __ _  _| |   ___  __ _ __| |   \
# /    \___/  ______/   | '_ \ || | |__/ _ \/ _` / _` |    \
# \            ◯ |      | .__/\_, |____\___/\__,_\__,_|    /
#  \_______\    /_______|_|   |__/________________________/
#           \  /
#            \/

from .app_blueprint import bp as app_bp
from .api_blueprint import bp as api_bp
from .cnl_blueprint import bp as cnl_bp
from .json_blueprint import bp as json_bp


BLUEPRINTS = [app_bp, api_bp, cnl_bp, json_bp]
