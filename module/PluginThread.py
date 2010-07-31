#!/usr/bin/env python
# -*- coding: utf-8 -*-

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

from threading import Thread
from Queue import Queue

from time import sleep
from traceback import print_exc

from pycurl import error
from module.plugins.Plugin import Abort, Reconnect, Retry, Fail

########################################################################
class PluginThread(Thread):
	"""abstract base class for thread types"""

	#----------------------------------------------------------------------
	def __init__(self, manager):
		"""Constructor"""
		Thread.__init__(self)
		self.setDaemon(True)
		self.m = manager #thread manager
		

########################################################################
class DownloadThread(PluginThread):
	"""thread for downloading files from 'real' hoster plugins"""

	#----------------------------------------------------------------------
	def __init__(self, manager):
		"""Constructor"""
		PluginThread.__init__(self, manager)
		
		self.queue = Queue() # job queue
		self.active = False
		
		self.start()
		
	#----------------------------------------------------------------------
	def run(self):
		"""run method"""
		
		while True:
			self.active = self.queue.get()
			pyfile = self.active
			
			if self.active == "quit":
				return True
			
			self.m.log.info(_("Download starts: %s" % pyfile.name))
			
			try:
				pyfile.plugin.preprocessing(self)
				
			except NotImplementedError:
				
				self.m.log.error(_("Plugin %s is missing a function.") % pyfile.pluginname)
				continue
			
			except Abort:
				self.m.log.info(_("Download aborted: %s") % pyfile.name)
				pyfile.setStatus("aborted")
				
				self.active = False
				pyfile.release()
				continue
				
			except Reconnect:
				self.queue.put(pyfile)
				pyfile.req.clearCookies()
				
				while self.m.reconnecting.isSet():
					sleep(0.5)
				
				continue
			
			except Retry:
				
				self.m.log.info(_("Download restarted: %s") % pyfile.name)
				self.queue.put(pyfile)
				continue
			
			except Fail,e :
				
				msg = e.args[0]
				
				if msg == "offline":
					pyfile.setStatus("offline")
					self.m.log.warning(_("Download is offline: %s") % pyfile.name)
				else:
					pyfile.setStatus("failed")
					self.m.log.warning(_("Download failed: %s | %s") % (pyfile.name, msg))
					pyfile.error = msg
				
				self.active = False
				pyfile.release()
				continue
						
			except error, e:
				code, msg = e
				print "pycurl error", code, msg
				
				self.active = False
				pyfile.release()
				continue
			
			except Exception, e:
				pyfile.setStatus("failed")
				self.m.log.error(_("Download failed: %s | %s") % (pyfile.name, str(e)))
				
				if self.m.core.debug:
					print_exc()
				
				self.active = False
				pyfile.release()
				continue
			
			
			finally:
				self.m.core.files.save()
			
			
			self.m.log.info(_("Download finished: %s") % pyfile.name)
			
			#@TODO hooks, packagaefinished etc
			
			self.m.core.hookManager.downloadFinished(pyfile)
			
			
			self.active = False	
			pyfile.finishIfDone()
			self.m.core.files.save()
			
	#----------------------------------------------------------------------
	def put(self, job):
		"""assing job to thread"""
		self.queue.put(job)
	
	#----------------------------------------------------------------------
	def stop(self):
		"""stops the thread"""
		self.put("quit")
		
		
		
########################################################################
class DecrypterThread(PluginThread):
	"""thread for decrypting"""

	#----------------------------------------------------------------------
	def __init__(self, manager, pyfile):
		"""constructor"""
		PluginThread.__init__(self, manager)
		
		self.active = pyfile
		manager.localThreads.append(self)
		
		pyfile.setStatus("decrypting")
		
		self.start()
		
	#----------------------------------------------------------------------
	def run(self):
		"""run method"""
		
		pyfile = self.active
		
		try:
			self.m.log.info(_("Decrypting starts: %s") % self.active.name)
			self.active.plugin.preprocessing(self)
				
		except NotImplementedError:
			
			self.m.log.error(_("Plugin %s is missing a function.") % self.active.pluginname)
			return
		
		except Fail,e :
			
			msg = e.args[0]
			
			if msg == "offline":
				self.active.setStatus("offline")
				self.m.log.warning(_("Download is offline: %s") % self.active.name)
			else:
				self.active.setStatus("failed")
				self.m.log.warning(_("Decrypting failed: %s | %s") % (self.active.name, msg))
				self.active.error = msg
			
			return
					
		
		except Exception, e:
		
			self.active.setStatus("failed")
			self.m.log.error(_("Decrypting failed: %s | %s") % (self.active.name, str(e)))
			self.active.error = str(e)
			
			if self.m.core.debug:
				print_exc()
			
			return
		
		
		finally:
			self.active.release()
			self.active = False
			self.m.core.files.save()
			self.m.localThreads.remove(self)
	
		
		#self.m.core.hookManager.downloadFinished(pyfile)
	
		
		#self.m.localThreads.remove(self)
		#self.active.finishIfDone()
		pyfile.delete()
    
########################################################################
class HookThread(PluginThread):
	"""thread for hooks"""

	#----------------------------------------------------------------------
	def __init__(self, m, function, pyfile):
		"""Constructor"""
		PluginThread.__init__(self, m)
		
		self.f = function
		self.active = pyfile
		
		m.localThreads.append(self)
		
		pyfile.setStatus("processing")
		
		self.start()
		
	def run(self):
		self.f(self.active)
		
		
		self.m.localThreads.remove(self)
		self.active.finishIfDone()
		
		
    
	