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

    @author: mkaay, RaNaN
"""

from urllib2 import BaseHandler
from urllib import addinfourl
from urllib2 import Request
from urlparse import urlparse, urlunparse, urljoin
from CookieJar import CookieJar

class CookieRedirectHandler(BaseHandler):
    # maximum number of redirections to any single URL
    # this is needed because of the state that cookies introduce
    max_repeats = 4
    # maximum total number of redirections (regardless of URL) before
    # assuming we're in a loop
    max_redirections = 10
    
    def __init__(self, cookiejar=None, follow=True):
        if cookiejar is None:
            cookiejar = CookieJar()
        self.cookiejar = cookiejar
        self.follow = follow

    def http_request(self, request):
        self.cookiejar.add_cookie_header(request)
        return request

    def http_response(self, request, response):
        self.cookiejar.extract_cookies(response, request)
        return response

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        """Return a Request or None in response to a redirect.

        This is called by the http_error_30x methods when a
        redirection response is received.  If a redirection should
        take place, return a new Request to allow http_error_30x to
        perform the redirect.  Otherwise, raise HTTPError if no-one
        else should try to handle this url.  Return None if you can't
        but another Handler might.
        """
        m = req.get_method()
        if (code in (301, 302, 303, 307) and m in ("GET", "HEAD")
            or code in (301, 302, 303) and m == "POST"):
            # Strictly (according to RFC 2616), 301 or 302 in response
            # to a POST MUST NOT cause a redirection without confirmation
            # from the user (of urllib2, in this case).  In practice,
            # essentially all clients do redirect in this case, so we
            # do the same.
            # be conciliant with URIs containing a space
            newurl = newurl.replace(' ', '%20')
            newheaders = dict((k,v) for k,v in req.headers.items()
                              if k.lower() not in ("content-length", "content-type", "cookie")
                             )
            req = Request(newurl,
                           headers=newheaders,
                           origin_req_host=req.get_origin_req_host(),
                           unverifiable=True)
            self.cookiejar.add_cookie_header(req)
            return req
        else:
            raise HTTPError(req.get_full_url(), code, msg, headers, fp)

    # Implementation note: To avoid the server sending us into an
    # infinite loop, the request object needs to track what URLs we
    # have already seen.  Do this by adding a handler-specific
    # attribute to the Request object.
    def http_error_302(self, req, fp, code, msg, headers):
        resp = addinfourl(fp, headers, req.get_full_url())
        resp.code = code
        resp.msg = msg
        self.cookiejar.extract_cookies(resp, req)
        
        if not self.follow:
            return resp
        
        # Some servers (incorrectly) return multiple Location headers
        # (so probably same goes for URI).  Use first header.
        if 'location' in headers:
            newurl = headers.getheaders('location')[0]
        elif 'uri' in headers:
            newurl = headers.getheaders('uri')[0]
        else:
            return

        # fix a possible malformed URL
        urlparts = urlparse(newurl)
        if not urlparts.path:
            urlparts = list(urlparts)
            urlparts[2] = "/"
        newurl = urlunparse(urlparts)

        newurl = urljoin(req.get_full_url(), newurl)

        # XXX Probably want to forget about the state of the current
        # request, although that might interact poorly with other
        # handlers that also use handler-specific request attributes
        new = self.redirect_request(req, fp, code, msg, headers, newurl)
        if new is None:
            return

        # loop detection
        # .redirect_dict has a key url if url was previously visited.
        if hasattr(req, 'redirect_dict'):
            visited = new.redirect_dict = req.redirect_dict
            if (visited.get(newurl, 0) >= self.max_repeats or
                len(visited) >= self.max_redirections):
                raise HTTPError(req.get_full_url(), code,
                                self.inf_msg + msg, headers, fp)
        else:
            visited = new.redirect_dict = req.redirect_dict = {}
        visited[newurl] = visited.get(newurl, 0) + 1

        # Don't close the fp until we are sure that we won't use it
        # with HTTPError.
        fp.read()
        fp.close()
        return self.parent.open(new, timeout=req.timeout)

    http_error_301 = http_error_303 = http_error_307 = http_error_302

    inf_msg = "The HTTP server returned a redirect error that would " \
              "lead to an infinite loop.\n" \
              "The last 30x error message was:\n"

    https_request = http_request
    https_response = http_response
