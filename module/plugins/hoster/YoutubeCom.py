# -*- coding: utf-8 -*-

import operator
import os
import re
import subprocess
import time
import urllib

from module.plugins.Plugin import Abort
from module.network.HTTPRequest import HTTPRequest
from module.network.CookieJar import CookieJar
from module.plugins.internal.Hoster import Hoster
from module.plugins.internal.misc import html_unescape, json, replace_patterns, which


class BIGHTTPRequest(HTTPRequest):
    """
    Overcome HTTPRequest's load() size limit to allow
    loading very big web pages by overrding HTTPRequest's write() function
    """
    def __init__(self, cookies=None, options=None, limit=1000000):  #@TODO: Add 'limit' parameter to HTTPRequest in v0.4.10
        self.limit = limit
        HTTPRequest.__init__(self, cookies=cookies, options=options)

    def write(self, buf):
        """ writes response """
        if self.limit and self.rep.tell() > self.limit or self.abort:
            rep = self.getResponse()
            if self.abort: raise Abort()
            f = open("response.dump", "wb")
            f.write(rep)
            f.close()
            raise Exception("Loaded Url exceeded limit")

        self.rep.write(buf)



class YoutubeCom(Hoster):
    __name__    = "YoutubeCom"
    __type__    = "hoster"
    __version__ = "0.52"
    __status__  = "testing"

    __pattern__ = r'https?://(?:[^/]*\.)?(youtu\.be/|youtube\.com/watch\?(?:.*&)?v=)\w+'
    __config__  = [("activated", "bool", "Activated", True),
                   ("quality", "sd;hd;fullhd;240p;360p;480p;720p;1080p;3072p", "Quality Setting"             , "hd" ),
                   ("fmt"    , "int"                                         , "FMT/ITAG Number (0 for auto)", 0    ),
                   (".mp4"   , "bool"                                        , "Allow .mp4"                  , True ),
                   (".flv"   , "bool"                                        , "Allow .flv"                  , True ),
                   (".webm"  , "bool"                                        , "Allow .webm"                 , False),
                   (".3gp"   , "bool"                                        , "Allow .3gp"                  , False),
                   ("3d"     , "bool"                                        , "Prefer 3D"                   , False)]

    __description__ = """Youtube.com hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("spoob",     "spoob@pyload.org"          ),
                       ("zoidberg",  "zoidberg@mujmail.cz"       ),
                       ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]


    URL_REPLACEMENTS = [(r'youtu\.be/', 'youtube.com/watch?v=')]

    #: Invalid characters that must be removed from the file name
    invalid_chars = u'\u2605:?><"|\\'

    #: name, width, height, quality ranking, 3D
    formats = {5  : (".flv" , 400 , 240 , 1 , False),
               6  : (".flv" , 640 , 400 , 4 , False),
               17 : (".3gp" , 176 , 144 , 0 , False),
               18 : (".mp4" , 480 , 360 , 2 , False),
               22 : (".mp4" , 1280, 720 , 8 , False),
               43 : (".webm", 640 , 360 , 3 , False),
               34 : (".flv" , 640 , 360 , 4 , False),
               35 : (".flv" , 854 , 480 , 6 , False),
               36 : (".3gp" , 400 , 240 , 1 , False),
               37 : (".mp4" , 1920, 1080, 9 , False),
               38 : (".mp4" , 4096, 3072, 10, False),
               44 : (".webm", 854 , 480 , 5 , False),
               45 : (".webm", 1280, 720 , 7 , False),
               46 : (".webm", 1920, 1080, 9 , False),
               82 : (".mp4" , 640 , 360 , 3 , True ),
               83 : (".mp4" , 400 , 240 , 1 , True ),
               84 : (".mp4" , 1280, 720 , 8 , True ),
               85 : (".mp4" , 1920, 1080, 9 , True ),
               100: (".webm", 640 , 360 , 3 , True ),
               101: (".webm", 640 , 360 , 4 , True ),
               102: (".webm", 1280, 720 , 8 , True )}

    def _decrypt_signature(self, encrypted_sig):
        """Turn the encrypted 's' field into a working signature"""
        try:
            player_url = json.loads(re.search(r'"assets":.+?"js":\s*("[^"]+")', self.data).group(1))
        except (AttributeError, IndexError):
            self.fail(_("Player URL not found"))

        if player_url.startswith("//"):
            player_url = 'https:' + player_url

        if not player_url.endswith(".js"):
            self.fail(_("Unsupported player type %s") % player_url)

        cache_info = self.db.retrieve("cache")
        cache_dirty = False

        if cache_info is None or 'version' not in cache_info or cache_info['version'] != self.__version__:
            cache_info = {'version': self.__version__,
                          'cache'  : {}}
            cache_dirty = True

        if player_url in cache_info['cache'] and time.time() < cache_info['cache'][player_url]['time'] + 24 * 60 * 60:
            self.log_debug("Using cached decode function to decrypt the URL")
            decrypt_func = lambda s: ''.join(s[_i] for _i in cache_info['cache'][player_url]['decrypt_map'])
            decrypted_sig = decrypt_func(encrypted_sig)

        else:
            player_data = self.load(player_url)
            try:
                function_name = re.search(r'\.sig\|\|([a-zA-Z0-9$]+)\(', player_data).group(1)

            except (AttributeError, IndexError):
                self.fail(_("Signature decode function name not found"))

            try:
                jsi = JSInterpreter(player_data)
                decrypt_func = lambda s: jsi.extract_function(function_name)([s])

                #: Since Youtube just scrambles the order of the characters in the signature
                #: and does not change any byte value, we can store just a transformation map as a cached function
                decrypt_map = [ord(c) for c in decrypt_func(''.join(map(unichr, xrange(len(encrypted_sig)))))]
                cache_info['cache'][player_url] = {'decrypt_map': decrypt_map,
                                                   'time'       : time.time()}
                cache_dirty = True

                decrypted_sig = decrypt_func(encrypted_sig)

            except (JSInterpreterError, AssertionError), e:
                self.log_error(_("Signature decode failed"), e)
                self.fail(e.message)

        #: Remove old records from cache
        for _c in cache_info['cache'].iterkeys():
            if time.time() >= cache_info['cache'][_c]['time'] + 24 * 60 * 60:
                cache_info['cache'].pop(_c, None)
                cache_dirty = True

        if cache_dirty:
            self.db.store("cache", cache_info)

        return decrypted_sig


    def setup(self):
        self.resume_download = True
        self.multiDL         = True

        try:
            self.req.http.close()
        except Exception:
            pass

        self.req.http = BIGHTTPRequest(cookies=CookieJar(None), options=self.pyload.requestFactory.getOptions(), limit=2000000)


    def process(self, pyfile):
        pyfile.url = replace_patterns(pyfile.url, self.URL_REPLACEMENTS)
        self.data  = self.load(pyfile.url)

        if re.search(r'<div id="player-unavailable" class="\s*player-width player-height\s*">', self.data):
            self.offline()

        if "We have been receiving a large volume of requests from your network." in self.data:
            self.temp_offline()

        #: Get config
        use3d = self.config.get('3d')

        if use3d:
            quality = {'sd': 82, 'hd': 84, 'fullhd': 85, '240p': 83, '360p': 82,
                       '480p': 82, '720p': 84, '1080p': 85, '3072p': 85}
        else:
            quality = {'sd': 18, 'hd': 22, 'fullhd': 37, '240p': 5, '360p': 18,
                       '480p': 35, '720p': 22, '1080p': 37, '3072p': 38}

        desired_fmt = self.config.get('fmt')

        if not desired_fmt:
            desired_fmt = quality.get(self.config.get('quality'), 18)

        elif desired_fmt not in self.formats:
            self.log_warning(_("FMT %d unknown, using default") % desired_fmt)
            desired_fmt = 0

        #: Parse available streams
        streams = re.search(r'"url_encoded_fmt_stream_map":"(.+?)",', self.data).group(1)
        streams = [x.split('\u0026') for x in streams.split(',')]
        streams = [dict((y.split('=', 1)) for y in x) for x in streams]
        streams = [(int(x['itag']),
                    urllib.unquote(x['url']),
                    x.get('s', x.get('sig', None)),
                    True if 's' in x else False)
                   for x in streams]

        # self.log_debug("Found links: %s" % streams)

        self.log_debug("AVAILABLE STREAMS: %s" % [x[0] for x in streams])

        #: Build dictionary of supported itags (3D/2D)
        allowed = lambda x: self.config.get(self.formats[x][0])
        streams = [x for x in streams if x[0] in self.formats and allowed(x[0])]

        if not streams:
            self.fail(_("No available stream meets your preferences"))

        fmt_dict = dict([(x[0], x[1:]) for x in streams if self.formats[x[0]][4] == use3d] or streams)

        self.log_debug("DESIRED STREAM: ITAG:%d (%s) %sfound, %sallowed" %
                      (desired_fmt, "%s %dx%d Q:%d 3D:%s" % self.formats[desired_fmt],
                       "" if desired_fmt in fmt_dict else "NOT ", "" if allowed(desired_fmt) else "NOT "))

        #: Return fmt nearest to quality index
        if desired_fmt in fmt_dict and allowed(desired_fmt):
            choosen_fmt = desired_fmt
        else:
            sel  = lambda x: self.formats[x][3]  #: Select quality index
            comp = lambda x, y: abs(sel(x) - sel(y))

            self.log_debug("Choosing nearest fmt: %s" % [(x, allowed(x), comp(x, desired_fmt)) for x in fmt_dict.keys()])

            choosen_fmt = reduce(lambda x, y: x if comp(x, desired_fmt) <= comp(y, desired_fmt) and
                                                   sel(x) > sel(y) else y, fmt_dict.keys())

        self.log_debug("Chosen fmt: %s" % choosen_fmt)

        url = fmt_dict[choosen_fmt][0]

        if fmt_dict[choosen_fmt][1]:
            if fmt_dict[choosen_fmt][2]:
                signature = self._decrypt_signature(fmt_dict[choosen_fmt][1])

            else:
                signature = fmt_dict[choosen_fmt][1]

            url += "&signature=" + signature

        if "&ratebypass=" not in url:
            url += "&ratebypass=yes"

        #: Set file name
        file_suffix = self.formats[choosen_fmt][0] if choosen_fmt in self.formats else ".flv"
        file_name_pattern = '<meta name="title" content="(.+?)">'
        name = re.search(file_name_pattern, self.data).group(1).replace("/", "")

        #: Cleaning invalid characters from the file name
        name = name.encode('ascii', 'replace')
        for c in self.invalid_chars:
            name = name.replace(c, '_')

        pyfile.name = html_unescape(name)

        time = re.search(r't=((\d+)m)?(\d+)s', pyfile.url)
        ffmpeg = which("ffmpeg")
        if ffmpeg and time:
            m, s = time.groups()[1:]
            if m is None:
                m = "0"

            pyfile.name += " (starting at %s:%s)" % (m, s)

        pyfile.name += file_suffix
        filename     = self.download(url)

        if ffmpeg and time:
            inputfile = filename + "_"
            os.rename(filename, inputfile)

            subprocess.call([
                ffmpeg,
                "-ss", "00:%s:%s" % (m, s),
                "-i", inputfile,
                "-vcodec", "copy",
                "-acodec", "copy",
                filename])

            self.remove(inputfile, trash=False)


"""Credit to this awesome piece of code below goes to the 'youtube_dl' project, kudos!"""
class JSInterpreterError(Exception):
    pass


class JSInterpreter(object):
    def __init__(self, code, objects=None):
        self._OPERATORS = [
            ('|', operator.or_),
            ('^', operator.xor),
            ('&', operator.and_),
            ('>>', operator.rshift),
            ('<<', operator.lshift),
            ('-', operator.sub),
            ('+', operator.add),
            ('%', operator.mod),
            ('/', operator.truediv),
            ('*', operator.mul),
        ]
        self._ASSIGN_OPERATORS = [(op + '=', opfunc) for op, opfunc in self._OPERATORS]
        self._ASSIGN_OPERATORS.append(('=', lambda cur, right: right))
        self._VARNAME_PATTERN = r'[a-zA-Z_$][a-zA-Z_$0-9]*'

        if objects is None:
            objects = {}
        self.code = code
        self._functions = {}
        self._objects = objects

    def interpret_statement(self, stmt, local_vars, allow_recursion=100):
        if allow_recursion < 0:
            raise JSInterpreterError('Recursion limit reached')

        should_abort = False
        stmt = stmt.lstrip()
        stmt_m = re.match(r'var\s', stmt)
        if stmt_m:
            expr = stmt[len(stmt_m.group(0)):]

        else:
            return_m = re.match(r'return(?:\s+|$)', stmt)
            if return_m:
                expr = stmt[len(return_m.group(0)):]
                should_abort = True
            else:
                # Try interpreting it as an expression
                expr = stmt

        v = self.interpret_expression(expr, local_vars, allow_recursion)
        return v, should_abort

    def interpret_expression(self, expr, local_vars, allow_recursion):
        expr = expr.strip()

        if expr == '':  # Empty expression
            return None

        if expr.startswith('('):
            parens_count = 0
            for m in re.finditer(r'[()]', expr):
                if m.group(0) == '(':
                    parens_count += 1
                else:
                    parens_count -= 1
                    if parens_count == 0:
                        sub_expr = expr[1:m.start()]
                        sub_result = self.interpret_expression(sub_expr, local_vars, allow_recursion)
                        remaining_expr = expr[m.end():].strip()
                        if not remaining_expr:
                            return sub_result
                        else:
                            expr = json.dumps(sub_result) + remaining_expr
                        break
            else:
                raise JSInterpreterError('Premature end of parens in %r' % expr)

        for op, opfunc in self._ASSIGN_OPERATORS:
            m = re.match(r'(?x)(?P<out>%s)(?:\[(?P<index>[^\]]+?)\])?\s*%s(?P<expr>.*)$' % (self._VARNAME_PATTERN, re.escape(op)), expr)
            if not m:
                continue
            right_val = self.interpret_expression(m.group('expr'), local_vars, allow_recursion - 1)

            if m.groupdict().get('index'):
                lvar = local_vars[m.group('out')]
                idx = self.interpret_expression(m.group('index'), local_vars, allow_recursion)
                assert isinstance(idx, int)
                cur = lvar[idx]
                val = opfunc(cur, right_val)
                lvar[idx] = val
                return val
            else:
                cur = local_vars.get(m.group('out'))
                val = opfunc(cur, right_val)
                local_vars[m.group('out')] = val
                return val

        if expr.isdigit():
            return int(expr)

        var_m = re.match(r'(?!if|return|true|false)(?P<name>%s)$' % self._VARNAME_PATTERN, expr)
        if var_m:
            return local_vars[var_m.group('name')]

        try:
            return json.loads(expr)
        except ValueError:
            pass

        m = re.match(r'(?P<var>%s)\.(?P<member>[^(]+)(?:\(+(?P<args>[^()]*)\))?$' % self._VARNAME_PATTERN, expr)
        if m:
            variable = m.group('var')
            member = m.group('member')
            arg_str = m.group('args')

            if variable in local_vars:
                obj = local_vars[variable]
            else:
                if variable not in self._objects:
                    self._objects[variable] = self.extract_object(variable)
                obj = self._objects[variable]

            if arg_str is None:
                # Member access
                if member == 'length':
                    return len(obj)
                return obj[member]

            assert expr.endswith(')')
            # Function call
            if arg_str == '':
                argvals = tuple()
            else:
                argvals = tuple([self.interpret_expression(v, local_vars, allow_recursion) for v in arg_str.split(',')])

            if member == 'split':
                assert argvals == ('',)
                return list(obj)

            if member == 'join':
                assert len(argvals) == 1
                return argvals[0].join(obj)

            if member == 'reverse':
                assert len(argvals) == 0
                obj.reverse()
                return obj

            if member == 'slice':
                assert len(argvals) == 1
                return obj[argvals[0]:]

            if member == 'splice':
                assert isinstance(obj, list)
                index, howMany = argvals
                res = []
                for i in range(index, min(index + howMany, len(obj))):
                    res.append(obj.pop(index))
                return res

            return obj[member](argvals)

        m = re.match(r'(?P<in>%s)\[(?P<idx>.+)\]$' % self._VARNAME_PATTERN, expr)
        if m:
            val = local_vars[m.group('in')]
            idx = self.interpret_expression(m.group('idx'), local_vars, allow_recursion - 1)
            return val[idx]

        for op, opfunc in self._OPERATORS:
            m = re.match(r'(?P<x>.+?)%s(?P<y>.+)' % re.escape(op), expr)
            if not m:
                continue

            x, abort = self.interpret_statement(m.group('x'), local_vars, allow_recursion - 1)
            if abort:
                raise JSInterpreterError('Premature left-side return of %s in %r' % (op, expr))

            y, abort = self.interpret_statement(m.group('y'), local_vars, allow_recursion - 1)
            if abort:
                raise JSInterpreterError('Premature right-side return of %s in %r' % (op, expr))

            return opfunc(x, y)

        m = re.match(r'^(?P<func>%s)\((?P<args>[a-zA-Z0-9_$,]+)\)$' % self._VARNAME_PATTERN, expr)
        if m:
            fname = m.group('func')
            argvals = tuple([int(v) if v.isdigit() else local_vars[v] for v in m.group('args').split(',')])
            if fname not in self._functions:
                self._functions[fname] = self.extract_function(fname)
            return self._functions[fname](argvals)

        raise JSInterpreterError('Unsupported JS expression %r' % expr)

    def extract_object(self, objname):
        obj = {}
        obj_m = re.search(r'(?:var\s+)?%s\s*=\s*\{\s*(?P<fields>([a-zA-Z$0-9]+\s*:\s*function\(.*?\)\s*\{.*?\}(?:,\s*)?)*)\}\s*;'
                          % re.escape(objname), self.code)
        fields = obj_m.group('fields')
        # Currently, it only supports function definitions
        fields_m = re.finditer(r'(?P<key>[a-zA-Z$0-9]+)\s*:\s*function\((?P<args>[a-z,]+)\){(?P<code>[^}]+)}', fields)
        for f in fields_m:
            argnames = f.group('args').split(',')
            obj[f.group('key')] = self.build_function(argnames, f.group('code'))

        return obj

    def extract_function(self, function_name):
        func_m = re.search(r'(?x)(?:function\s+%s|[{;,]%s\s*=\s*function|var\s+%s\s*=\s*function)\s*\((?P<args>[^)]*)\)\s*\{(?P<code>[^}]+)\}'
                           % (re.escape(function_name), re.escape(function_name), re.escape(function_name)), self.code)
        if func_m is None:
            raise JSInterpreterError('Could not find JS function %r' % function_name)

        argnames = func_m.group('args').split(',')

        return self.build_function(argnames, func_m.group('code'))

    def call_function(self, function_name, *args):
        f = self.extract_function(function_name)
        return f(args)

    def build_function(self, argnames, code):
        def resf(argvals):
            local_vars = dict(zip(argnames, argvals))
            for stmt in code.split(';'):
                res, abort = self.interpret_statement(stmt, local_vars)
                if abort:
                    break
            return res

        return resf