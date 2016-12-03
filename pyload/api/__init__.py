from __future__ import unicode_literals
__all__ = ["CoreApi", "ConfigApi", "DownloadApi", "DownloadPreparingApi", "FileApi",
            "UserInteractionApi", "AccountApi", "AddonApi", "UserApi", "StatisticsApi"]

# Import all components
# from .import *
# Above does not work in py 2.5
for name in __all__:
    __import__(__name__ + "." + name)
