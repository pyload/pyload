# -*- coding: utf-8 -*-
# @author: vuolter

from pkg_resources import get_distribution
from semver import parse_version_info

__package__ = 'pyload'
__package_name__ = 'pyload-ng'
__version__ = get_distribution(__package_name__).version
__version_info__ = parse_version_info(__version__)
__credits__ = (('Walter Purcaro', 'vuolter@gmail.com', '2015-2017'),
               ('pyLoad Team', 'info@pyload.net', '2009-2015'))

del get_distribution, parse_version_info
