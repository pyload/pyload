# Create your views here.
from django.http import HttpResponse
from django.http import HttpResponseForbidden
from django.http import HttpResponseServerError
from django.conf import settings
from django.utils import simplejson
from django.core.serializers import json
  
def permission(perm):
    def _dec(view_func):
        def _view(request, *args, **kwargs):
            if request.user.has_perm(perm) and request.user.is_authenticated():
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


@permission('pyload.can_see_dl')    
def status(request):
    try:
        return JsonResponse(settings.PYLOAD.status_server())
    except:
        return HttpResponseServerError()

@permission('pyload.can_see_dl')
def links(request):
    try:
        return JsonResponse(settings.PYLOAD.status_downloads())
    except:
        return HttpResponseServerError()

@permission('pyload.can_see_dl')
def queue(request):
    try:
        return JsonResponse(settings.PYLOAD.get_queue())
        
    except:
        return HttpResponseServerError()
        
        
@permission('pyload.can_change_satus')
def pause(request):
    try:
        return JsonResponse(settings.PYLOAD.pause_server())
        
    except:
        return HttpResponseServerError()


@permission('pyload.can_change_status')
def unpause(request):
    try:
        return JsonResponse(settings.PYLOAD.unpause_server())
        
    except:
        return HttpResponseServerError()
        


@permission('pyload.can_see_dl')
def packages(request):
    try:
        data = settings.PYLOAD.get_queue()
        
        for package in data:
            package['links'] = []
            for file in settings.PYLOAD.get_package_files(package['id']):
                package['links'].append(settings.PYLOAD.get_file_info(file))
        
        return JsonResponse(data)
        
    except:
        return HttpResponseServerError()

@permission('pyload.can_see_dl')
def package(request,id):
    try:
        data = settings.PYLOAD.get_package_data(int(id))
        data['links'] = []
        for file in settings.PYLOAD.get_package_files(data['id']):
                data['links'].append(settings.PYLOAD.get_file_info(file))

        return JsonResponse(data)
        
    except:
        return HttpResponseServerError()
        
@permission('pyload.can_see_dl')
def link(request,id):
    try:
        data = settings.PYLOAD.get_file_info(int(id))
        return JsonResponse(data)
        
    except:
        return HttpResponseServerError()
