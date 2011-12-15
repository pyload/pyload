# -*- coding: utf-8 -*-

"""
    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 3 of the License,
    or (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
    See the GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program; if not, see <http://www.gnu.org/licenses/>.
    
    @author: mkaay
"""

from module.plugins.Plugin import Plugin

class Hoster(Plugin):

    @staticmethod
    def getInfo(urls):
        """This method is used to retrieve the online status of files for hoster plugins.
        It has to *yield* list of tuples with the result in this format (name, size, status, url),
        where status is one of API pyfile statusses.

        :param urls: List of urls
        :return:
        """
        pass