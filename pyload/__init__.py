# -*- coding: utf-8 -*-

__all__ = ["__status_code__", "__status__", "__version_info__", "__version__", "__author_name__", "__author_mail__", "__license__"]

__status_code__ = 4
__status__ = {1: "Planning",
              2: "Pre-Alpha",
              3: "Alpha",
              4: "Beta",
              5: "Production/Stable",
              6: "Mature",
              7: "Inactive"}[__status_code__]  #: PyPI Development Status Classifiers

__version_info__ = (0, 4, 10)
__version__ = '.'.join(map(str, __version_info__))

__author_name__ = "pyLoad Team"
__author_mail__ = "admin@pyload.org"

__license__ = "GNU Affero General Public License v3"
