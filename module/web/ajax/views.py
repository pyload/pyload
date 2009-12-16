# Create your views here.
from django.http import HttpResponse
from django.http import HttpResponseForbidden
from django.http import HttpResponseServerError
from django.conf import settings
from django.shortcuts import render_to_response
from django.utils import simplejson
from django.core.serializers import json

def check_server(function):
    def _dec(view_func):
        def _view(request, *args, **kwargs):
            try:
                version = settings.PYLOAD.get_server_version()
                return view_func(request, *args, **kwargs)
            except Exception, e:
                return HttpResponseServerError()
        
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
        def _view(request, *args, **kwargs):
            if request.user.has_perm(perm) and request.user.is_authenticated:
                return view_func(request, *args, **kwargs)
            else:
                return HttpResponseForbidden()
        
        _view.__name__ = view_func.__name__
        _view.__dict__ = view_func.__dict__
        _view.__doc__ = view_func.__doc__

        return _view

    return _dec

class JsonResponse(HttpResponse):
    def __init__(self, object):
        content = simplejson.dumps(
            object, indent=2, cls=json.DjangoJSONEncoder,
            ensure_ascii=False)
        super(JsonResponse, self).__init__(
            content)#, content_type='application/json')
        self['Cache-Control'] =  'no-cache, must-revalidate'



def add_package(request):
    a = {'b' : [1,2,3], 'dsfsd' : "sadd"}
    return JsonResponse(a)
    
# @TODO: Auth + Auth
    
def status(request):
    return JsonResponse(settings.PYLOAD.status_server())
    
def links(request):
    return JsonResponse(settings.PYLOAD.status_downloads())
    
def queue(request):
    return JsonResponse(settings.PYLOAD.get_queue())