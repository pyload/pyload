<?xml version="1.0" ?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
    "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>

%for item in use_js:
<script type="text/javascript" src="static/{{item}}"></script>
%end

%for item in use_css:
<link rel="stylesheet" type="text/css" href="static/{{item}}">
%end

<meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>

%if redirect:
<meta http-equiv="refresh" content="3; url=/">
%end

<title>{{title}}</title>

</head>
<body>
