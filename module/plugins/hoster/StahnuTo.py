from module.plugins.internal.DeadHoster import DeadHoster, create_getInfo

class StahnuTo(DeadHoster):
    __name__ = "StahnuTo"
    __type__ = "hoster"
    __version__ = "0.13"
    __status__  = "stable"

    __pattern__ = r"http://(\w*\.)?stahnu.to/(files/get/|.*\?file=)([^/]+).*"
    __config__  = []  #@TODO: Remove in 0.4.10

    __description__ = """stahnu.to"""
    __license__     = "GPLv3"
    __author_name__ = ("zoidberg")

getInfo = create_getInfo(StahnuTo)
