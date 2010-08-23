
from django import VERSION
from django import template
register = template.Library()
    
if VERSION[:3] < (1,1,2):
    
    class TokenNode(template.Node):
        def render(self, content):
            return ""
    
    @register.tag()
    def csrf_token(parser, token):
        """ 
        Return nothing, since csrf is deactivated in django 1.1
        """ 
        return TokenNode()
