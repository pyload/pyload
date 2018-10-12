# -*- coding: utf-8 -*-
from pkg_resources import get_distribution, DistributionNotFound

try:
    dist_name = 'pyload-ng'
    __version__ = get_distribution(dist_name).version
except DistributionNotFound:
    __version__ = 'unknown'
finally:
    del get_distribution, DistributionNotFound
