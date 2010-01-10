# Create your views here.
from os.path import join

from django.conf import settings
from django.core.serializers import json
from django.http import HttpResponse
from django.http import HttpResponseForbidden
from django.http import HttpResponseServerError
from django.utils import simplejson
  
def permission(perm):
    def _dec(view_func):
        def _view(request, * args, ** kwargs):
            if request.user.has_perm(perm) and request.user.is_authenticated():
                return view_func(request, * args, ** kwargs)
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
                                           content)#, content_type='application/json') #@TODO uncomment
        self['Cache-Control'] = 'no-cache, must-revalidate'


@permission('pyload.can_add')
def add_package(request):
    
    name = request.POST['add_name']
    
    if name is None or "":
        return HttpResponseServerError()
    
    links = request.POST['add_links'].split("\n")
    
    try:
        f = request.FILES['add_file']
        fpath = join(settings.DL_ROOT, f.name)
        destination = open(fpath, 'wb')
        for chunk in f.chunks():
            destination.write(chunk)
        destination.close()
        links.insert(0, fpath)
    except:
        pass
    
    links = filter(lambda x: x is not "", links)
     
    settings.PYLOAD.add_package(name, links)
    
    return JsonResponse("success")


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
def package(request, id):
    try:
        data = settings.PYLOAD.get_package_data(int(id))
        data['links'] = []
        for file in settings.PYLOAD.get_package_files(data['id']):
            data['links'].append(settings.PYLOAD.get_file_info(file))

        return JsonResponse(data)
        
    except:
        return HttpResponseServerError()
        
@permission('pyload.can_see_dl')
def link(request, id):
    try:
        data = settings.PYLOAD.get_file_info(int(id))
        return JsonResponse(data)
        
    except:
        return HttpResponseServerError()
