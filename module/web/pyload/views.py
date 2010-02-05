# -*- coding: utf-8 -*-

# Create your views here.
import mimetypes
from os import listdir
from os import stat
from os.path import isdir
from os.path import isfile
from os.path import join

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.http import HttpResponseNotFound
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils.translation import ugettext as _


def check_server(function):
    def _dec(view_func):
        def _view(request, * args, ** kwargs):
            try:
                version = settings.PYLOAD.get_server_version()
            except Exception, e:
                return base(request, messages=[_('Can\'t connect to pyLoad. Please check your configuration and make sure pyLoad is running.'), str(e)])
            return view_func(request, * args, ** kwargs)
        
        _view.__name__ = view_func.__name__
        _view.__dict__ = view_func.__dict__
        _view.__doc__ = view_func.__doc__

        return _view

    if function is None:
        return _dec
    else:
        return _dec(function)
        
        
def permission(perm):
    def _dec(view_func):
        def _view(request, * args, ** kwargs):
            if request.user.has_perm(perm) and request.user.is_authenticated():
                return view_func(request, * args, ** kwargs)
            else:
                return base(request, messages=[_('You don\'t have permission to view this page.')])
        
        _view.__name__ = view_func.__name__
        _view.__dict__ = view_func.__dict__
        _view.__doc__ = view_func.__doc__

        return _view

    return _dec



def status_proc(request):
    return {'status': settings.PYLOAD.status_server()}


def base(request, messages):
    return render_to_response(join(settings.TEMPLATE, 'base.html'), {'messages': messages}, RequestContext(request))

@login_required
@permission('pyload.can_see_dl')
@check_server
def home(request):
    return render_to_response(join(settings.TEMPLATE, 'home.html'), RequestContext(request, {'content': settings.PYLOAD.status_downloads()}, [status_proc]))
    

@login_required
@permission('pyload.can_see_dl')
@check_server
def queue(request):
    queue = settings.PYLOAD.get_full_queue()
    return render_to_response(join(settings.TEMPLATE, 'queue.html'), RequestContext(request, {'content': queue}, [status_proc]))


@login_required
@permission('pyload.can_download')
@check_server
def downloads(request):
    if not isdir(settings.DL_ROOT):
        return base(request, [_('Download directory not found.')])
    data = {
        'folder': [],
        'files': []
    }
    
    for item in listdir(settings.DL_ROOT):
        if isdir(join(settings.DL_ROOT, item)):
            folder = {
                'name': item,
                'files': []
            }
            for file in listdir(join(settings.DL_ROOT, item)):
                if isfile(join(settings.DL_ROOT, item, file)):
                    folder['files'].append(file)
            
            data['folder'].append(folder)
        elif isfile(join(settings.DL_ROOT, item)):
            data['files'].append(item)
    
    
    return render_to_response(join(settings.TEMPLATE, 'downloads.html'), RequestContext(request, {'files': data}, [status_proc]))
    
@login_required
@permission('pyload.can_download')
@check_server
def download(request, path):
    path = path.split("/")
    
    dir = join(settings.DL_ROOT, path[1].replace('..', ''))
    if isdir(dir) or isfile(dir):
        if isdir(dir): filepath = join(dir, path[2])
        elif isfile(dir): filepath = dir
        
        print filepath
        if isfile(filepath):
            try:
                type, encoding = mimetypes.guess_type(filepath)
                if type is None:
                    type = 'application/octet-stream'
            
                response = HttpResponse(mimetype=type)
                response['Content-Length'] = str(stat(filepath).st_size)
            
                if encoding is not None:
                    response['Content-Encoding'] = encoding
                     
                response.write(file(filepath, "rb").read())
                return response
            
            except Exception, e:
                return HttpResponseNotFound("File not Found. %s" % str(e))
    
    return HttpResponseNotFound("File not Found.")

@login_required
@permission('pyload.can_see_logs')
@check_server
def logs(request, page=0):
    
    log = file(join(settings.LOG_ROOT, "log.txt")).readlines()
    log.reverse()
    data = []
    page = int(page)
    try:
        for i in range(page, page + 20):
            data.append({'line': i + 1, 'content':log[i]})
    except:
        pass
    
    return render_to_response(join(settings.TEMPLATE, 'logs.html'), RequestContext(request, {'log': data, 'next': str(page + 20), 'prev': 0 if page-20 < 0 else page-20}, [status_proc]))

@login_required
@permission('pyload.can_add_dl')
@check_server
def collector(request):
    coll = settings.PYLOAD.get_collector_packages()
    for pack in coll:
        pack["children"] = map(settings.PYLOAD.get_file_info, settings.PYLOAD.get_package_files(pack["id"]))
    return render_to_response(join(settings.TEMPLATE, 'collector.html'), RequestContext(request, {'content': coll}, [status_proc]))


@login_required
@permission('pyload.can_change_status')
@check_server
def config(request):
    return render_to_response(join(settings.TEMPLATE, 'settings.html'), RequestContext(request, {}, [status_proc]))
