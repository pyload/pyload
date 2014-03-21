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


class FilestubeCom(SimpleCrypter):
    __name__ = "FilestubeCom"
    __type__ = "crypter"
    __pattern__ = r"http://(?:w{3}.)?filestube\.(?:com|to)/\w+"
    __version__ = "0.03"
    __description__ = """Filestube.com Plugin"""
    __author_name__ = ("stickell")
    __author_mail__ = ("l.stickell@yahoo.it")

    LINK_PATTERN = r"<a class=\"file-link-main(?: noref)?\" [^>]* href=\"(http://[^\"]+)"
    TITLE_PATTERN = r"<h1\s*> (?P<title>.+)  download\s*</h1>"
