# -*- coding: utf-8 -*-

############################################################################
# This program is free software: you can redistribute it and/or modify     #
# it under the terms of the GNU Affero General Public License as           #
# published by the Free Software Foundation, either version 3 of the       #
# License, or (at your option) any later version.                          #
#                                                                          #
# This program is distributed in the hope that it will be useful,          #
# but WITHOUT ANY WARRANTY; without even the implied warranty of           #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the            #
# GNU Affero General Public License for more details.                      #
#                                                                          #
# You should have received a copy of the GNU Affero General Public License #
# along with this program.  If not, see <http://www.gnu.org/licenses/>.    #
############################################################################

from module.plugins.internal.SimpleCrypter import SimpleCrypter


class FiletramCom(SimpleCrypter):
    __name__ = "FiletramCom"
    __type__ = "crypter"
    __pattern__ = r"http://(?:www\.)?filetram.com/[^/]+/.+"
    __version__ = "0.01"
    __description__ = """Filetram.com Plugin"""
    __author_name__ = ("igel", "stickell")
    __author_mail__ = ("igelkun@myopera.com", "l.stickell@yahoo.it")

    LINK_PATTERN = r"\s+(http://.+)"
    TITLE_PATTERN = r"<title>(?P<title>[^<]+) - Free Download[^<]*</title>"
