from module.plugins.internal.SimpleCrypter import SimpleCrypter


class NosvideoCom(SimpleCrypter):
    __name__ = "NosvideoCom"
    __type__ = "crypter"
    __pattern__ = r"http://(?:www\.)?nosvideo\.com/\?v=\w+"
    __version__ = "0.01"
    __description__ = """Nosvideo.com Plugin"""
    __author_name__ = "igel"

    LINK_PATTERN = r'href="(http://(?:w{3}\.)?nosupload.com/\?d=\w+)"'
    TITLE_PATTERN = r"<[tT]itle>Watch (?P<title>.+)</[tT]itle>"
