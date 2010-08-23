
from django import VERSION
from django import template
register = template.Library()
    
if VERSION[:3] < (1,1,2):
    
    @register.tag()
    def csrf_token():
        """ 
        Return nothing, since csrf is deactivated in django 1.1
        """ 
        return ""
