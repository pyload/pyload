__all__ = ["CoreApi", "ConfigApi", "DownloadApi", "DownloadPreparingApi", "FileApi",
           "CollectorApi", "UserInteractionApi", "AccountApi", "AddonApi"]

# Import all components
# from .import *
# Above does not work in py 2.5
for name in __all__:
    __import__(__name__ + "." + name)