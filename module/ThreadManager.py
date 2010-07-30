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

from threading import Event
import PluginThread

########################################################################
class ThreadManager:
	"""manages the download threads, assign jobs, reconnect etc"""

	#----------------------------------------------------------------------
	def __init__(self, core):
		"""Constructor"""
		self.core = core
		self.log = core.log
				
		self.threads = []  # thread list
		self.localThreads = []  #hook+decrypter threads
		
		self.pause = True
		
		self.reconnecting = Event()
		self.reconnecting.clear()
		
		for i in range(0, self.core.config.get("general","max_downloads") ):
			self.createThread()
		
		
		
	#----------------------------------------------------------------------
	def createThread(self):
		"""create a download thread"""
		
		thread = PluginThread.DownloadThread(self)		
		self.threads.append(thread)
		
	#----------------------------------------------------------------------
	def downloadingIds(self):
		"""get a list of the currently downloading pyfile's ids"""
		return [x.active.id for x in self.threads if x.active]
	
	#----------------------------------------------------------------------
	def processingIds(self):
		"""get a id list of all pyfiles processed"""
		return [x.active.id for x in self.threads+self.localThreads if x.active]
		
		
	#----------------------------------------------------------------------
	def work(self):
		"""run all task which have to be done (this is for repetivive call by core)"""
				
		self.checkReconnect()
		self.checkThreadCount()
		self.assignJob()
	
	#----------------------------------------------------------------------
	def checkReconnect(self):
		"""checks if reconnect needed"""
		pass
	
	#----------------------------------------------------------------------
	def checkThreadCount(self):
		"""checks if there are need for increasing or reducing thread count"""
		
		if len(self.threads) == self.core.config.get("general", "max_downloads"):
			return True
		elif len(self.threads) < self.core.config.get("general", "max_downloads"):
			self.createThread()
		else:
			#@TODO: close thread
			pass
		
	
	#----------------------------------------------------------------------
	def assignJob(self):
		"""assing a job to a thread if possible"""
		
		if self.pause: return
		
		free = [x for x in self.threads if not x.active]


		
		occ = [x.active.pluginname for x in self.threads if x.active and not x.active.plugin.multiDL ]
		occ.sort()
		occ = set(occ)
		job = self.core.files.getJob(tuple(occ))
		if job:
			try:
				job.initPlugin()
			except Exception, e:
				self.log.critical(str(e))
			
			if job.plugin.__type__ == "hoster":
				if free:
					thread = free[0]
					thread.put(job)
				else:
					#put job back
					self.core.files.jobCache[occ].append(job.id)
					
			else:
				thread = PluginThread.DecrypterThread(job)
					
	
		
		
		
    
	