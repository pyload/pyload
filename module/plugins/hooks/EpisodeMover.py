#!/usr/bin/python
# -*- coding: utf-8 -*-

#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License,published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

import string
import re
from module.plugins.Hook import Hook
from threading import Thread, RLock
import shutil as mv
from Queue import Queue
import time
import urllib2
from module.utils import fs_encode,save_path
from module.common.json_layer import json
from datetime import datetime as dt
import traceback
import inspect
#remote debugging
#from module.common.pydevsrc import pydevd 


class EpisodeMover(Hook):
    '''This class implements means to automatically move tv episodes within the underlying file system.
       

    Once pointed towards the local path of tv shows EM automatically acts upon the unrarFinished, packageFinished
    downloadFinished events trying to sort out the actual tv episodes based on certain criteria such,regex pattern and so forth.
    On passing the checks the file is moved to its final destination. 
    '''
    
#    TODO: (in no particular order)
#    -Implement feature for defining custom strings EM can process (Colbert Report/Daily Show/...)
#    -Overwrite if size(src) > size(dst)
#    -Implement mapping of UTF8-encoded Umlaute to ASCII-encoded Umlaute and use it for querying/matching
#    -Add unmatched files to a log file 
#    -Implement prioritisation for shows with same word length where one show also is the name of a rls grp: Dexter.S07E11.720p.HDTV.x264-EVOLVE.mkv
#    -Allow skipping of certain files triggered by a specific package name declared in an external text file AKA blacklisting
#    -Implement database(mysql/plain txt/...) for saving local tv shows. Functionality: refresh on failed local match/... 

#    Notes: 
#    -use "self.manager.dispatchEvent("name_of_the_event", arg1, arg2, ..., argN)" to define your own events! ;)
    __name__ = "EpisodeMover"
    __version__ = "0.531"
    __description__ = "EpisodeMover(EM) moves episodes to their final destination after downloading or extraction"
    __config__ = [  ("activated" , "bool" , "Activated"  , "False" ), 
                    ("tvshows", "folder", "This is the path to the locally existing tv shows", ""),
                    ("create_season", "bool","Create season folder if necessary", "False"),
                    ("extensions","list","Add your own _comma-separated_ file extensions for EM to watch for","mkv,ts,avi,wmv,mpeg"),
                    ("overwrite","bool","Overwrite existing episodes","False"),
                    ("season_text", "str", "Add your own season text w/o a trailing whitespace", "Season"),
                    ("arbitrary","bool","Allow arbitrary season directory names","False"),
                    ("occurrences", "folder", "Path to file holding common occurrences (/path/to/file.txt)","/path_to_file.txt"),
                    ("detection", "bool","TV-Show title recognition and folder creation for incoming episodes","False"),
                    ("startup", "bool","On startup search in download folder for files to process", "False"),
                    ("rename", "bool", "Automatically rename episodes", "False"),
                    ("usr_string", "str", "Define your own naming convention for renaming", "%show - %1index.%episodeANYTHING%720p|1080p%"),
                    ("episode_language", """English;German;Danish;Finnish;Dutch;Italian;Spanish;French;Polish;
                    Hungarian;Greek;Turkish;Russian;Hebrew;Japanese;Portugese;Chinese;Czech;
                    Slovene;Croatian;Korean;Swedish;Norwegian""","Choose a language for episode names","English"),
                    ("folder_search", "bool", "On matching failure use enclosing folder to match episode", "False"),
                    ("ignore_sample", "bool","Ignore sample files", "False"),
                    ('move_log', 'folder', 'Specify a directory to log EM operations to. (Disabled if empty)', ''),
                    ("leading_zero", "bool", "Show leading zero for season numbers smaller 10", "False"),
                    ("char_sub", "str", "Characters to substitute w/o any sanity checks (Syntax: a|b,c|b,d|,)", ""),
                    ("folder_sub", "bool", "Substitute characters in folders as well?", "False"),
                    ("junk_rm", "bool", "Automatic deletion of empty directories and files with certain (user-specified) extensions", "False"),
                    ("junk_exts", "list", "Files with these extensions will be automatically deleted if automatic deletion is enabled", "txt,nfo,sfv,sub,idx,bmp,jpg,png"),
                    ("blacklist", "path", "/path/to/blacklist.txt (or relative to pyload config folder)", ""),
                    ("bl_switch", "bool", "Blacklisting", "False"),]
    __author_name__ = ("rusk")
    __author_mail__ = ("troggs@gmx.net")
    __tvdb = {}
    __mv_queue = Queue(1) #we only want one moving operation at a time but a thread for every file that needs moving
    __tvdb_update_lock = RLock() # really just a precaution 
    __tvdb_queue_ = Queue(1) # really just a precaution.
    __mv_lock = RLock()
    __em_lock = RLock()
    event_map = {"unrarFinished":"unrarFinished",
                 "pluginConfigChanged":"updateConfig",}
    
       
    def setup(self):
        self.number_of_parallel_queries = 10
        self.language = self.getConfig("episode_language")
        self.pattern_compiler = PatternCompiler() # local scope possibly enough
        self.pattern_checker = PatternChecker(self.pattern_compiler)
        self.renamer = Renamer(self.pattern_compiler)
        


    def updateConfig(self,plugin_name,option_name,value):
        ConfigDumper(self).dump()
        if(option_name == "tvshows"):
            if not(self.getConfig("tvshows") == value):
                self.start_populateTVDb()
                if not self.__tvdb_queue_.get():
                    return
                else:
                    self.__tvdb_queue_.task_done()
  
    
    def start_populateTVDb(self):
        tgt = self.populateTVDb
        Thread(target=tgt).start()
    
   
    def populateTVDb(self):
        self.__tvdb_update_lock.acquire(1)
        self.logDebug("(Re)-Populating local tv database if necessary. Locked meanwhile...")
        if(self.getConfig("tvshows") == ""):
            self.logWarning("Path to local tv shows is not set. Please check plugin Config. Aborting...")
            self.__tvdb_queue_.put(False)
            self.__tvdb_update_lock.release()
            return False
        else:
            ldr = PathLoader()
            self.__tvdb = ldr.loadFolders(self.getConfig("tvshows"))
            if (self.__tvdb == {}): # only returns empty if target dir either on its own is empty or not existing
                self.logWarning("No shows found. Please check correct path in plugin config. Aborting...")
                self.__tvdb_queue_.put(False)
                self.__tvdb_update_lock.release()
                return False
        for show in self.__tvdb.keys():
            self.logDebug("Local show: %s | Path to show: %s" % (show, self.__tvdb[show]))
        self.__tvdb_queue_.put(True)
        self.__tvdb_update_lock.release()
        self.logDebug("Lock for population process of tv database released.")
        return True    
    
    
    def coreReady(self):
        #ConfigDumper(self).dump()
        #pydevd.settrace("192.168.1.46",stdoutToServer=True,stderrToServer=True)
        #ConfigDumper(self).load('/root/.pyload/Logs/em_debug.conf')
        self.mv_logger = \
        MoveLogger(self.getConfig('move_log') +\
                   'moving_log.txt')
        if self.getConfig('startup'):
            self.doInitialSearch()
    
    def doInitialSearch(self):
            extract_path = self.config.plugin["ExtractArchive"]["destination"]["value"]
            dl_path = self.config["general"]["download_folder"]
            self.logDebug('Initial search on startup activated. Proceeding...')
            
            if self.config.plugin["ExtractArchive"]["activated"]["value"] is False or \
             len(self.config.plugin["ExtractArchive"]["destination"]["value"]) == 0:
                self.acq_rls_ProcessingLock(dl_path)
            elif dl_path.find(extract_path) != -1:
                self.acq_rls_ProcessingLock(extract_path)
            elif extract_path.find(dl_path) != -1:
                self.acq_rls_ProcessingLock(dl_path)
            else:
                self.acq_rls_ProcessingLock(extract_path)
                self.acq_rls_ProcessingLock(dl_path)
    
    
    # event dispatched on completion of single file   
    def downloadFinished(self, pyfile):
        isArchive = self.pattern_checker
        for ext in ['rar', 'zip']:
            if isArchive.hasExtension(pyfile.name, ext):
                self.logDebug(u"%s is an archive. Aborting..." % pyfile.name)
                return
            
        p = pyfile.package()
        path_to_file = os.path.join(self.config["general"]["download_folder"], p.folder, pyfile.name)
        self.acq_rls_ProcessingLock(path_to_file) 
     
        
    def unrarFinished(self,path_to_extracted_files,path_to_downloads):
        self.acq_rls_ProcessingLock(path_to_extracted_files)
   
    
    def acq_rls_ProcessingLock(self, path):
        self.__em_lock.acquire()
        self.logDebug("acq_rls_ProcessingLock(): __em_lock acquired")
        try:
            self.doProcessing(path)
        except BaseException, e:
            self.logDebug_()
            raise
        except Exception, ee:
            self.logDebug_()
            raise
        self.__em_lock.release()
        self.logDebug("acq_rls_ProcessingLock(): __em_lock released")

     
    #path_to_file_s marks the root folder of an extracted archive, a finished package
    #or a single file
    def doProcessing(self, path_to_file_s):
        ''' Process either a file or a number of files within the given path.

        This includes checking each file and finally discarding of or moving it to its final resting place.
        May it rest in peace.
        '''
        
        #populate local tv db if needed and halt main thread meanwhile
        self.start_populateTVDb()
        if not self.__tvdb_queue_.get():
            return
        else:
            self.__tvdb_queue_.task_done()
            
#        crntShows = {}  #add found tv episodes: {ep_file_name:(path_to_show, show_title, show_index)} 

        crntShows = []
        
        
        # collect files from extract/download location
        files_ = self.collectFiles(path_to_file_s)
        if files_ == {}:
            if os.path.isdir(path_to_file_s):
                self.logInfo(u'Nothing to process in "%s". Aborting...' % path_to_file_s)
            else:
                self.logInfo(u'"%s" is not for me to handle. Aborting...' % path_to_file_s)
            return
        
        
        # check if any of the collected files are blacklisted
        if self.getConfig("bl_switch") is True:
            for file_ in files_.keys():
                if self.__isBlacklisted(files_[file_]) is True:
                    files_.pop(file_)
                    self.logDebug(u'The path of the file "%s" is blacklisted and it will not be proccessed.' % file_)
        

        #Check for sample files is enabled
        if self.getConfig("ignore_sample") is True:
            self.logDebug('Ignoring samples is activated. Checking...')
            for file_ in files_.keys():
                if self.__isSample(file_) is True:
                    files_.pop(file_)
                    self.logDebug(u'"%s" is a sample file and will not be processed.' % file_)

        
        #Check if and what files are video files and remove bad apples
        for file_ in files_.keys():
            if not(self.isVideoFile(file_)):
                files_.pop(file_)
        if (files_ == {}):
            self.logInfo(u'No video files to process in "%s". Aborting...' % path_to_file_s)
            return
        
            
        #Check if and what files are tv shows and remove bad apples
        for vid in files_.keys():
            if not self.isTVEp(vid, files_[vid]):
                files_.pop(vid)
            else:
                src = files_[vid]
                crntShows.append(Episode(src=src, src_filename=vid))
        if len(crntShows) == 0:
            self.logInfo(u'No tv episodes to process in "%s". Aborting...' % path_to_file_s)
            return
        
        
        #Check if and what files are episodes of shows existing in the local database of shows
        #(and remove bad apples/add to db and file system)
        crnt_shows = crntShows[:] # prevents a f'd up iteration
        for episode in crntShows:
            if not(self.isinDb(episode, self.getConfig("detection"))) is True:
                crnt_shows.remove(episode)
        if len(crnt_shows) == 0:
            self.logInfo(u'All found tv episodes in "%s" are not part of local tv shows. Aborting...' % path_to_file_s)
            return
        
        crntShows = crnt_shows[:]
        
        #Check if season folder of that particular show exists locally or remove bad apples 
        for episode in crntShows:
            if not self.hasSeasonDir(episode, self.getConfig("create_season"), self.getConfig("arbitrary")):
                crnt_shows.remove(episode)
        if len(crnt_shows) == 0:
            self.logInfo(u'No existing seasons found for episodes in "%s". Aborting...' % path_to_file_s)
            return
        
        crntShows = crnt_shows[:]
        
                
        #<--- The remainder of files_ is now ready to be moved to its final destination ---> 
        
        #<-- missing information for successful moving op -->
        # { full_path_to_episode : path_to_season_of_show } basically { src : dst }
        #<-- to cater to this need crntShows altered using a callback during season check (last loop) -->
        
        # create,many producer and consumer threads,there are files to be moved
        # since our Queue is of size = 1 we don't want any blocking to happen on self.__mv_queue.add(episode)
        # possibly dangerous for extreme cases where loads of files need to be moved
        for episode in crntShows:
            addToQueue = Thread(target=self.add_queueMoving, args=(episode,))
            addToQueue.setDaemon(True)
            addToQueue.start()
            getFromQueue = Thread(target=self.get_queueMoving)
            getFromQueue.setDaemon(True)
            getFromQueue.start()
        
        self.__mv_queue.join()
        self.logDebug("doProcessing(): __mv_queue joined")
        return
    
        
    def collectFiles(self,single_path_to_files):
        '''collects all extracted/downloaded files
        
        The search is recursive and starts atop the location either the archive was extracted to
        or the package/file was downloaded to 
        '''
        collect = PathLoader()
        files_ = collect.loadFiles(single_path_to_files)
        return files_
    
    
    def isVideoFile(self,file_name):
        '''checks a file extension against a set of user-defined extensions
        
        Check if file is valid (supported) video container .
        '''
        valdor = self.pattern_checker
        extensions = string.split(self.getConf("extensions"), ',')
        for ext in extensions: 
            if (valdor.hasExtension(file_name, ext)):
                return True
        self.logDebug(u'File extension in file "%s" is unrecognised' % file_name) #TODO: let the user choose what to do (ignore,delete or move anyway)
        return False
    
    
    def isTVEp(self,video_name, src_path):
        '''checks if a file is a tv show episode'''
        valdor = self.pattern_checker
        if(valdor.isTVEpisode(video_name)):
            self.logDebug(u'File "%s" is a tv episode' % video_name)
            return True
        else:
            if self.getConfig("folder_search") and (valdor.isTVEpisode(src_path)):
                self.logDebug(u'Folder "%s" is a tv episode' % src_path)
                return True
            else:
                self.logDebug(u'File "%s" in Folder "%s" is not a tv episode' % (video_name,src_path))
                self.mv_logger.log_custom(u'File "%s" in Folder "%s" is not a tv episode' % (video_name,src_path))
                return False
    
        
    def isinDb(self, episode_obj, createShow=False):    
        '''checks downloaded/extracted show against local database of tv shows
        
        Returns True on a match and False if no match was produced
        '''
        episode = episode_obj
        valdor = self.pattern_checker
        #crntShows = {}  #add found tv episodes: {ep_file_name:(path_to_show, show_title, show_index)}  <- obsolete structure; adapt it!
        filename=self.renamer.substitute_chars(episode.src_filename, self.getConfig("char_sub"))
        if self.getConfig("folder_sub"):
            foldername=self.renamer.substitute_chars(episode.root_folder, self.getConfig("char_sub"))
        else:
            foldername=episode.root_folder
        if self.getConfig("folder_search"):
            self.logInfo(u'Searching local Database for "%s". On matching Failure Searching for "%s".' %(filename,foldername))
        else:
            self.logInfo(u'Searching local Database for "%s".' %filename)
        for e in self.__tvdb.keys(): # where e is an actual name of locally existing show
            if (valdor.hasPattern(filename, valdor.createPattern(e)) is not None) or \
            (self.getConfig("folder_search") and valdor.hasPattern(foldername, valdor.createPattern(e)) is not None): # if True we got a local match
                episode.dst = os.path.join(self.__tvdb.get(e), e) 
                episode.show_name = e # e is the (folder) name of the (locally existing) show 
                self.logDebug(u'"%s" recognised as show "%s"' % (episode.src_filename, e))
                if self.getConfig("rename") is True:
                    self.logInfo(u'Querying remote resource for episode name for "%s". Please exercise patience meanwhile...' % episode.src_filename)
                    episode_names = self.__getEpisodeNamesFromRemoteDB(e)
                    if episode_names != None: # if None no episode names were found remotely
                        episode.episode_names = episode_names
                        return True
                    else:
                        if self.getConfig("folder_search") is True: # Just for announcing that no episode names were found
                            self.logInfo(u'No match in database for neither "%s" nor "%s". \
                            Applying episode name will not be available.' % (episode.src_filename, episode.src))
                        else: # Just for announcing that no episode names were found
                            self.logInfo(u'No match in database for "%s". \
                            Applying episode name will not be available.' % (episode.src_filename))
                        return True # return True since the show itself was successfully matched
                else:
                    return True
        if(createShow):
            return self.__createShow(episode)
    

    def __createShow(self, episode):
        if self.__getShowNameFromRemoteDB(episode) is not None: #actual name of tv show
            if os.path.exists(self.getConfig("tvshows")): # just a precaution - we don't want to leave a trail of folders across the filesystem
                if self.getConfig("folder_sub") is True:
                    episode.show_name = self.renamer.substitute_chars(episode.show_name, self.getConfig("char_sub"))
                show_name = episode.show_name
                if episode.episode_names == {}:
                    self.logInfo(u'No episode name for "%s" found. Applying those during renaming will not be available' % show_name)
                episode.dst = os.path.join(self.getConfig("tvshows"), show_name)
                try:
                    os.mkdir(episode.dst) #race condition 
                    self.logInfo(u'Conclusive result on show name determination: "%s" recognised as show "%s".' % (episode.src_filename, show_name))
                    self.logInfo(u'Added "%s" to local tv database and created folder "%s".' % (show_name, episode.dst))
                    return True
                except OSError, ose:
                    if ose.errno == 17:
                        self.logDebug(u'Folder "%s" already exists. Moving on...' % episode.dst)
                        return True
        else:
            self.logInfo(u'No conclusive result on show name determination for "%s". Skipping...' % (episode.src_filename))
            self.mv_logger.log_custom(u'No conclusive result on show name determination for "%s". Skipping...' % (episode.src_filename))
            return False
        self.logDebug(u'The show "%s" is not part of the local database' % (episode.src_filename))
        self.mv_logger.log_custom(u'The show "%s" is not part of the local database' % (episode.src_filename))
        return False

                
    def __getShowNameFromRemoteDB(self, episode):
        full_query_string = episode.full_query_string
        minimal_query_string = self.pattern_checker.getMinimalQueryString(episode.full_query_string) # cut off file name at series index
        
        root_folder = episode.root_folder
        root_folder_search_enabled = False 
        if self.getConfig("folder_search") is True and \
        os.path.split(self.config.plugin["ExtractArchive"]["destination"]["value"])[1] != root_folder and \
        os.path.split(self.config["general"]["download_folder"]) != root_folder:
            root_folder_search_enabled = True 
        
        # in case PatternChecker() produces no workable result skip querying w/ minimal string 
        # e.g. Anger Mangangement: "poe-ams01e02.avi" -> NONE: poe gets cut off as common occurrence, ams gets cut off by getMinimalQueryString()
        # TODO: disable application of common occurrence removal for querying w/ minimal string (?)
        if minimal_query_string != None:
            minimal_query_string = [StringCleaner().clean(minimal_query_string, isFile=False),] # clean punctuation and convert to list
            query_handler = QueryHandler(self.number_of_parallel_queries, self.pattern_compiler, self.language)
            query_result = query_handler.processQueries(minimal_query_string)
            if query_result != None:
                episode.show_name = query_result["name"]
                episode.episode_names = query_result["episode_names"]
                self.logDebug(u'Show name minimal query successful for "%s". Proceeding...' % episode.src_filename)
                return episode
            else:
                self.logDebug(u'Show name determination with minimal query string for "%s" failed.' \
                              ' Trying full query string next.' % episode.src_filename)
                # lets try again using the full file name
        
        # query using the full file name / full query string
        query = Query(self.getConfig("occurrences"),
                          self.number_of_parallel_queries,
                          self.pattern_compiler,
                          self.language)            
        query_result = query.sendQuery(full_query_string)
        if query_result != None:
            episode.show_name = query_result["name"]
            episode.episode_names = query_result["episode_names"]
            self.logDebug(u'Show name full query successful for "%s". Proceeding...' % episode.src_filename)
            return episode
        else:
            self.logDebug(u'Show name determination with full query string for "%s" failed.' \
                          ' Trying next with root_folder search if enabled.' % episode.src_filename)
        # lets try again with the root_folder if that option is enabled
        
        # query using the root/parent folder where episode.src_filename resides in
        if not root_folder_search_enabled:
            self.logDebug(u'Skipping root_folder ("%s") search for "%s" since that option is disabled.' \
                          % (root_folder, episode.src_filename))
            return None
        else:
            query_result = query.sendQuery(root_folder,isFile=False)
            if query_result != None:
                episode.show_name = query_result["name"]
                episode.episode_names = query_result["episode_names"]
                self.logDebug(u'Show name query successful for "%s" using its enclosing directory ("%s"). Proceeding...' \
                             % (episode.src_filename, root_folder))
                return episode
            else:
                self.logDebug(u'Show name determination on "%s" with its parent directory "%s" failed.' \
                              % (episode.src_filename, root_folder))
                return None
    
    
    def __getEpisodeNamesFromRemoteDB(self, show_name):
        query_handler = QueryHandler(self.number_of_parallel_queries, self.pattern_compiler, self.language)
        query_result = query_handler.processQueries([show_name,])
        if query_result != None:
            query_result = query_result["episode_names"]
            self.logDebug(u'Episode query successful on "%s". Proceeding...' % show_name)
            return query_result
        else:
            self.logDebug(u'Episode query on "%s" failed.' % show_name)
            return None
        
    
    def hasSeasonDir(self, episode_obj, createSeason=False, arbitrarySeason=True):
        #crntShows = {}  #add found tv episodes: {ep_file_name:(path_to_show, show_title, show_index)}  <- obsolete structure; adapt it!
        episode = episode_obj
        valdor = self.pattern_checker
        episode_name_for_show_index=episode.src_filename
        if self.getConfig("folder_search") and \
        valdor.hasPattern(episode.src_filename, valdor.createPattern(episode.show_name)) is None and \
        valdor.hasPattern(episode.root_folder, valdor.createPattern(episode.show_name)) is not None:
            episode_name_for_show_index=episode.root_folder
        season = valdor.getSeason(episode_name_for_show_index,
                                  self.getConfig("season_text"),
                                  self.getConfig("leading_zero")) # returns "Season 1" e.g.
        if season == None:
            self.logDebug(u'No valid show index could be extracted from "%s". Skipping...' % episode_name_for_show_index)
            return False
        season_path = os.path.join(episode.dst, season)
        show_index = valdor.getShowIndex(episode_name_for_show_index)
        episode.show_index["raw"] = show_index
        # TODO: no clue what I am doing here; looks like legacy -> overhaul!
        episode.show_index["season"], episode.show_index["episode"] = \
        self.renamer.convert_show_index(show_index, 1, returnRaw=True)
        if (os.path.exists(season_path)):
            episode.dst = season_path
            self.logDebug(u'Season directory for show "%s" already exists. No creation necessary.' % episode_name_for_show_index)
            return True
        elif arbitrarySeason is True:
            arbSeason = self.getArbSeasonPath(episode.dst, episode_name_for_show_index)
            if arbSeason is not None:
                season_path = os.path.join(episode.dst, arbSeason)
                episode.dst = season_path
                self.logDebug(u'Custom season directory (%s) for show "%s" already exists. No creation necessary.' % (episode.show_name, arbSeason))
                return True
        if createSeason is True and os.path.exists(season_path) is not True:
            os.mkdir(season_path)
            episode.dst = season_path
            self.logInfo(u'Season directory for show "%s" does not exist. Directory "%s" is being created' % (episode_name_for_show_index,season))
            return True
        elif createSeason is False and os.path.exists(season_path) is False:
            self.logDebug(u'Season directory for show "%s" does not exist. Directory "%s" is not being created' % (episode.show_name,season))
            return False
    
    
    def getArbSeasonPath(self,path_to_show, episode_name):
        directories = PathLoader().loadFolders(path_to_show)
        vldr = self.pattern_checker
        
        for dir_ in directories:
            if dir_ == vldr.checkArbitrarySeason(self.getConfig("season_text"),
                                                 vldr.getSeason(episode_name,
                                                                "",
                                                                self.getConfig("leading_zero")),
                                                 dir_):
                return dir_
        self.logDebug("No season folder amended by an arbitrary string was found")
        return None
    
    def __isEmptyDir(self,folder):
        '''checks if folder is empty so it can be deleted'''
        if not os.listdir(folder):
            return True
        return False
    
    def __isJunk(self, file_name):
        '''checks if file is a Junk File so it can be deleted'''
        valdor = self.pattern_checker
        jextensions = self.getConfig("junk_exts")
        extensions = string.split(jextensions, ',')
        for ext in extensions: 
            if (valdor.hasExtension(file_name, ext)):
                return True
        return False
    
    def __isSample(self, file_name):
        match_ = re.search(
                           "((^)|(\\.+)|(-+)|(_+)|(\\s+))(sample)(($)|(\\.+)|(-+)|(\\s+)|(_+))", \
                           file_name, \
                           re.IGNORECASE
                          )
        return True if match_ else False
    
    def __isBlacklisted(self, path_to_file):
        """checks if a file should not be processed based on part of its path"""
        
        blacklist_file_name = "blacklist.txt"
        path_to_blacklist = self.getConfig("blacklist")
        blacklist_file = os.path.join(path_to_blacklist, blacklist_file_name)
        if not os.path.exists(blacklist_file):
            return False
        
        blacklist = []
        for line in open(blacklist_file):
            blacklist.append(line.replace("\n", ""))
        
        extract_path = self.config.plugin["ExtractArchive"]["destination"]["value"]
        dl_path = self.config["general"]["download_folder"]
        if path_to_file.find(extract_path) != -1: 
            new_path = path_to_file[len(extract_path):] 
            testees = new_path.split(os.sep)
            while testees.count("") != 0:
                testees.remove("")    
            for entry in blacklist:
                for testee in testees:
                    if entry.lower() == testee.lower():
                        return True # file is blacklisted
        
            
        elif path_to_file.find(dl_path) != -1:
            new_path = path_to_file[len(dl_path):]
            testees = new_path.split(os.sep)
            while testees.count("") != 0:
                testees.remove("")    
            for entry in blacklist:
                for testee in testees:
                    if entry.lower() == testee.lower():
                        return True # file is blacklisted
    
    
    def add_queueMoving(self,episode_obj):
        ep = episode_obj
        if self.__mv_queue.full():
            self.logInfo(u'Queue full. Adding "%s"as soon as a slot is freed up.' % (ep.src_filename))
        self.__mv_queue.put(episode_obj)


    def get_queueMoving(self):
        ep_obj = self.__mv_queue.get() # get item from queue
        episode = ep_obj
        if episode.dst.find(self.getConfig('tvshows')) == -1:
            self.logDebug("Episode %s does not have destination. Skipping..." % episode.src_filename)
            self.__mv_queue.task_done()
            return
        self.__mv_lock.acquire(1)
        if os.path.exists(os.path.join(episode.src, episode.src_filename)) is False:
            self.logInfo(u'"%s" does not exist. Maybe was moved already? Aborting moving operation.' % os.path.join(episode.src, episode.src_filename))
            self.__mv_lock.release()
            self.__mv_queue.task_done()
            return
        if self.getConfig('rename'):
            episode.unicode()
            episode.dst_filename = self.renamer.rename(episode, self.getConfig('usr_string'), self.getConfig('char_sub'))
            episode.dst_filename = save_path(episode.dst_filename)
        try:
            episode.unicode()
            utf = Transcoder().encode_utf8
            utfd = Transcoder().decode_utf8
            if len(episode.dst_filename) == 0:
                episode.dst_filename = save_path(episode.src_filename)
            if os.path.exists(os.path.join(utf(episode.src), utf(episode.src_filename))):
                if os.path.exists(episode.dst) and not os.path.exists(os.path.join(utf(episode.dst), utf(episode.dst_filename))):
                    self.logInfo(u'Starting to move "%s" to "%s"' % (episode.src_filename, utfd((os.path.join(utf(episode.dst), utf(episode.dst_filename))))))
                    mv.move(os.path.join(utf(episode.src), utf(episode.src_filename)), os.path.join(utf(episode.dst), utf(episode.dst_filename)))
                    self.setPermissions(os.path.join(utf(episode.dst), utf(episode.dst_filename)))
                    self.logInfo(u'Moving of "%s" completed.' % episode.dst_filename)
                    self.mv_logger.log_mv(utf(episode.src_filename), os.path.join(utf(episode.dst), utf(episode.dst_filename)))
                    if self.getConfig("junk_rm"):
                        self.cleanFolder(episode.src)
                elif os.path.exists(os.path.join(utf(episode.dst), utf(episode.dst_filename))):
                    if self.getConfig('overwrite'):
                        self.logInfo(u'Starting to move "%s" to "%s" overwriting the destination' \
                                     % (episode.src_filename, utfd(os.path.join(utf(episode.dst), utf(episode.dst_filename)))))
                        mv.copy(os.path.join(utf(episode.src), utf(episode.src_filename)), os.path.join(utf(episode.dst), utf(episode.dst_filename)))
                        os.remove(os.path.join(utf(episode.src), utf(episode.src_filename)))
                        self.setPermissions(os.path.join(utf(episode.dst), utf(episode.dst_filename)))
                        self.logInfo(u'Moving of "%s" completed.' % episode.dst_filename)
                        self.mv_logger.log_mv(utf(episode.src_filename), os.path.join(utf(episode.dst), utf(episode.dst_filename)))
                    else:
                        self.logInfo(u'"%s" already exists. Skipping file...' % utfd(os.path.join(utf(episode.dst),utf(episode.dst_filename))))
                else:
                    if episode.dst != None and episode.dst_filename != None:
                        self.logInfo(u'Conditions to move file "%s" to "%s" not met. Skipping file...' % utf(episode.dst),utf(episode.dst_filename))
                    elif episode.dst_filename == None:
                        self.logInfo(u'Destination filename for file "%s" is unknown. SKipping file...' % utf(episode.src_filename))
                    elif episode.dst == None:
                        self.logInfo(u'No destination for file %s specified. Skipping file...' % utf(episode.src_filename))
            else:
                self.logInfo(u'"%s" does not exist. Aborting moving operation.' % utfd(os.path.join(utf(episode.src), utf(episode.src_filename)))) # in case another thread moved our file
        except OSError,ose:
            if ose.errno == 2:
                self.logInfo(u'"%s" does not exists and was probably already moved. Aborting...' % utfd(os.path.join(utf(episode.src), utf(episode.src_filename))))
        self.__mv_lock.release()
        self.__mv_queue.task_done() # announce completion
    
    
        
    def setPermissions(self, files): # sorry whoever wrote ExtractArchive but I had to steal this one... ;) (import was not feasible) 
        for f in files:
            if not os.path.exists(f): continue
            try:
                if self.core.config["permission"]["change_file"]:
                    if os.path.isfile(f):
                        os.path.chmod(f, int(self.core.config["permission"]["file"], 8))
                    elif os.path.isdir(f):
                        os.path.chmod(f, int(self.core.config["permission"]["folder"], 8))

                if self.core.config["permission"]["change_dl"] and os.name != "nt":
                    uid = os.path.getpwnam(self.config["permission"]["user"])[2]
                    gid = os.path.getgrnam(self.config["permission"]["group"])[2]
                    os.path.chown(f, uid, gid)
            except Exception, e:
                self.log.warning(_("Setting User and Group failed"), e)

    def logDebug_(self):
        for line in traceback.format_exc().split('\n'):
            self.logDebug(line)
                
    def cleanFolder(self,folder):
        '''Cleans a given folder from junk files and delete it if empty.
        
        cleanFolder checks every file if it has a file extension that marks it as junk file (List provided in config) and deletes it if so. 
        Removes empty folders (i.e. empty sample folders).
        If given folder is empty after cleaning and moving, it deletes the folder.
        Prints removed files and directories in debug and info.
        '''    
        # TODO: "Force Delete" Option ?
        filelist = []
        for f in os.listdir(folder):
            file_ = os.path.join(folder,f)
            if os.path.isfile(file_):
                if self.__isJunk(file_) or self.__isSample(file_):
                    if os.path.exists(file_):
                        os.remove(file_)
                        filelist.append(f)
            elif os.path.isdir(file_):
                self.cleanFolder(file_)
        if len(filelist) > 0:
            self.logDebug(u'Deleted Junkfiles: %s' % filelist)
            self.logInfo(u'%s Junk File(s) deleted' % len(filelist)) 
        if self.__isEmptyDir(folder):
            if os.path.exists(folder) and not self.config["general"]["download_folder"] == folder:
                os.rmdir(folder)
                self.logInfo(u'Dir %s deleted' % folder)

class Episode:
    
    def __init__(self, src="", src_filename="", dst="", dst_filename="",
                 show_name="", show_index="", episode_names={}):
        self.src = src # source folder of episode
        self.src_filename = src_filename # name of episode in src folder
        self.root_folder = os.path.basename(os.path.abspath(self.src))
        self.dst = dst # dst folder for episode
        self.dst_filename = dst_filename # dst filename for episode
        self.show_name = show_name
        self.show_index = {} # (1,10) -> (SEASON_NUM, EPISODE_NUM)
        self.show_index["season"] = None
        self.show_index["episode"] = None
        self.show_index["raw"] = None
        self.episode_names = episode_names # dict of all episode names: ep_name = self.episodes["episode_names"][1][10]
        self.full_query_string = self.src_filename
        self.minimal_query_string = "" # file name cut at series index: "A.Series.S01E01.blabla.mkv" -> "A.Series"
        
        
    def episode_name(self, decode=False):
        if  self.show_index["season"] is not None and \
            self.show_index["episode"] is not None and \
            self.episode_names is not None and \
            len(self.episode_names) > 0:
            season = str(self.show_index["season"])
            episode = str(self.show_index["episode"])
            if self.episode_names.has_key(season):
                if self.episode_names[season].has_key(episode):
                    ep_name = self.episode_names[season][episode]
                    if not decode:
                        return ep_name
                    return Transcoder().decode(ep_name)
        return None
    
    def get_show_index(self):
        return self.show_index["raw"]

        
    def unicode(self):
        t = Transcoder()
        if isinstance(self.src, str):
            self.src = t.decode(self.src)
        if isinstance(self.src_filename, str):
            self.src_filename = t.decode(self.src_filename)
        if isinstance(self.dst, str):
            self.dst = t.decode(self.dst)
        if isinstance(self.dst_filename, str):
            self.dst_filename = t.decode(self.dst_filename)
        if isinstance(self.show_name, str):
            self.show_name = t.decode(self.show_name)
        

import os
class PathLoader:
    ''' This class implements methods for recursively searching a specific path filtering out files with their absolut path'''
    
    
    def loadFiles(self,path_to_files, returnDict=True):
        '''Flat search for files which incurs self.deepLoadFiles(...) if needed

        self.loadFiles on its own only checks the root directory on which it was called
        for files and if necessary calls a recursive search via self.deepLoadFiles(...)
        If returnDict=True a dictionary is returned otherwise a list of tuples
        '''
        try:
            path_to_files = str(path_to_files)
            self.__files = []
            if(os.path.exists(path_to_files)):
                for dir_name in os.listdir(path_to_files):
                    if os.path.isdir(os.path.join(path_to_files, dir_name)):
                        self.deepLoadFiles(dir_name,path_to_files)
                    else:
                        self.__files.append((Transcoder().decode(dir_name), os.path.join(Transcoder().decode(path_to_files))))
            if(returnDict):
                return self.__convertTplLstToDict(self.__files)
            else:
                return self.__files
        except OSError, e:
            if e.errno == 20: # not a directory
                bn, file_ = os.path.split(path_to_files)
                return { file_ : bn}
        else:
            return {}


    def deepLoadFiles(self,sub_dir_path,base_name):
        '''Recursively searches for files 

        Calling of this function should be left to self.loadFiles()
        which will be calling it in an event of necessity
        '''
        sub_dir_path = os.path.join(base_name, sub_dir_path)
        for dir_name in os.listdir(sub_dir_path):
            if (os.path.isdir(os.path.join(sub_dir_path,dir_name))):
                self.deepLoadFiles(dir_name,sub_dir_path)
            else:
                # at this point dir_name equals to a filename 
                self.__files.append((Transcoder().decode(dir_name), os.path.join(Transcoder().decode(sub_dir_path))))


    def loadFolders(self, dir_path_to_search):
        '''Flat (non-recursive) search for folders within a specified directory.'''
        paths_ = {}
        paths = []
        shows = []
        if os.path.exists(dir_path_to_search):
            for dname in os.listdir(dir_path_to_search):
                if (os.path.isdir(os.path.join(dir_path_to_search, dname))):
                    #paths = dict(zip(dname,dir_path_to_search))
                    paths.append(dir_path_to_search)
                    shows.append(dname)
                paths_ = dict(zip(shows,paths))

        return paths_
    
    
    def __convertTplLstToDict(self,list_of_tpls):
        files_ = []
        paths_ = []
        for e in list_of_tpls:
                file_,path_ = e
                files_.append(file_)
                paths_.append(path_)
                
        _dict = dict(zip(files_,paths_))
        return _dict
    


class PatternCompiler:
    ''' All static patterns used for various tasks throughout this module are part of this class.
    
    To add new static patterns follow this guideline:
    I)   Create the neccessary config strings within the constructor for accessing the self.compiled_pattern dict 
         by staying closely to the name of the class' method that uses that pattern. If there are multiple patterns per method 
         define as many variables as there are independent patterns and assign them the typeN variables within the constructor. 
         If you run out of types simply create more type variables with a local scope
    II)  Create a method prefixed with self.compile_prefix: def compile_somePattern(self): ...
    III) Create a method that has the same name as the method that retrieves the compiled pattern and 
         use it to return the compiled pattern. If there are multiple patterns pass a variable defining the type 
         def somePattern(self, some_pattern_type=typeN): ...
         
    All methods containing the prefix "compile_" will be called at instantiation of PatternCompiler
    '''
    
    
    def __init__(self):
        # config strings
        
        self.compile_prefix = "compile_"
        
        type1 = "type1"
        type2 = "type2"
        type3 = "type3"
        type4 = "type4"

        self.is_tv_episode = "isTVEpisode"
        
        self.get_season = "getSeason"
        self.getSeason_type1 = type1
        self.getSeason_type2 = type2
        self.getSeason_type3 = type3
        self.getSeason_type4 = type4
        
        self.get_show_index = "getShowIndex"
        self.getShowIndex_type1 = type1
        self.getShowIndex_type2 = type2
        self.getShowIndex_type3 = type3
        self.getShowIndex_type4 = type4
        
        self.get_minimal_query_string = "getMinimalQueryString"
        self.getMinimalQueryString_type1 = type1
        self.getMinimalQueryString_type2 = type2
        self.getMinimalQueryString_type3 = type3
        
        self.get_series = "__getSeries"
        self.get_series_seriesid = type1
        self.get_series_seriesname = type2
        
        self.analyse_response = "__analyzeResponse"
        
        self.get_episodes = "__getEpisodes"
        self.get_episodes_seasonnumber = type1
        self.get_episodes_episodenumber = type2
        self.get_episodes_episodename = type3
        
        self.parse_rename_string_ = "parse_rename_string"
        
        self.convert_show_index_ = "convert_show_index"
        self.convert_show_index_type1 = type1 
        self.convert_show_index_type2 = type2 
        self.convert_show_index_type3 = type3 
        
        # compiled pattern dict
        self.compiled_pattern = {}
        
        # compile all patterns and assign to pattern dict
        self.compile_all_patterns()
        
        
    def compile_all_patterns(self):
        '''Calls all methods satisfying these conditions:
        
        a) name of method starts with "compile_"
        '''
        
        # structure of return value for inspect.getmembers:
        #     result_list = [('meth_name_1', instance_method_object_1),('meth_name2', instance_method_object_2), ...]
        for tpl in inspect.getmembers(self, self.compiles):
            for element in tpl:
                if inspect.ismethod(element) and element != self.compile_all_patterns:
                    compiler_method = element
                    compiler_method() # call it right on the spot

        
    def compiles(self, a_method):
        if not inspect.ismethod(a_method): return False
        return a_method.__name__.find(self.compile_prefix) == 0 and True or False
    
    
    def compile_isTVEpisode(self):
        pattern1 = '(s\d{2}e\d{2})' # S01E01 e.g.
        pattern2 = '(\d{1,2}x\d{1,2})' # 1x1, 10x10, 1x10, 10x1 e.g.
        pattern3 = '((\\s+)|(-+)|(_+)|(\\.+))(\d{3})((\\s+)|(-+)|(_+)|(\\.+))' # ".101-", "_901 " with ESS

        self.compiled_pattern[self.is_tv_episode] = \
        re.compile(pattern1 + '|' + pattern2 + '|' + pattern3, re.IGNORECASE|re.DOTALL)
    
    def compile_getSeason(self):
        p1 = '((\\s+)|(-+)|(_+)|(\\.+))(s\d{2}e\d{2})((\\s+)|(-+)|(_+)|(\\.+)|$)' # S01E01 e.g.
        p10 = '(\w{1})(s\d{2}e\d{2})((\\s+)|(-+)|(_+)|(\\.+))' # ShwnmS01E01 e.g.
        p2 = '((\\s+)|(-+)|(_+)|(\\.+))(\d{1,2}x\d{1,2})((\\s+)|(-+)|(_+)|(\\.+))' # 1x1, 10x10, 1x10, 10x1 e.g.
        p3 = '((\\s+)|(-+)|(_+)|(\\.+))([1-9][0-5][0-9])((\\s+)|(-+)|(_+)|(\\.+))' # 100 - 959
        
        result_dict = {}
        
        result_dict[self.getSeason_type1] = re.compile(p1, re.IGNORECASE)
        result_dict[self.getSeason_type2] = re.compile(p10, re.IGNORECASE)
        result_dict[self.getSeason_type3] = re.compile(p2, re.IGNORECASE)
        result_dict[self.getSeason_type4] = re.compile(p3, re.IGNORECASE)
        
        self.compiled_pattern[self.get_season] = result_dict

    
    def compile_getShowIndex(self):
        p1 = '((\\s+)|(-+)|(_+)|(\\.+))(s\d{2}e\d{2})((\\s+)|(-+)|(_+)|(\\.+)|$)' # S01E01 e.g.
        p10 = '(\w{1})(s\d{2}e\d{2})((\\s+)|(-+)|(_+)|(\\.+))' # ShwnmS01E01 e.g.
        p2 = '((\\s+)|(-+)|(_+)|(\\.+))(\d{1,2}x\d{1,2})((\\s+)|(-+)|(_+)|(\\.+))' # 1x1, 10x10, 1x10, 10x1 e.g.
        p3 = '((\\s+)|(-+)|(_+)|(\\.+))([1-9][0-5][0-9]){1}((\\s+)|(-+)|(_+)|(\\.+))' # ".101-", "_901 " with ESS
        
        result_dict = {}
        
        result_dict[self.getShowIndex_type1] = re.compile(p1, re.IGNORECASE)
        result_dict[self.getShowIndex_type2] = re.compile(p10, re.IGNORECASE)
        result_dict[self.getShowIndex_type3] = re.compile(p2, re.IGNORECASE)
        result_dict[self.getShowIndex_type4] = re.compile(p3, re.IGNORECASE)
        
        self.compiled_pattern[self.get_show_index] = result_dict
        
    def compile_getMinimalQueryString(self):
        p1 = '((\\s+)|(-+)|(_+)|(\\.+))(s\d{2}e\d{2})((\\s+)|(-+)|(_+)|(\\.+))' # S01E01 e.g.
        p2 = '((\\s+)|(-+)|(_+)|(\\.+))(\d{1,2}x\d{1,2})((\\s+)|(-+)|(_+)|(\\.+))' # 1x1, 10x10, 1x10, 10x1 e.g.
        p3 = '((\\s+)|(-+)|(_+)|(\\.+))([1-9][0-5][0-9]){1}((\\s+)|(-+)|(_+)|(\\.+))' # ".101-", "_901 " with ESS
        
        result_dict = {}
        
        result_dict[self.getMinimalQueryString_type1] = re.compile(p1, re.IGNORECASE)
        result_dict[self.getMinimalQueryString_type2] = re.compile(p2, re.IGNORECASE)
        result_dict[self.getMinimalQueryString_type3] = re.compile(p3, re.IGNORECASE)
        
        self.compiled_pattern[self.get_minimal_query_string] = result_dict
    
    
    def compile__getSeries(self):
        series_start = "(<seriesid>)"
        series_id = "([0-9]+)"
        series_end = "(</seriesid>)"
        uncompiled_sid_pattern = series_start + series_id + series_end
        
        seriesname_element_start = '(<SeriesName>)'
        seriesname = '(.{1,})'
        seriesname_element_end = '(</SeriesName>)'
        uncompiled_sn_pattern = seriesname_element_start + seriesname + seriesname_element_end
        
        result_dict = {}
        
        result_dict[self.get_series_seriesid] = re.compile(uncompiled_sid_pattern)
        result_dict[self.get_series_seriesname] = re.compile(uncompiled_sn_pattern)
        
        self.compiled_pattern[self.get_series] = result_dict
        
    
    def compile___analyzeResponse(self):
        seriesname_element_start = '(<SeriesName>)'
        content_element = '(.{1,})'
        seriesname_element_end = '(</SeriesName>)'
        uncompiled_pattern = seriesname_element_start + content_element + seriesname_element_end
        
        self.compiled_pattern[self.analyse_response] = re.compile(uncompiled_pattern)
        
    
    def compile___getEpisodes(self):
        season_number_element = "(<Combined_season>)([0-9]{1,3})(</Combined_season>)"
        episode_number_element = "(<EpisodeNumber>)([0-9]{1,3})(</EpisodeNumber>)"
        episode_name_element = "(<EpisodeName>)(.+)(</EpisodeName>)"
        
        result_dict = {}
        
        result_dict[self.get_episodes_seasonnumber] = re.compile(season_number_element)
        result_dict[self.get_episodes_episodenumber] = re.compile(episode_number_element)
        result_dict[self.get_episodes_episodename] = re.compile(episode_name_element)
        
        self.compiled_pattern[self.get_episodes] = result_dict
        
        
    def compile_parse_rename_string(self):
        uncompiled_renaming_string = \
        "(%show)|(%[123]index)|(%episode)|(%\\|?.*?%)"
        
        self.compiled_pattern[self.parse_rename_string_] = \
        re.compile(uncompiled_renaming_string) 
        
    
    def compile_convert_show_index(self):
        uncompiled_show_index_type1 = '(S\d{2}E\d{2})'
        uncompiled_show_index_type2= '(\d{1,2}x\d{1,2})'
        uncompiled_show_index_type3 = '(\d{1,4})'
        
        result_dict = {}
        
        result_dict[self.convert_show_index_type1] = \
        re.compile(uncompiled_show_index_type1, re.IGNORECASE)
        result_dict[self.convert_show_index_type2] = \
        re.compile(uncompiled_show_index_type2, re.IGNORECASE)
        result_dict[self.convert_show_index_type3] = \
        re.compile(uncompiled_show_index_type3, re.IGNORECASE)
        
        self.compiled_pattern[self.convert_show_index_] = result_dict
    
    
    def isTvEpisode(self):
        return self.compiled_pattern[self.is_tv_episode]
    
    def getSeason(self, season_type):
        return self.compiled_pattern[self.get_season][season_type]
    
    def getShowIndex(self, show_index_type):
        return self.compiled_pattern[self.get_show_index][show_index_type]
    
    def getMinimalQueryString(self, minimal_query_string_type):
        return self.compiled_pattern[self.get_minimal_query_string][minimal_query_string_type]
    
    def getSeries(self, element_type):
        if element_type == self.get_series_seriesid:
            return self.compiled_pattern[self.get_series][self.get_series_seriesid]
        elif element_type == self.get_series_seriesname:
            return self.compiled_pattern[self.get_series][self.get_series_seriesname]
        
    def analyseResponse(self):
        return self.compiled_pattern[self.analyse_response]
    
    def getEpisodes(self, element_type):
        if element_type == self.get_episodes_episodename:
            return self.compiled_pattern[self.get_episodes][self.get_episodes_episodename]
        elif element_type == self.get_episodes_episodenumber:
            return self.compiled_pattern[self.get_episodes][self.get_episodes_episodenumber]
        elif element_type == self.get_episodes_seasonnumber:
            return self.compiled_pattern[self.get_episodes][self.get_episodes_seasonnumber]
        
    def parse_rename_string(self):
        return self.compiled_pattern[self.parse_rename_string_]
    
    def convert_show_index(self, show_index_type):
        if show_index_type == self.convert_show_index_type1:
            return self.compiled_pattern\
                [self.convert_show_index_][self.convert_show_index_type1]
        elif show_index_type == self.convert_show_index_type2:
            return self.compiled_pattern\
                [self.convert_show_index_][self.convert_show_index_type2]
        elif show_index_type == self.convert_show_index_type3:
            return self.compiled_pattern\
                [self.convert_show_index_][self.convert_show_index_type3]
    

class PatternChecker:
    
    def __init__(self, pattern_compiler):
        self.pattern = pattern_compiler


    def isTVEpisode(self, string_to_check):
        '''Checks a string for being a tv episode

        Checking is done by regex on the grounds of a tv episode having
        a progression indicator in terms of its season and episode numbering
        Example: s02e11 <- 11th episode of 2nd season - its trivial I know but had to be mentioned.
        '''

        compiled_pattern = self.pattern.isTvEpisode()
        m = compiled_pattern.search(string_to_check)
        if m:
            return True
        else:
            return False

    
    def hasExtension(self, string_to_check, ext_to_check='mkv'):
        '''Checks file extension matching a given extension

        Checking is done using regex. Its possible to check for arbitrary extensions
        though in practice matching should be done for extensions of video containers
        like: mkv, avi, and so forth
        '''

        re1 = '(\\.)'
        re2 = '(' + ext_to_check + ')'
        re3 = '$'
        

        rg = re.compile(re1+re2+re3,re.IGNORECASE|re.DOTALL)
        m = rg.search(string_to_check)

        if m:
            return True
        else:
            return False

   
    def hasPattern(self, string_to_check, pattern):
        '''Checks a string against a (generated) regex pattern

        On match the match object is returned otherwise None
        
        re1='(' + existing_string + ')'    # Word 1
        '''
        re1 = pattern

        rg = re.compile(re1,re.IGNORECASE|re.DOTALL)
        result = rg.search(StringCleaner().stripclean(string_to_check))
        
        return result


    
    def createPattern(self, list_representation_of_ep_title, isString=True):
        '''Creates a case-insensitive regex pattern based on a show title

        As long as every word in the file name appears in the order its specified
        in the database of locally existing shows you are good
        Example for a title on which to compile pattern: a_list = ["Person", "of", "Interest"]
        will match
        (i)    Person.of.Interest.S01E08.720p.HDTV.x264-IMMERSE.mkv
        (ii)   person.of.something.intereSt.andsoForth
        (iii)  persOnasdwof.interest.yadiya
        ------------------------------------------------------------
        needs a revamp!
        input such as
        a_list = ["Person", "of", "Interest"]
        should only match examples like
        (i)   blablah.Person.of.Interest.blablah
        (ii)  blah Person of Interest blah
        (iii) blah_Person_of_Interest_blah
        '''

        eps = None
        if(isString): #turn whitespace separated string into list
            string_ = StringCleaner().stripclean(list_representation_of_ep_title)
            eps = string_.split(" ")
        elif not(isString): # list_representation_of_ep_title already is a list
            new_list = []
            for s in list_representation_of_ep_title:
                new_list.append(StringCleaner().stripclean(s))
            eps = new_list

        #        gap = "((\\.)|(\\s+)|(_))"
#        gap = ".*?"
        start = '((\\s)|(-)|(_)|(\\.)|(^))'
        end = '((\\s)|(-)|(_)|(\\.)|($))'
        gap = '((\\s)|(-)|(_)|(\\.))'

        pattern = ""
        
        for s in eps:
#            if (len(eps) != eps.index(s) + 1):
            if eps[len(eps) - 1] == s and len(eps) > 1: #last element of eps
                pattern += '(' + s + ')' + end
            elif len(eps) == 1: #eps has only 1 element
                pattern += start + '(' + s + ')' + end
            elif eps[0] == s: # first element of eps
                pattern += start + '(' + s + ')' + gap
            else: # anything else
                pattern += '(' + s + ')' + gap
            
        return pattern   

  
    def checkArbitrarySeason(self,season_text, season_number, directory_name_to_check):
        
        re1 = '(' + season_text + ')' + '(' + season_number + ')'
        
        rg = re.compile(re1, re.IGNORECASE|re.DOTALL)
        m = rg.search(directory_name_to_check)
        
        if m:
            return directory_name_to_check
        else:
            return ''
        
    
    def getSeason(self,string_to_check, season_text = "Season", leading_zero=False):
        '''Retrieves the season number from a show index with a leading season_text.
        
        
        Allowed input formats are specified in p1, (p10), p2 and p3.
        Returns a leading zero for numbers < 10 if leading_zero is True.
        '''
        
        p1 = self.pattern.getSeason(self.pattern.getSeason_type1)
        p2 = self.pattern.getSeason(self.pattern.getSeason_type2)
        p3 = self.pattern.getSeason(self.pattern.getSeason_type3)
        p4 = self.pattern.getSeason(self.pattern.getSeason_type4)
        
        type1 = re.search(p1, string_to_check)
        type2 = re.search(p2, string_to_check)
        type3 = re.search(p3, string_to_check)
        type4 = re.search(p4, string_to_check)
        
        punc = ['.', ' ', '-', '_']
        if type1:
            index = type1.group(0)
            for c in punc:
                index = index.strip(c)
            season_number = int(index[1:3])
        elif type2:
            index = type2.group(0)[1:]
            for c in punc:
                index = index.strip(c)
            season_number = int(index[1:3])
        elif type3:
            index = type3.group(0)
            for c in punc:
                index = index.strip(c)
            index = index[:index.find('x')]
            season_number = int(index)
        elif type4:
            index = type4.group(0)
            for c in punc:
                index = index.strip(c)
            season_number = int(index[0])
        else:
            return None

        if season_number:
            if leading_zero:
                season_folder = season_text + " %02d" % season_number
            else:
                season_folder = season_text + " " + str(season_number)
            return season_folder
    
    
    def getShowIndex(self, episode):
        
        p_type1 = self.pattern.getShowIndex(self.pattern.getShowIndex_type1)
        p_type2 = self.pattern.getShowIndex(self.pattern.getShowIndex_type2)
        p_type3 = self.pattern.getShowIndex(self.pattern.getShowIndex_type3)
        p_type4 = self.pattern.getShowIndex(self.pattern.getShowIndex_type4)
        
        type1 = re.search(p_type1, episode)
        type2 = re.search(p_type2, episode)
        type3 = re.search(p_type3, episode)
        type4 = re.search(p_type4, episode)
        
        if type1:
            m = type1.group(0)
        elif type2:
            m = type2.group(0)[1:]
        elif type3:
            m = type3.group(0)
        elif type4:
            m = type4.group(0)
            
        punc = ['.', ' ', '-', '_']
        for c in punc:
            m = m.strip(c)
        return m
    
    
    def getMinimalQueryString(self, episode_file_name):
        efn = episode_file_name
        
        p_type1 = self.pattern.getMinimalQueryString(self.pattern.getMinimalQueryString_type1)
        p_type2 = self.pattern.getMinimalQueryString(self.pattern.getMinimalQueryString_type2)
        p_type3 = self.pattern.getMinimalQueryString(self.pattern.getMinimalQueryString_type3)
        
        type1 = re.search(p_type1, efn)
        type2 = re.search(p_type2, efn)
        type3 = re.search(p_type3, efn)

        # arg: "a.series.s01e01.blabla.mkv
        # return: "a.series"
        if type1:
            return efn[:efn.find(type1.group(0))]
        elif type2:
            return efn[:efn.find(type2.group(0))]
        elif type3:
            return efn[:efn.find(type3.group(0))]
      

            
class StringCleaner:
    '''Cleans a given string from common occurrences and punctuation
    
    StringCleaner is initialised with a list of common occurrences on runtime whereas the punctuation is provided
    It should not be applied to generic strings lacking an element such as "s01e01" or "1x10" (known as Progression Indicator or PI)
    '''    
    def __init__(self, common_occurrences=None):
        self._common_occurences = None
        if common_occurrences != None:
            try:
                if os.path.exists(common_occurrences) and \
                os.path.isfile(common_occurrences):
                    self._common_occurences = self._loadOccurenceFile(common_occurrences)
            except TypeError, e:
    #                self._common_occurences = common_occurrences[:]
                    self._common_occurences = ["dts","DiMENSION"]
        
    
    def _loadOccurenceFile(self, path_to_file):
        if os.path.exists(path_to_file):
            o = []
            for line in open(path_to_file,'r+'):
                o.append(line[:len(line) - 1])
            return o
        else:
            return None

    
    def _removeExtension(self, cleanee):
        index = cleanee.rfind('.')
        cleanee = cleanee[:index]
        return cleanee
        

    def __cleanOccurences(self, cleanee): # @deprecated
        for co in self._common_occurences:
            cleanee = cleanee.replace(co, '')
        return cleanee
    
    
    def _cleanOccurences(self, cleanee):
        if self._common_occurences == None:
            return cleanee
        punc = '((\\s+)|(-+)|(_+)|(\\.+))'
        for o in self._common_occurences:
            index = o.find('.')
            if index != -1:
                o = o[:index] + '\\.' + o[index + 1:]
            p = re.compile(punc + '(' + o + ')' + punc, re.IGNORECASE)
            cleanee = p.sub(" ",cleanee)
        return cleanee
    
    
    def _cleanPunctuation(self, cleanee):
        cleanee = re.sub('(\\s+)|(-+)|(_+)|(\\.+)', ' ', cleanee) #TODO: perhaps add some more punctuation
        return cleanee
    

    def stripclean(self, cleanee):
        # remove chars such as ':','-',''
        cleanee = re.sub("(:+)|(_+)|(-+)|(\\.+)|(\\))|(\\()|(!+)"," ", cleanee)
        cleanee = re.sub("(\\s+)"," ", cleanee)
        cleanee = cleanee.strip()
        cleanee = self.clean_apostrophe(cleanee)
        return cleanee
        
    
    def clean_apostrophe(self, cleanee):
        '''Clean any apostrophes(') followed by (s )'''
        if cleanee.find("'s ") != -1:     
            cleanee = re.sub("'s\\s", "s ", cleanee)
        if re.search("('s$)", cleanee, re.IGNORECASE) != None:
            cleanee = re.sub("'s$", "s", cleanee)
        return cleanee


    def _cleanProgressionIndicator(self, cleanee, returnIndex=False):
        
        p1 = '((\\s+)|(-+)|(_+)|(\\.+))(s\d{2}e\d{2})((\\s+)|(-+)|(_+)|(\\.+))' # S01E01 e.g.
        p2 = '((\\s+)|(-+)|(_+)|(\\.+))(\d{1,2}x\d{1,2})((\\s+)|(-+)|(_+)|(\\.+))' # 1x1, 10x10, 1x10, 10x1 e.g.
        p3 = '((\\s+)|(-+)|(_+)|(\\.+))([1-9][0-5][0-9]){1}((\\s+)|(-+)|(_+)|(\\.+))' # ".101-", "_901 " with ESS
        p = p1 + '|' + p2 + '|' + p3 
        
        rg = re.compile(p, re.IGNORECASE)
        if not returnIndex:
            return rg.sub(' ',cleanee)
        else:
            index = rg.search(cleanee).start()
            return index
        

    
    def partialClean(self, cleanee):
        '''Cuts everything starting with the PI and returns the result'''
        cleanee = cleanee[:self._cleanProgressionIndicator(cleanee, True)]
        cleanee = self._cleanOccurences(cleanee)
        cleanee = self._cleanPunctuation(cleanee)
        return cleanee

    
    def clean(self, cleanee, isFile=True):
        '''Does a full clean on a TV episode string
        
        This returns all remaining elements as a whitespace separated string
        '''
        c = cleanee[:]
        if isFile:
            c = self._removeExtension(c)
        c = self._cleanOccurences(c)
        c = self._cleanProgressionIndicator(c)
        for run in range(2): # removes punctuation created by the first run 
            c = self._cleanPunctuation(c)
        return c
    

class QueryGenerator:


    def genQueryElems(self,ws_sep_string):
        '''returns either the combination of all elements of a whitespace separated string
        or (I)returns a chain of all elements looped num-of-element times with each loop loosing
        the first element:
        (I) A B C-> (A,B,C),(A,B),(A),(B,C),(B),(C) 
        '''
        combinations = self._combine(ws_sep_string)
        return self._unpackCombinations(combinations)


    def _combine(self,ws_sep_string):
        list_of_elements = ws_sep_string.split(' ')
        for e in list_of_elements:
            if e == '': # some cleaning
                list_of_elements.remove(e)
        # heavy lifting        
        self.combines = []
        ingoing_list = list_of_elements[:]
        for elem in list_of_elements:
            self.__start_combine(ingoing_list[:])
            ingoing_list.remove(elem)

        return self.combines
    
    
    def __start_combine(self, remainder): 
        self.combines.append(tuple(remainder))
        remainder.pop(len(remainder) - 1)
        if len(remainder) == 0:
            return
        self.__start_combine(remainder)
    
    
    def _unpackCombinations(self,list_of_tuples):
        final_result = []
        strg = ''
        for tpl in list_of_tuples:
            count = 0
            for elem in tpl:
                if count == len(tpl) -1:
                    strg += elem
                    final_result.append(strg)
                    strg = ''
                else:
                    strg += elem + ' '
                count += 1
        
        return final_result


class QueryHandler:
    '''Queries remote resource for possible TV show titles
    
    Upon receiving possible TV show titles those are first checked against the local combinations
    and then purged of double entries followed by a last regex pattern check to narrow down the results to possibly a single one
    '''

    __default_host = "www.thetvdb.com"
    __default_api_getSeries = "/api/GetSeries.php?seriesname="
    __default_api_getEpisodes = "/api/603963AA95970288/series/%(ID)s/all/%(lang)s.xml" #TODO: WIP
    __default_api_key = "FAADD9E6115A051A"
    #http://thetvdb.com/api/603963AA95970288/series/248651//default/1/2/en.xml <-- get episode S01E02
    #http://thetvdb.com/api/603963AA95970288/series/248651/all/en.xml <- get all episodes
    
    def __init__(self, num_parallel_queries, pattern_compiler, language="English"):
        self.query_queue = Queue(num_parallel_queries)
        self.pattern = pattern_compiler
        self.__shows = {}
        self.language = language
        self.config = {}
        self.config['valid_languages'] = { 
            "Danish":"da", "Finnish":"fi", "Dutch":"nl", "German":"de", "Italian":"it",
            "Spanish":"es", "French":"fr", "Polish":"pl", "Hungarian":"hu", "Greek":"el",
            "Turkish":"tr","Russian":"ru", "Hebrew":"he", "Japanese":"ja", "Portuguese":"pt", "Chinese":"zh",
            "Czech":"cs", "Slovene":"sl", "Croatian":"hr", "Korean":"ko", "English":"en", "Swedish":"sv",
            "Norwegian":"no"
        }
    
        
    def processQueries(self,list_of_possible_names, episode_name=''):
        '''processes queries by calling all necessary methods for sending queries and validating the responses
        
        
        #args: list_of_possible_names = []
        #returns: dictionary with the name of the show and episode names
        #        result["name"] -> show name
        #        result["episode names"] -> dictionary of episode names [1][10]: Season 1 Episode 10 
        
        '''
        self._start_threads(list_of_possible_names)
        self.query_queue.join() # wait until all queries are done
        self._validateNameResult(episode_name, self._matchResults(list_of_possible_names, self.__shows))
        if len(self.__shows) > 0:
            series_id = self.__shows.keys()[0]
            self._sendEpisodesReq(series_id)
            return self.__shows[series_id]
        else:
            return None
    

    def __add_to_queue_sendRequest(self, single_combination):
        self.query_queue.put(single_combination)
    
    
    def __get_from_queue_sendRequest(self):
        single_combination = self.query_queue.get()
        self.__sendRequest(single_combination)
        self.query_queue.task_done()
        
    
    def _start_threads(self, list_of_possible_names):
        for single_combination in list_of_possible_names:
            addToQueue = Thread(target=self.__add_to_queue_sendRequest, args=(single_combination,))
            addToQueue.setDaemon(True)
            addToQueue.start()
        for i in range (len(list_of_possible_names)):
            getFromQueue = Thread(target=self.__get_from_queue_sendRequest)
            getFromQueue.setDaemon(True)
            getFromQueue.start()
    
                
    def __sendRequest(self, single_combination):
        '''sends actual queries and calls _analyzeResponse'''
        try:
            url_ = "http://" + \
                    self.__default_host + \
                    self.__default_api_getSeries + \
                    single_combination.replace(" ","%20")
            request = urllib2.Request(url_)
            connection = urllib2.urlopen(request)
            resp = connection.read()
            self.__getSeries(resp)
        except AttributeError, ae:
            if ae.args[0] == "AttributeError: 'NoneType' object has no attribute 'makefile'":
                time.sleep(5)
                connection = urllib2.urlopen(request)
                self.__getSeries(connection.read())
                
    
    def __getSeries(self, response):
        series = response.split("</Series>")
        if series is not None and series is not []:
            for show in series:
                # seriesid                
                compiled_pattern = self.pattern.getSeries\
                (self.pattern.get_series_seriesid)
                ID = re.search(compiled_pattern, show)
                if ID:
                    ID = ID.group(2)
                    # SeriesName
                    compiled_pattern = self.pattern.getSeries\
                    (self.pattern.get_series_seriesname)
                    SERIES = re.search(compiled_pattern, show).group(2)
                    self.__shows[ID] = {"name":SERIES,}
    
    
    def __analyzeRespone(self, response): #deprecated - use __getSeries() instead
        '''Looks for TV show names in response and on match calls _unpackResponse'''
        compiled_pattern = self.pattern.analyzeResponse()
        match_ = compiled_pattern.findall(response)
        if match_:
            return self.__unpackResponse(match_)

        
    def __unpackResponse(self,list_of_tuples): #deprecated - dont use at all!
        rslt = []
        for a_tuple in list_of_tuples:
            for elem in a_tuple:
                if not elem == '<SeriesName>' and not elem == '</SeriesName>':
                    rslt.append(elem)
        return rslt
                     

    def _matchResults(self, all_combinations, results):
        '''Checks every local combination against every retrieved/acquired TV show title
        
        This is a good way to remove utterly impossible matches:
        A response may consist of more word than what was initially conveyed (men -> Two And A Half Men)
        Now in order to discard of those a pattern using each local combination is checked against all results. 
        To avoid redundancies a set is returned 
        including possible matches using remotely acquired names
        '''
        names = []
        id_list = []
        c = StringCleaner()
        for comb in all_combinations:
            if not comb.find(" ") == -1: # not single word
                p = re.compile(self.__generatePattern(c.stripclean(comb)), re.IGNORECASE) # use local combination as pattern
                for ID in results.keys():
                    match_ = p.search(c.stripclean(results[ID]["name"])) #match against remote results
                    if match_:
                        names.append(c.stripclean(results[ID]["name"])) # on match add that particular remote result
                        id_list.append(ID)
            else: # single word
                for ID in results:
                    if comb.lower() == results[ID]["name"].lower(): #compare single word
                        names.append(results[ID]["name"])
                        id_list.append(ID)
        for id in self.__shows.keys():
            if id_list.count(id) == 0:
                self.__shows.pop(id)
        return self.__shows
 
    
    def _validateNameResult(self, movie_name, results):
        '''Tries to validate acquired TV show titles by checking them against the local episode name in question.
        
        For this a pattern on basis of the acquired TV show titles/ remote results is being generated and
        checked against our actual episode name. 
        Only the longest match in terms of len(match) is being returned with the assumption that this must
        be our wanted show name. Other matches might be false positives.
        In case match has less than 3 chars it will be discarded to avoid false positives.
        '''
        matches = ''
        match_id = -1
        c = StringCleaner()
        movie_name = c.stripclean(movie_name)
        for id in results:
            p = re.compile(self.__generatePattern(c.stripclean(results[id]["name"]),False), re.IGNORECASE)
            match_ = p.search(movie_name)
            if match_:
                if len(matches) < len(match_.group()): #crucial!: 
                    matches = results[id]["name"]
                    match_id = id
        if match_id == -1: # this is just a workaround for that annoying key_error thing which probably relates to a racing condition
            return None
        if len(results) > 0:
            if len(results[match_id]["name"]) > 2: # anything with less than 3 characters is going to be discarded - too many false positives otherwise
                for id in self.__shows.keys():
                    if id != match_id:
                        self.__shows.pop(id)
                return results[match_id]
            else:
                return None
        else:
            return None
            
    
    
    def __generatePattern(self, a_ws_sep_combination, rightAnchored=True):
        pattern = ''
        for strg in a_ws_sep_combination.split():
            pattern += strg + '.'
            
        pattern = pattern[:pattern.rfind('.')]
        if rightAnchored:
            pattern = '(' + pattern[:] + ')$'
        else:
            pattern = '(' + pattern[:] + ')'
            
        return pattern

        
    def _sendEpisodesReq(self, series_id):
        '''sends actual queries and calls _analyzeResponse'''
        try:
            api = self.__default_api_getEpisodes % \
                    {
                     "ID":series_id,
                     "lang":self.config["valid_languages"][self.language]
                     }
            url_ = "http://" + self.__default_host + api
            request = urllib2.Request(url_)
            connection = urllib2.urlopen(request)
            resp = connection.read()
            self.__getEpisodes(resp, series_id)
        except AttributeError,ae:
            if ae.args[0] == "AttributeError: 'NoneType' object has no attribute 'makefile'":
                time.sleep(5)
                connection = urllib2.urlopen(request)
                resp = connection.read()
                self.__getEpisodes(resp.read(), series_id)
     
    
    def __getEpisodes(self, response, sid):
        for episode in response.split("</Episode>"):
            try:
#                 season_num = re.search("(<Combined_season>)([0-9]{1,3})(</Combined_season>)", episode).group(2)
#                 ep_num = re.search("(<EpisodeNumber>)([0-9]{1,3})(</EpisodeNumber>)", episode).group(2)
#                 ep_name = re.search("(<EpisodeName>)(.+)(</EpisodeName>)", episode).group(2)
                
                season_number_pattern = self.pattern.getEpisodes(self.pattern.get_episodes_seasonnumber)
                episode_number_pattern = self.pattern.getEpisodes(self.pattern.get_episodes_episodenumber)
                episode_name_pattern = self.pattern.getEpisodes(self.pattern.get_episodes_episodename)
                
                season_num = season_number_pattern.search(episode).group(2)
                ep_num = episode_number_pattern.search(episode).group(2)
                ep_name = episode_name_pattern.search(episode).group(2)
                
                
                if not self.__shows[sid].has_key("episode_names"):
                    self.__shows[sid]["episode_names"] = {}
                if not self.__shows[sid]["episode_names"].has_key(season_num):
                    self.__shows[sid]["episode_names"][season_num] = {}
                self.__shows[sid]["episode_names"][season_num][ep_num] = ep_name
                
            except AttributeError,ae: # above element not matched
                pass # skip that particular episode
        if self.__shows[sid].has_key("episode_names") is False:
            self.__shows[sid]["episode_names"] = {}
            
    
    

    
class Query:
    '''Handling a Query from start to end.
    
    Preferably call this class instead of StringCleaner, QueryGenerator, QeueryHandler.
    This will cause far less manual work on your side. Just pass it a (tv episode) string.
    '''
    
    def __init__(self, common_occurrences, num_queries, pattern_compiler, language="English"):
        '''common_occurrences requires a path to a file with common occurrences'''
        self._cleaner = StringCleaner(common_occurrences)
        self._query_generator = QueryGenerator()
        self._query_handler = QueryHandler(num_queries, pattern_compiler, language)
        
    
    def sendQuery(self,episode_name, isFile=True):
        return self._query_handler.processQueries(self._generateQuery(episode_name, isFile), episode_name)
    
    def _clean(self, episode_name, isFile):
        return self._cleaner.clean(episode_name, isFile)
    
    
    def _combine(self, episode_name, isFile):
        return self._query_generator.genQueryElems(self._clean(episode_name, isFile))
    
    
    def _generateQuery(self, episode_name, isFile):
        return self._combine(episode_name, isFile)


class RenameElement:
    
    def __init__(self, syntax_element, start_position, end_position):
        self.syntax_element = syntax_element # %show, %episode, ...
        self.start_position = start_position # start index for syntax_element in rename_string
        self.end_position = end_position # end index for syntax_element in rename_string
        # the actual content: "S01E01", "Breaking Bad"
        # Also gap_content which equals syntax_element
        self.content = None
        
    def start(self):
        return self.start_position
    
    def end(self):
        return self.end_position
    
    def element(self):
        return self.syntax_element
    
    def get_content(self):
        return self.content
    
    
class OrderedRenameElementDict(dict):
    
    def __init__(self):
        self.custom_element_start = '%'
        self.custom_element_end = '%'
        self.custom_element_separator = '|'
        self.is_custom = "is_custom"
        self.is_gap = "is_gap"
    
    def order(self):
        '''Return an sorted listed ordered by increasing starting positions'''
        return sorted(list(self.values()),\
        key=lambda RenameElement: RenameElement.start_position)
    
    def gaps(self):
        '''Get position intervalls for all exisiting gaps'''
        ored = self.order()
        gap_list = []
        for index in range(0,len(ored)):
            if index + 1 != len(ored):
                gap_list.append\
                ((ored[index].end(), ored[index+1].start()))
        return gap_list
    
    def custom(self):
        '''Find all custom elements and turn them into lists'''
        start = self.custom_element_start
        end = self.custom_element_end
        sep = self.custom_element_separator 
        for key in self:
            if self[key].syntax_element[0] == start and \
            self[key].syntax_element[len(self[key].syntax_element)-1] == end:
                    self[key].syntax_element = \
                    self[key].syntax_element.strip(start)
                    self[key].syntax_element = \
                    self[key].syntax_element.split(sep)
                    self[key].is_custom = True
    
                    
    def drop_empty(self):
        '''Drop all elements that have content==None'''
        empty = []
        for key in self:
            if self[key].content == None:
                empty.append(key)
        for key in empty:
            self.pop(key)
            
    def drop_last_gap(self):
        '''Check if last gap is followed by any element and drop if not'''
        last_element = max(self.values(), \
        key=lambda RenameElement: RenameElement.start_position)
        if hasattr(last_element, self.is_gap):
            self.pop(last_element.start_position)
            
    def get_element(self, syntax_element):
        '''Search for an element using its syntax_element attribute
        
        This is based on the assumption that syntax_elements for all 
        standard and custom elements are unique. Do not search for gaps! 
        '''
        if syntax_element[0] != self.custom_element_start: return
        for key in self:
            if self[key].syntax_element == syntax_element:
                return self[key]
            
    def drop_element(self, syntax_element):
        '''Drop an element based on its syntax_element attribute
        
        
        This is based on the assumption that syntax_elements for all 
        standard and custom elements are unique. Do not drop gaps with this! 
        '''
        if syntax_element[0] != self.custom_element_start: return
        for key in self:
            if self[key].syntax_element == syntax_element:
                self.pop(key)
                return
            
    def drop_multi_gaps(self):
        '''Drop multiple gaps in a row'''
        gap_index = []
        index = 0
        for element in self.order():
            if hasattr(element, self.is_gap):
                gap_index.append(index)
            index += 1
        
        multi_gaps = []
        index = 0
        for idx in gap_index:
            if idx != gap_index[len(gap_index)-1]:
                if gap_index[index+1] - idx == 1:
                    multi_gaps.append(gap_index[index+1])
            index += 1
        
        ordered_elements = self.order()
        for index in multi_gaps:
            self.drop_gap(ordered_elements[index].start())
        
        
    def drop_gap(self, gap_key):
        '''Drop gap by key which is the same as the starting position'''
        self.pop(gap_key)
                
                    
    
class Renamer:
    
    def __init__(self, pattern_compiler):
        self.pattern = pattern_compiler
        self.element_show = "%show"
        self.element_1index = "%1index"
        self.element_2index = "%2index"
        self.element_3index = "%3index"
        self.show_index_type1 = 1
        self.show_index_type2 = 2
        self.show_index_type3 = 3
        self.element_episode = "%episode"

    
    def rename(self, episode, rename_string, substitute_string):
        rename_elements = self.parse_rename_string(rename_string)
        self.assign_content_to_standard_elements(episode, rename_elements)
        self.assign_content_to_custom_elements(episode, rename_elements)
        episode_name = self.construct_name(rename_elements) + \
        Utils().get_extension(episode.src_filename)
        episode_name = self.substitute_chars(episode_name, substitute_string)
        return episode_name
    
    def parse_rename_string(self, rename_string):
        rename_elements = OrderedRenameElementDict()
        self.parse_rename_elements(rename_string, rename_elements)
        self.parse_gap_content(rename_string, rename_elements)
        return rename_elements
        
            
    def parse_rename_elements(self, rename_string, rename_elements):
        compiled_syntax_pattern = self.pattern.parse_rename_string()
        matches = compiled_syntax_pattern.finditer(rename_string)
        for m in matches:
            rename_elements[m.start()] = \
            RenameElement(m.group(0), m.start(), m.end())
 
    def parse_gap_content(self, rename_string, rename_elements):
        for gap_position in rename_elements.gaps():
            gap_start, gap_end = gap_position
            syntax_element = rename_string[gap_start:gap_end]
            rename_elements[gap_start] = \
            RenameElement(syntax_element, gap_start, gap_end)
            rename_elements[gap_start].content = syntax_element
            rename_elements[gap_start].is_gap = True
            
    def assign_content_to_standard_elements(self, episode, rename_elements):
        # TODO: catch Error when no Rename String is given
        if rename_elements.get_element(self.element_show):
            rename_elements.get_element(self.element_show).content = episode.show_name
        if rename_elements.get_element(self.element_1index):
            show_index = self.convert_show_index\
            (episode.get_show_index(), self.show_index_type1)
            rename_elements.get_element(self.element_1index).content = show_index
        elif rename_elements.get_element(self.element_2index):
            show_index = self.convert_show_index\
            (episode.get_show_index(), self.show_index_type2)
            rename_elements.get_element(self.element_2index).content = show_index
        elif rename_elements.get_element(self.element_3index):
            show_index = self.convert_show_index\
            (episode.get_show_index(), self.show_index_type3)
            rename_elements.get_element(self.element_2index).content = show_index
 
        if episode.episode_name(decode=True) and rename_elements.get_element(self.element_episode):
            rename_elements.get_element(self.element_episode).content = episode.episode_name(decode=True)
        elif rename_elements.get_element(self.element_episode):
            rename_elements.drop_element(self.element_episode)
            
    def assign_content_to_custom_elements(self, episode, rename_elements):
        rename_elements.custom() 
        is_custom = rename_elements.is_custom
        for key in rename_elements:
            if hasattr(rename_elements[key], is_custom):
                for custom_element in rename_elements[key].syntax_element:
                    compiled_pattern = re.compile(custom_element, re.IGNORECASE)
                    a_match = compiled_pattern.search(episode.src_filename)
                    if a_match:
                        rename_elements[key].content = custom_element
                        break
                    
                    
    def construct_name(self, rename_elements):
        name = ""
        rename_elements.drop_empty()
        rename_elements.drop_multi_gaps()
        rename_elements.drop_last_gap()
        for element in rename_elements.order():
            name += element.get_content()
        return name
    
 
    def convert_show_index(self, show_index, type_, returnRaw=False):
        '''Convert show index between certain types
        
        
        (I  )    type_ = 1 : S01E01, S10E11
        (II )    type_ = 2 : 1x1, 10x11
        (III)    type_ = 3 : 101, 1011
        
        if returnRaw: 
            return (SEASON_NUM,EPISODE_NUM) # (1,1) e.g.
        '''
        p = self.pattern
        compiled_show_index_type1 = p.convert_show_index(p.convert_show_index_type1)
        csit1 = compiled_show_index_type1
        csit2 = p.convert_show_index(p.convert_show_index_type2)
        csit3 = p.convert_show_index(p.convert_show_index_type3)
        
        csit1_match = csit1.match(show_index)
        csit2_match = csit2.match(show_index)
        csit3_match = csit3.match(show_index)
        
        if csit1_match:
            if type_ == 2:
                return self.do_index_conversion(csit1_match.group(0), 12, returnRaw)
            elif type_ == 3:
                return self.do_index_conversion(csit1_match.group(0), 13, returnRaw)
            else:
                if returnRaw:
                    return self.do_index_conversion(csit1_match.group(0), 12, returnRaw)
                return show_index.upper()
        elif csit2_match:
            if type_ == 1:
                return self.do_index_conversion(csit2_match.group(0), 21, returnRaw)
            elif type_ == 3:
                return self.do_index_conversion(csit2_match.group(0), 23, returnRaw)
            else:
                if returnRaw:
                    return self.do_index_conversion(csit2_match.group(0), 21, returnRaw)
                return show_index
        elif csit3_match:
            if type_ == 1:
                return self.do_index_conversion(csit3_match.group(0), 31, returnRaw)
            elif type_ == 2:
                return self.do_index_conversion(csit3_match.group(0), 32, returnRaw)
            else:
                if returnRaw:
                    return self.do_index_conversion(csit3_match.group(0), 31, returnRaw)
                return show_index
        else:
            return show_index
        

    def do_index_conversion(self, show_index, type_, returnRaw=False):
        '''Actual conversion between show index types
        
        type_ is being composed by concatenating the input type_ with the output type_
        For instance: type_ 1 to type_ 2 -> type_ = 12

        
        (I  )    type_ = 1 : S01E01, S10E11
        (II )    type_ = 2 : 1x1, 10x11
        (III)    type_ = 3 : 101, 1011
        '''        
        season, episode = ('','')
        
        if type_ == 12:
            season = show_index[1:3]
            if season[0] == '0':
                season = season[1]
            episode = show_index[4:]
            if episode[0] == '0':
                episode = episode[1]
            if returnRaw:
                return (int(season),int(episode))
            return season + 'x' + episode
        
        elif type_ == 13:
            season = show_index[1:3]
            if season[0] == '0':
                season = season[1]
            episode = show_index[4:]
            if returnRaw:
                return (int(season),int(episode))
            return season + episode
    
        elif type_ == 21:
            season = show_index[:show_index.find('x')]
            episode = show_index[show_index.find('x')+1:]
            if len(season) == 1:
                season = '0' + season[0]
            if len(episode) == 1:
                episode = '0' + episode[0]
            if returnRaw:
                return (int(season),int(episode))
            return 'S' + season + 'E' + episode
        
        elif type_ == 23:
            season = show_index[:show_index.find('x')]
            episode = show_index[show_index.find('x')+1:]
            if len(season) == 2 and season[0] == '0':
                season = season[0]
            if len(episode) == 1:
                episode = '0' + episode[0]
            if returnRaw:
                return (int(season),int(episode))
            return season + episode
        
        elif type_ == 31:
            if len(show_index) == 4:
                season = show_index[:2]
                episode = show_index[2:]
            elif len(show_index) == 3:
                season = '0' + show_index[0]
                episode = show_index[1:]
            if returnRaw:
                return (int(season),int(episode))
            return 'S' + season + 'E' + episode
        
        elif type_ == 32:
            #2    type_ = 2 : 1x1, 10x11
            #3    type_ = 3 : 101, 1011
            if len(show_index) == 4:
                season = show_index[:2]
                if show_index[2] == '0':
                    episode = show_index[3]
                else:
                    episode = show_index[2:]
            elif len(show_index) == 3:
                season = show_index[0]
                if show_index[1] == '0':
                    episode = show_index[2]
            if returnRaw:
                return (int(season),int(episode))
            return season + 'x' + episode

        else:
            if returnRaw:
                return None
            return show_index


    def substitute_chars(self, renamee, substitute_string):
        ''' substitute_string = "'?'|'!', " -> kv_chars = ['?'|'!'] would substitute a '?' for '!'. '''
        seperator = '|'
        #TODO: some sanity checks perhaps
        if substitute_string.find(seperator) == -1: return renamee #invalid/missing string
        for sub_pair in substitute_string.split(','):
            if sub_pair.find(seperator) == -1: return renamee
            key, value = sub_pair.split(seperator)
            renamee = renamee.replace(key, value)
        return renamee

        
class EMException(Exception):
    
    error_codes = {
                   1 : "No match on series in remote db.",
                  }
    
    
    def __init__(self, message, errno):
        Exception.__init__(self, message)
        self.errno = errno
        
    def error(self):
        if self.errno != None:
            return self.error_codes[self.errno]
    
    
class Utils:
    
    def encode(self, string): # on the way out
#        return string.encode("utf_8", 'ignore')
        return fs_encode(string)
    
    def decode(self, string): # on the way in 
        try:
            return self.encode(string).decode("utf-8", 'ignore')
        except UnicodeDecodeError, ude:
            return string
        except UnicodeEncodeError, uee:
            return string  
        
    def get_extension(self, file_name):
        return file_name[file_name.rfind('.'):]

class Transcoder:
        
    def encode(self, output): # unicode -> byte string
        result = self.encode_ascii(output)
        if result == None:
            result = self.encode_utf8(output)
        if result == None:
            result = self.encode_latin1(output)
        if result == None:
            result = self.encode_cp1252(output)
        if result == None:
            result = self.encode_utf16(output)
        if result == None:
            result = ""
        return result
            
        
    def decode(self, input): # byte string -> unicode
        result = self.decode_ascii(input)
        if result == None:
            result = self.decode_utf8(input)
        if result == None:
            result = self.decode_latin1(input)
        if result == None:
            result = self.decode_cp1252(input)
        if result == None:
            result = self.decode_utf16(input)
        if result == None:
            result = ""
        return result
    
    
    def encode_ascii(self, output):
        try:
            return output.encode('ascii')
        except UnicodeEncodeError:
            return None

    
    def encode_utf8(self, output):
        try:
            return output.encode('utf-8')
        except UnicodeEncodeError:
            return None

    
    def encode_utf16(self, output):
        try:
            return output.encode('utf-16')
        except UnicodeEncodeError:
            return None

    
    def encode_latin1(self, output):
        try:
            return output.encode('latin_1')
        except UnicodeEncodeError:
            return None

    
    def encode_cp1252(self, output):
        try:
            return output.encode('cp1252')
        except UnicodeEncodeError:
            return None


    def decode_ascii(self, input):
        try:
            return input.decode('ascii')
        except UnicodeDecodeError:
            return None
    

    def decode_utf8(self, input):
        try:
            return input.decode('utf-8')
        except UnicodeDecodeError:
            return None

    
    def decode_utf16(self, input):
        try:
            return input.decode('utf-16')
        except UnicodeDecodeError:
            return None

    
    def decode_latin1(self, input):
        try:
            return input.decode('latin_1')
        except UnicodeDecodeError:
            return None

    
    def decode_cp1252(self, input):
        try:
            return input.decode('cp1252')
        except UnicodeDecodeError:
            return None


class ConfigDumper:
    #TODO: 
    #-managing of multiple log files or one log file with multiple entries
    #-checking for compatibility (version or compatibility tags)
    
    def __init__(self, hook):
        #        t= self.manager.config.plugin['MovieMover']['rename']
#        self.logger = self.manager.log
#        self.logger.debug('EPISODEMOVER TEST DEBUG LOG')
        self.hook = hook
        self.hook_name = hook.__class__.__name__ 
        self.config_parser = hook.config
        self.config_dict = self.config_parser.plugin[self.hook_name]
        #self.config['log']['log_folder']
        self.path = os.path.join(self.config_parser.config['log']['log_folder']['value'], self.hook_name + '.txt')
        return
        
        
    def dump(self):
        d = json.dumps(self.config_dict)
#        if os.path.exists(self.path):
#            self.path = os.path.join(self.path.split(self.path)[0], self.hook_name + '001')
        f = open(self.path, 'w')
        f.write(d)
        f.close()
        #self.hook.logDebug('%s config written to %s' % (self.hook_name, self.path))
        
        
    def load(self, src):
        self.config_dict = json.loads(open(src).readline())
        #def setPlugin(self, plugin, option, value):
        exclude = [
                   'outline',
                   'desc',
                   'tvshows',
                   'occurrences'
                  ]
        for option in self.config_dict.keys():
            if option not in exclude:
                self.config_parser.setPlugin(self.hook_name, option, self.config_dict[option]['value'])
        

class MoveLogger:
    
    def __init__(self, dst):
        self.path = dst
        self.transcoder = Transcoder()
        
    def timestamp(self, format_='datetime'):
        if format_ == 'datetime':
            return dt.strftime(dt.today(), '%d.%m.%y %H:%M:%S')
        elif format_ =='date':
            return dt.strftime(dt.today(), '%d.%m.%y')
        elif format_ =='time':
            return dt.strftime(dt.today(), '%H:%M:%S')
        else:
            return dt.strftime(dt.today(), '%d.%m.%y %H:%M:%S')   
    
    
    def log_mv(self, src, dst):
        if self.path != '':
            entry = '%s: MOVED: "%s" -> "%s"\n' % (self.timestamp('datetime'), src, dst)
            l = open(self.path, 'a')
            l.write(entry)
            l.close()
        
    
    def log_custom(self, record):
        record = self.transcoder.encode(record)
        if self.path != '':
            l = open(self.path, 'a')
            l.write('%s: %s \n' % (self.timestamp('datetime'), record))
            l.close()
