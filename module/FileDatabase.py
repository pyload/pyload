#!/usr/bin/env python
"""
    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 3 of the License,
    or (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
    See the GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program; if not, see <http://www.gnu.org/licenses/>.

    @author: RaNaN
"""
from Queue import Queue
import sqlite3
from threading import Thread
from threading import RLock
from time import sleep
from time import time
import traceback

statusMap = {
    "finished":    0,
    "offline":     1,
    "online":      2,
    "queued":      3,
    "checking":    4,
    "waiting":     5,
    "reconnected": 6,
    "starting":    7,
    "failed":      8,
    "aborted":     9,
    "decrypting":  10,
    "custom":      11,
    "downloading": 12,
    "processing":  13
}

########################################################################
class FileHandler:
	"""Handles all request made to obtain information, 
	modify status or other request for links or packages"""

	
	#----------------------------------------------------------------------
	def __init__(self, core):
		"""Constructor"""
		self.core = core

		# translations
		self.statusMsg = [_("finished"), _("offline"), _("online"), _("queued"), _("checking"), _("waiting"), _("reconnected"), _("starting"),_("failed"), _("aborted"), _("decrypting"), _("custom"),_("downloading"), _("processing")]
		
		self.cache = {} #holds instances for files
		self.packageCache = {}  # same for packages
		#@TODO: purge the cache

		self.jobCache = {}
		
		self.lock = RLock()
		
		self.filecount = -1 # if an invalid value is set get current value from db		
		self.unchanged = False #determines if any changes was made since last call

		self.db = FileDatabaseBackend(self) # the backend


	def change(func):
		def new(*args):
			args[0].unchanged = False
			args[0].filecount = -1
			args[0].jobCache = {}
			return func(*args)
		return new
	
	#----------------------------------------------------------------------
	def save(self):
		"""saves all data to backend"""
		self.db.commit()

	#----------------------------------------------------------------------
	def syncSave(self):
		"""saves all data to backend and waits until all data are written"""
		self.db.syncSave()
		
	#----------------------------------------------------------------------
	def getCompleteData(self, queue=1):
		"""gets a complete data representation"""

		data = self.db.getAllLinks(queue)
		packs = self.db.getAllPackages(queue)
		
		data.update( [ (str(x.id), x.toDbDict()[x.id]) for x in self.cache.itervalues() ] )
		packs.update( [ (str(x.id), x.toDict()[x.id]) for x in self.packageCache.itervalues() if x.queue == queue] )

		for key, value in data.iteritems():
			if packs.has_key(str(value["package"])):
				packs[str(value["package"])]["links"][key] = value

		return packs

	#----------------------------------------------------------------------
	@change
	def addLinks(self, urls, package):
		"""adds links"""
	
		# tuple of (url, name, plugin, package)
		links = [ (x[0], x[0], x[1], package) for x in self.core.pluginManager.parseUrls(urls) ]
		
		self.db.addLinks(links, package)
		

	#----------------------------------------------------------------------
	@change
	def addPackage(self, name, folder, queue=0):
		"""adds a package, default to link collector"""
		return self.db.addPackage(name, folder, queue)

	#----------------------------------------------------------------------
	@change
	def deletePackage(self, id):
		"""delete package and all contained links"""
		
		self.lock.acquire()

		if self.packageCache.has_key(id):
			del self.packageCache[id]

		toDelete = []

		for pyfile in self.cache.itervalues():
			if pyfile.packageid == id:
				pyfile.abortDownload()
				toDelete.append(pyfile.id)
		
		for pid in toDelete:
			del self.cache[pid]

		self.db.deletePackage(id)
		
		
		self.lock.release()

	#----------------------------------------------------------------------
	@change
	def deleteLink(self, id):
		"""deletes links"""
		
		self.lock.acquire()
		
		if self.cache.has_key(id):
			if id in self.core.threadManager.processingIds():
				self.cache[id].abortDownload()
	
			#del self.cache[id]
			
		self.lock.release()
		
		self.db.deleteLink(id)

	#----------------------------------------------------------------------
	def releaseLink(self, id):
		"""removes pyfile from cache"""
		if self.cache.has_key(id):
			del self.cache[id]

	#----------------------------------------------------------------------
	def releasePackage(self, id):
		"""removes package from cache"""
		if self.packageCache.has_key(id):
			del self.packageCache[id]

	#----------------------------------------------------------------------
	def updateLink(self, pyfile):
		"""updates link"""
		self.db.updateLink(pyfile)

	#----------------------------------------------------------------------
	def updatePackage(self, pypack):
		"""updates a package"""
		self.db.updatePackage(pypack)

	#----------------------------------------------------------------------
	def getPackage(self, id):
		"""return package instance"""
		
		if self.packageCache.has_key(id):
			return self.packageCache[id]
		else:
			return self.db.getPackage(id)
	
	#----------------------------------------------------------------------
	def getPackageData(self, id):
		"""returns dict with package information"""
		pack = self.getPackage(id)
		pack = pack.toDict()[id]
		
		data = self.db.getPackageData(id)
		
		data.update( [ (str(x.id), x.toDbDict()[x.id]) for x in self.cache.itervalues() ] )
		
		pack["links"] = data
		
		return pack
	
	#----------------------------------------------------------------------
	def getFile(self, id):
		"""returns pyfile instance"""
		if self.cache.has_key(id):
			return self.cache[id]
		else:
			return self.db.getFile(id)

	#----------------------------------------------------------------------
	def getJob(self, occ):
		"""get suitable job"""
		
		self.lock.acquire()
		
		#@TODO clean mess
		
		if self.jobCache.has_key(occ):
			if self.jobCache[occ]:
				id = self.jobCache[occ].pop()
				if id == "empty":
					pyfile = None
				else:
					pyfile = self.getFile(id)
			else:
				jobs = self.db.getJob(occ)
				jobs.reverse()
				if not jobs:
					self.jobCache[occ].append("empty")
					pyfile = None
				else:
					self.jobCache[occ].extend(jobs)
					pyfile = self.getFile(self.jobCache[occ].pop())
				
		else:
			self.jobCache = {} #better not caching to much
			jobs = self.db.getJob(occ)
			jobs.reverse()
			self.jobCache[occ] = jobs
			
			if not jobs:
				self.jobCache[occ].append("empty")
				pyfile = None
		
			pyfile = self.getFile(self.jobCache[occ].pop())
			#@TODO: maybe the new job has to be approved...
					
		
		#pyfile = self.getFile(self.jobCache[occ].pop())
		
		self.lock.release()
		return pyfile
	
	
	#----------------------------------------------------------------------
	def getFileCount(self):
		"""returns number of files"""

		if self.filecount == -1:
			self.filecount = self.db.filecount(1)
		
		return self.filecount
	
	#----------------------------------------------------------------------
	def getQueueCount(self):
		"""number of files that have to be processed"""
		pass
	
	#----------------------------------------------------------------------
	def restartPackage(self, id):
		"""restart package"""
		for pyfile in self.cache.itervalues():
			if pyfile.packageid == id:
				self.restartFile(pyfile.id)
		
		self.db.restartPackage(id)
	
	def restartFile(self, id):
		""" restart file"""
		if self.cache.has_key(id):
			self.cache[id].abortDownload()
			self.cache[id].status = 3
			self.cache[id].name = self.cache[id].url
			self.cache[id].sync()
		else:
			self.db.restartFile(id)
		


#########################################################################
class FileDatabaseBackend(Thread):
	"""underlying backend for the filehandler to save the data"""

	def __init__(self, manager):
		Thread.__init__(self)

		self.setDaemon(True)

		self.manager = manager

		self.jobs = Queue() # queues for jobs
		self.res = Queue()

		self.start()


	def queue(func):
		"""use as decorator when fuction directly executes sql commands"""
		def new(*args):
			args[0].jobs.put((func, args, 0))
			return args[0].res.get()
		return new

	def async(func):
		"""use as decorator when function does not return anything and asynchron execution is wanted"""
		def new(*args):
			args[0].jobs.put((func, args, 1))
			return True
		return new

	def run(self):
		"""main loop, which executes commands"""

		self.conn = sqlite3.connect("files.db")
		self.c = self.conn.cursor()
		#self.c.execute("PRAGMA synchronous = OFF")
		self._createTables()

		while True:
			try:
				f, args, async = self.jobs.get()
				if f == "quit": return True
				res = f(*args)
				if not async: self.res.put(res)
			except Exception, e:
				#@TODO log etc
				print "Database Error @", f.__name__, args[1:], e
				traceback.print_exc()
				if not async: self.res.put(None)

	def shutdown(self):
		self.save()
		self.jobs.put(("quit", "", 0))

	def _createTables(self):
		"""create tables for database"""

		self.c.execute('CREATE TABLE IF NOT EXISTS "packages" ("id" INTEGER PRIMARY KEY AUTOINCREMENT, "name" TEXT NOT NULL, "folder" TEXT, "password" TEXT, "site" TEXT, "queue" INTEGER DEFAULT 0 NOT NULL)')
		self.c.execute('CREATE TABLE IF NOT EXISTS "links" ("id" INTEGER PRIMARY KEY AUTOINCREMENT, "url" TEXT NOT NULL, "name" TEXT, "size" INTEGER DEFAULT 0 NOT NULL, "status" INTEGER DEFAULT 3 NOT NULL, "plugin" TEXT DEFAULT "BasePlugin" NOT NULL, "error" TEXT, "package" INTEGER DEFAULT 0 NOT NULL, FOREIGN KEY(package) REFERENCES packages(id))')
		self.c.execute('CREATE INDEX IF NOT EXISTS "pIdIndex" ON links(package)')
		self.c.execute('VACUUM')
		
	#----------------------------------------------------------------------
	@queue
	def filecount(self, queue):
		"""returns number of files in queue"""
		self.c.execute("SELECT l.id FROM links as l INNER JOIN packages as p ON l.package=p.id WHERE p.queue=? ORDER BY l.id", (queue,))
		r = self.c.fetchall()
		return len(r)
		
	@queue
	def addLink(self, url, name, plugin, package):
		self.c.execute('INSERT INTO links(url, name, plugin, package) VALUES(?,?,?,?)', (url, name, plugin, package))
		return self.c.lastrowid

	@queue
	def addLinks(self, links, package):
		""" links is a list of tupels (url,name,plugin)"""
		self.c.executemany('INSERT INTO links(url, name, plugin, package) VALUES(?,?,?,?)', links)

	@queue
	def addPackage(self, name, folder, queue):

		self.c.execute('INSERT INTO packages(name, folder, queue) VALUES(?,?,?)', (name, folder, queue))
		return self.c.lastrowid

	@queue
	def deletePackage(self, id):

		self.c.execute('DELETE FROM links WHERE package=?', (str(id), ))
		self.c.execute('DELETE FROM packages WHERE id=?', (str(id), ))

	@queue
	def deleteLink(self, id):

		self.c.execute('DELETE FROM links WHERE id=?', (str(id), ))


	@queue
	def getAllLinks(self, q):
		"""return information about all links in queue q

		q0 queue
		q1 collector

		format:

		{
		    id: {'name': name, ... 'package': id }, ...
		}

		"""
		self.c.execute('SELECT l.id,l.url,l.name,l.size,l.status,l.error,l.plugin,l.package FROM links as l INNER JOIN packages as p ON l.package=p.id WHERE p.queue=? ORDER BY l.id', (q, ))
		data = {}
		for r in self.c:
			data[str(r[0])] = {
				'url': r[1],
				'name': r[2],
				'size': r[3],
				'status': r[4],
			    'statusmsg': self.manager.statusMsg[r[4]],
				'error': r[5],
				'plugin': r[6],
				'package': r[7]
			}

		return data

	@queue
	def getAllPackages(self, q):
		"""return information about packages in queue q
		(only useful in get all data)

		q0 queue
		q1 collector

		format:

		{
		    id: {'name': name ... 'links': {} }, ...
		}
		"""
		self.c.execute('SELECT id,name,folder,site,password,queue FROM packages WHERE queue=? ORDER BY id', str(q))

		data = {}
		for r in self.c:
			data[str(r[0])] = {
				'name': r[1],
				'folder': r[2],
				'site': r[3],
				'password': r[4],
				'queue': r[5],
				'links': {}
			}

		return data


	def getLinkData(self, id):
		"""get link information"""
		pass

	@queue
	def getPackageData(self, id):
		"""get package data"""
		self.c.execute('SELECT id,url,name,size,status,error,plugin,package FROM links WHERE package=? ORDER BY id', (str(id),))

		data = {}
		for r in self.c:
			data[str(r[0])] = {
				'url': r[1],
				'name': r[2],
				'size': r[3],
				'status': r[4],
			    'statusmsg': self.manager.statusMsg[r[4]],
				'error': r[5],
				'plugin': r[6],
				'package': r[7]
			}

		return data


	@async
	def updateLink(self, f):
		self.c.execute('UPDATE links SET url=?,name=?,size=?,status=?,error=?,package=? WHERE id=?', (f.url, f.name, f.size, f.status, f.error, str(f.packageid), str(f.id)))

	@async
	def updatePackage(self, p):
		self.c.execute('UPDATE packages SET name=?,folder=?,site=?,password=?,queue=? WHERE id=?', (p.name, p.folder, p.site, p.password, p.queue, str(p.id)))

	@async
	def restartFile(self, id):
		self.c.execute('UPDATE links SET status=3 WHERE id=?', ( str(id), ) )

	@async
	def restartPackage(self, id):
		self.c.execute('UPDATE links SET status=3 WHERE package=?', ( str(id), ) )
		
	@async
	def commit(self):
		self.conn.commit()
		
	@queue
	def syncSave(self):
		self.conn.commit()

	@queue
	def getPackage(self, id):
		"""return package instance from id"""
		self.c.execute("SELECT name,folder,site,password,queue FROM packages WHERE id=?", (str(id),))
		r = self.c.fetchone()
		if not r: return None
		return PyPackage(self.manager, id, *r)

	#----------------------------------------------------------------------
	@queue
	def getFile(self, id):
		"""return link instance from id"""
		self.c.execute("SELECT url, name, size, status, error, plugin, package FROM links WHERE id=?", (str(id),))
		r = self.c.fetchone()
		if not r: return None
		return PyFile(self.manager, id, *r)


	@queue
	def getJob(self, occ):
		"""return pyfile instance, which is suitable for download and dont use a occupied plugin"""
		self.c.execute("SELECT l.id FROM links as l INNER JOIN packages as p ON l.package=p.id WHERE p.queue=1 AND l.plugin NOT IN %s AND l.status IN (2,3,6) LIMIT 5" % str(occ)) # very bad!

		return [x[0] for x in self.c ]

class PyFile():
	def __init__(self, manager, id, url, name, size, status, error, pluginname, package):
		self.m = manager
		self.m.cache[int(id)] = self
		
		self.id = int(id)
		self.url = url
		self.name = name
		self.size = size
		self.status = status
		self.pluginname = pluginname
		self.packageid = package #should not be used, use package() instead
		self.error = error
		# database information ends here
		
		self.plugin = None
			
		self.waitUntil = 0 # time() + time to wait
		
		# status attributes
		self.active = False #obsolete?
		self.abort = False
		self.reconnected = False

		
	def __repr__(self):
		return "PyFile %s: %s@%s" % (self.id, self.name, self.pluginname)
		
	def initPlugin(self):
		""" inits plugin instance """
		self.pluginmodule = self.m.core.pluginManager.getPlugin(self.pluginname)
		self.pluginclass = getattr(self.pluginmodule, self.pluginname)
		self.plugin = self.pluginclass(self)
	
	
	def package(self):
		""" return package instance"""
		return self.m.getPackage(self.packageid)

	def setStatus(self, status):
		self.status = statusMap[status]
		self.sync() #@TODO needed aslong no better job approving exists

	def hasStatus(self, status):
		return statusMap[status] == self.status
	
	def sync(self):
		"""sync PyFile instance with database"""
		self.m.updateLink(self)

	def release(self):
		"""sync and remove from cache"""
		self.sync()
		self.m.releaseLink(self.id)

	def delete(self):
		"""delete pyfile from database"""
		self.m.deleteLink(self.id)

	def toDict(self):
		"""return dict with all information for interface"""
		return self.toDbDict()

	def toDbDict(self):
		"""return data as dict for databse

		format:

		{
		    id: {'url': url, 'name': name ... }
		}

		"""
		return {
			self.id: {
				'url': self.url,
				'name': self.name,
		        'plugin' : self.pluginname,
				'size': self.getSize(),
				'status': self.status,
		        'statusmsg': self.m.statusMsg[self.status],
				'package': self.packageid,
				'error': self.error
			}
		}
	
	def abortDownload(self):
		"""abort pyfile if possible"""
		self.m.core.log.info(_("Download aborted: %s" % self.name))
		while self.id in self.m.core.threadManager.processingIds():
			self.abort = True
			if self.plugin: self.plugin.req.abort = True
			sleep(0.1)
		
		abort = False 
		self.plugin.req.abort = False
		
	def finishIfDone(self):
		"""set status to finish and release file if every thread is finished with it"""
		
		if self.id in self.m.core.threadManager.processingIds():
			return False
		
		self.setStatus("finished")
		self.release()
		return True
	
	def formatWait(self):
		""" formats and return wait time in humanreadable format """
		return self.waitUntil - time()
	
	def getSpeed(self):
		""" calculates speed """
		try:
			return self.plugin.req.get_speed()
		except:
			return 0
		
	def getETA(self):
		""" gets established time of arrival"""
		try:
			return self.plugin.req.get_ETA()
		except:
			return 0
	
	def getKbLeft(self):
		""" gets kb left """
		try:
			return self.plugin.req.kB_left()
		except:
			return 0
	
	def getPercent(self):
		""" get % of download """
		try:
			return int((float(self.plugin.req.dl_arrived)  / self.plugin.req.dl_size) * 100)
		except:
			return 0
		
	def getSize(self):
		""" get size of download """
		if self.size: return self.size
		else:
			try:
				return self.plugin.req.dl_size
			except:
				return 0

class PyPackage():
	def __init__(self, manager, id, name, folder, site, password, queue):
		self.m = manager
		self.m.packageCache[int(id)] = self

		self.id = int(id)
		self.name = name
		self.folder = folder
		self.site = site
		self.password = password
		self.queue = queue

	def toDict(self):
		"""return data as dict

		format:

		{
		    id: {'name': name ... 'links': {} } }
		}

		"""
		return {
			self.id: {
				'name': self.name,
				'folder': self.folder,
				'site': self.site,
				'password': self.password,
				'queue': self.queue,
				'links': {}
			}
		}

	def getChildren(self):
		"""get information about contained links"""
		raise NotImplementedError

	def sync(self):
		"""sync with db"""
		self.m.updatePackage(self)

	def release(self):
		"""sync and delete from cache"""
		self.sync()
		self.m.releasePackage(self.id)

	def delete(self):
		self.m.deletePackage(self.id)


if __name__ == "__main__":

	pypath = "."

	db = FileHandler(None)

	#p = PyFile(db, 5)
	#sleep(0.1)

	a = time()

	#print db.addPackage("package", "folder" , 1)
	
	#print db.addPackage("package", "folder",  1)

	#db.addLinks([x for x in range(0,200)], 5)

	db.save()

	b = time()
	print "adding 200 links, single sql execs, no commit", b-a


	res = db.getCompleteData(1)
	#print res
	r = [ len(x["links"]) for x in res.itervalues() ]
	print r
	c = time()
	print "get all links", c-b

	#i = 2
	#db.updateLink(i, "urlupdate%s" % i, "nameupdate%s" % i, i, i, i,i)

	d = time()
	print "update one link", d-c

	#p.sync()
	#p.remove()

	e = time()
	print "sync and remove link", e-d

	db.save()

	db.deletePackage(1)
	#db.commit()

	f = time()
	print "commit, remove package/links, commit", f-e

	#db.commit()
	sleep(0.5)

	g = time()
	print "empty commit", g-f -0.5


	job = db.getJob("")
	print job
	
	h = time()
	#print db.getFileCount()
	
	print "get job", h-g

	print db.getFileCount()
	
	i = time()
	
	print "file count", i-h
	
	
	print db.getJob("")
	
	j = time()
	
	
	print "get job 2", j-i
	
	for i in db.cache.itervalues():
		i.sync()
	
	sleep(1)
	
	