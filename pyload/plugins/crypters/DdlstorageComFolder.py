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


class DdlstorageComFolder(SimpleCrypter):
    __name__ = "DdlstorageComFolder"
    __type__ = "crypter"
    __pattern__ = r"http://(?:\w*\.)*?ddlstorage.com/folder/\w{10}"
    __version__ = "0.02"
    __description__ = """DDLStorage.com Folder Plugin"""
    __author_name__ = ("godofdream", "stickell")
    __author_mail__ = ("soilfiction@gmail.com", "l.stickell@yahoo.it")

    LINK_PATTERN = '<a class="sub_title" style="text-decoration:none;" href="(http://www.ddlstorage.com/.*)">'
