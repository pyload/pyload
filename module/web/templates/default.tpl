%header =  'pyLoad Webinterface'
%include header title=header, use_js=['mootools-1.2.3-core.js'], use_css= ['default.css']

<a class="anchor" name="dokuwiki__top" id="dokuwiki__top"></a>

<div id="head-panel">

	<div id="head-search-and-login">



				<img src="static/default/head-login.png" alt="User:" style="vertical-align:middle; margin:2px" /><span style="padding-right: 2px;">User</span>

					<ul id="user-actions">
				<li><a href="/start?do=logout&amp;sectok=ff40bdf226c283991652e062d187c43a"  class="action logout" rel="nofollow">Logout</a></li>
				<li></li>
				<li></li>
			</ul>

	</div>

	<a href="/"><img id="head-logo" src="/static/default/pyload-logo-edited3.5-new-font-small.png" alt="pyLoad" /></a>

	<div id="head-menu">
		<ul>
			<li class=" selected"><a href="/" title=""><img src="static/default/head-menu-home.png" alt="" /> Home</a></li><li class=""><a href="/news" title=""><img src="static/default/head-menu-news.png" alt="" /> News</a></li><li class=""><a href="/wiki" title=""><img src="static/default/head-menu-wiki.png" alt="" /> Wiki</a></li><li class=""><a href="/download" title=""><img src="static/default/head-menu-download.png" alt="" /> Download</a></li><li class=""><a href="/development" title=""><img src="static/default/head-menu-development.png" alt="" /> Development</a></li><li class="right"><a href="/start?do=index"  class="action index" accesskey="x" rel="nofollow"><img src="static/default/head-menu-index.png" alt="" />Logs</a></li>		</ul>
	</div>

	<div style="clear:both;"></div>
</div>

<ul id="page-actions">
	<li><a href=""  class="action revisions" accesskey="o" rel="nofollow">Reload page</a></li>

</ul>

<div id="body-wrapper" class="dokuwiki">

	<div id="content" lang="en" dir="ltr">


<h1><a name="pyload_download_manager_for_1_click_hoster" id="pyload_download_manager_for_1_click_hoster">pyLoad — Webinterface</a></h1>
<div class="level1">

%if page == "login":

</div>
<div class="centeralign">
<form action="" method="post" accept-charset="utf-8" id="login"><div class="no">
<input type="hidden" name="do" value="login" /><fieldset ><legend>Login</legend>
<label class="block" for="focus__this"><span>Username</span> <input type="text" id="focus__this" name="u" class="edit" /></label><br />
<label class="block"><span>Password</span> <input type="password" name="p" class="edit" /></label><br />
<label class="simple" for="remember__me"><input type="checkbox" id="remember__me" name="r" value="1" /> <span>Remember me</span></label>
<input type="submit" value="Login" class="button" />
</fieldset>
</div></form>
</div>
<br>

%else:
<h2>Downloads:</h2>

% for link in links:

<p>
{{str(link)}}
</p>

%end

%end
	<hr style="clear: both;" />

<div id="foot">© 2008-2009 the pyLoad Team

	<a href="#dokuwiki__top" class="action top" accesskey="x"><span>Back to top</span></a><br />
	<!--<div class="breadcrumbs"></div>-->


</div>

</div>

%include footer