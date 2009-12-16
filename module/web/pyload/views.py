# Create your views here.
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.conf import settings
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from os.path import join


def check_server(function):
    def _dec(view_func):
        def _view(request, *args, **kwargs):
            try:
                version = settings.PYLOAD.get_server_version()
            except Exception, e:
                return base(request, messages=['Can\'t connect to pyLoad. Please check your configuration and make sure pyLoad is running.',str(e)])
            return view_func(request, *args, **kwargs)
        
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
            if request.user.has_perm(perm):
                return view_func(request, *args, **kwargs)
            else:
                return base(request, messages=['You don\'t have permission to view this page.'])
        
        _view.__name__ = view_func.__name__
        _view.__dict__ = view_func.__dict__
        _view.__doc__ = view_func.__doc__

        return _view

    return _dec


def base(request, messages):
    return render_to_response(join(settings.TEMPLATE,'base.html'), {'messages': messages},RequestContext(request))

@login_required
@permission('pyload.can_see_dl')
@check_server
def home(request):
    return render_to_response(join(settings.TEMPLATE,'home.html'), RequestContext(request))
    

@login_required
@permission('pyload.can_see_dl')
@check_server
def queue(request):
    return render_to_response(join(settings.TEMPLATE,'queue.html'), RequestContext(request))


@login_required
@permission('pyload.can_download')
@check_server
def downloads(request):
    return render_to_response(join(settings.TEMPLATE,'downloads.html'), RequestContext(request))


@login_required
@permission('pyload.user.can_see_logs')
@check_server
def logs(request):
    return render_to_response(join(settings.TEMPLATE,'logs.html'), RequestContext(request))
    
    