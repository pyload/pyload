%header =  'pyLoad Webinterface'
%include header title=header, use_js=['mootools-1.2.3-core.js'], use_css= ['default.css']

<a class="anchor" name="dokuwiki__top" id="dokuwiki__top"></a>

<div id="head-panel">

	<div id="head-search-and-login">


		<form action="" accept-charset="utf-8">
			<label for="head-search"><img src="static/default/head-search-noshadow.png" alt="Search" style="vertical-align:middle; margin:2px" /></label>
			<input type="hidden" name="do" value="search" />
			<input id="head-search" type="text" style="width:140px;" value="search" accesskey="f" name="id" title="" />
		</form>



				<img src="static/default/head-login.png" alt="User:" style="vertical-align:middle; margin:2px" /><span style="padding-right: 2px;">RaNaN (ranan) </span>

					<ul id="user-actions">
				<li><a href="/start?do=logout&amp;sectok=ff40bdf226c283991652e062d187c43a"  class="action logout" rel="nofollow">Logout</a></li>
				<li><a href="/start?do=profile"  class="action profile" rel="nofollow">Update Profile</a></li>
				<li></li>
				<li></li>
			</ul>

	</div>

	<a href="/"><img id="head-logo" src="/static/default/pyload-logo-edited3.5-new-font-small.png" alt="pyLoad" /></a>

	<div id="head-menu">
		<ul>
			<li class=" selected"><a href="/" title=""><img src="static/default/head-menu-home.png" alt="" /> Home</a></li><li class=""><a href="/news" title=""><img src="static/default/head-menu-news.png" alt="" /> News</a></li><li class=""><a href="/wiki" title=""><img src="static/default/head-menu-wiki.png" alt="" /> Wiki</a></li><li class=""><a href="/download" title=""><img src="static/default/head-menu-download.png" alt="" /> Download</a></li><li class=""><a href="/development" title=""><img src="static/default/head-menu-development.png" alt="" /> Development</a></li><li class="right"><a href="/start?do=index"  class="action index" accesskey="x" rel="nofollow"><img src="static/default/head-menu-index.png" alt="" />Index</a></li><li class="right"><a href="/start?do=recent"  class="action recent" accesskey="r" rel="nofollow"><img src="static/default/head-menu-recent.png" alt="" />Recent Changes</a></li>		</ul>
	</div>

	<div style="clear:both;"></div>
</div>

<ul id="page-actions">
	<li><a href="/start?do=edit&amp;rev="  class="action edit" accesskey="e" rel="nofollow">Edit this page</a></li>
	<li><a href="/start?do=revisions"  class="action revisions" accesskey="o" rel="nofollow">Old revisions</a></li>
	<li><a href="/start?do=backlink"  class="action backlink" rel="nofollow">Backlinks</a></li>
	<li></li>
	<!--<li><a href="/start?do=index"  class="action index" accesskey="x" rel="nofollow">Index</a></li>
	<li><a href="/start?do=recent"  class="action recent" accesskey="r" rel="nofollow">Recent changes</a></li>-->
</ul>

<div id="body-wrapper" class="dokuwiki">

	<div id="content" lang="en" dir="ltr">


<h1><a name="pyload_download_manager_for_1_click_hoster" id="pyload_download_manager_for_1_click_hoster">pyLoad — download manager for 1 click hoster</a></h1>
<div class="level1">

<p>

<a href="/screenshots" class="media" title="screenshots"><img src="/_media/:screenshot-reflection-small.png" class="mediaright" align="right" alt="" /></a>
</p>

<p>
pyLoad is a free and open source downloader for 1-click-hosting sites like rapidshare.com or uploaded.to.
</p>

<p>
Link-Crypt services like lix.in as well as the Link-Container Files RSDF, CCF and DLC are also supported.
</p>

<p>
pyLoad is currently under heavy development. It aims to be fully automated in as many ways as possible, so you don&#039;t have to sit in front of your computer waiting for a download ticket. It will be good for long-time unattended downloading of files from sharehosters.
</p>

</div>

<h2><a name="features" id="features">Features</a></h2>
<div class="level2">
<ul>
<li class="level1"><div class="li"> <strong>written entirely in Python</strong></div>
</li>
<li class="level1"><div class="li"> <strong>gets links from Link-Crypt services</strong></div>
</li>
<li class="level1"><div class="li"> <strong>can open RSDF, CCF and DLC containers</strong></div>
</li>
<li class="level1"><div class="li"> <strong>User interfaces: CLI and wxWidgets (currently in development)</strong></div>
</li>
<li class="level1"><div class="li"> <strong>Open Source and Free Software (<acronym title="GNU General Public License">GPL</acronym> v3 or later)</strong></div>
</li>
</ul>

</div>

	</div>

	<hr style="clear: both;" />

<div id="foot">© 2008-2009 the pyLoad Team

	<a href="#dokuwiki__top" class="action top" accesskey="x"><span>Back to top</span></a><br />
	<!--<div class="breadcrumbs"></div>-->


</div>

</div>

%include footer