import urllib

def api_request( method, params ):
    url = 'http://localhost:8000/api/' + method    
    data = urllib.urlencode(params)
    u = urllib.urlopen(url, data)
    return u.read()

login_params = {
    'username': 'api',
    'password': 'apiapi'
}

api_key = api_request('login', login_params).strip('"')

print 'API_REQUEST:login:' + api_key
status_server = api_request('statusServer', {'session': api_key})
print 'API_REQUEST:statusServer:' + status_server
