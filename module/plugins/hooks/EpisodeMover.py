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
#remote debugging
#from module.common.pydevsrc import pydevd 


class EpisodeMover(Hook):
    '''This class implements means to automatically move tv episodes within the underlying file system.
       

    Once pointed towards the local path of tv shows EM automatically acts upon the unrarFinished, packageFinished
    downloadFinished events trying to sort out the actual tv episodes based on certain criteria such,regex pattern and so forth.
    On passing the checks the file is moved to its final destination. 
    '''
    
#    TODO: (in no particular order)
#    -implement cleaning of sample files (as a hook of its own)
#    -implement removing/cleaning of junk files caused by particular download that was _processed_ by EM (readmes, nfos, etc...)
#    -implement element for %episode if DB supports that
#    -add separator element (?)
#    -EM localisation options for config
#    -EM localisation option for episode names
#    -Implement feature for defining custom strings EM can process (Colbert Report/Daily Show/...) - done though not accessible by way of the GUI
#    -It appears multiple calls are made for a single download: check into the cause for that!
#    -dynamic-length separator
#    -in case no match for show name fallback to parent folder and use its names
#    -Overwrite if size(src) > size(dst)
#    -Check if mixing of folders and files when querying for episode information works as intended
#    -Implement mapping of UTF8-encoded Umlaute to ASCII-encoded Umlaute and use it for querying/matching
#    -Do a final clean after renaming in order to remove multiple occurrences of special characters: ' .-_'
#    -Add unmatched files to a log file 
#    -Implement prioritisation for shows with same word length where one show also is the name of a rls grp: Dexter.S07E11.720p.HDTV.x264-EVOLVE.mkv
#    -Allow bypass of certain files triggered by specific package name declared in an external text file
#    -Modify series matching to only/alternatively use the portion before the series index (marked w/ arrows): "->A.Series.<-S01E01.blabla.release-grp.mkv"

#    Notes: 
#    -use "self.manager.dispatchEvent("name_of_the_event", arg1, arg2, ..., argN)" to define your own events! ;)
    __name__ = "EpisodeMover"
    __version__ = "0.519"
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
                    ("usr_string", "str", "Define your own naming convention for renaming", "%show %1index %hd=720p %YourElem=this|or|that"),
                    ("punc", "str","Provide the separator for the renaming procedure","."),
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
                    ("junk_exts", "list", "Files with these extensions will be automatically deleted if automatic deletion is enabled", "txt,nfo,sfv,sub,idx,bmp,jpg,png"),]
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
        self.renamer = FileRenamer(self.log)
        self.number_of_parallel_queries = 10
        self.language = self.getConfig("episode_language")
        


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
        ConfigDumper(self).dump()
        #ConfigDumper(self).load('/home/pyload/workspace/pyload/tests/test_suite/em_debug_config.cfg')
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
        isArchive = PatternChecker()
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
        valdor = PatternChecker()
        extensions = string.split(self.getConf("extensions"), ',')
        for ext in extensions: 
            if (valdor.hasExtension(file_name, ext)):
                return True
        self.logDebug(u'File extension in file "%s" is unrecognised' % file_name) #TODO: let the user choose what to do (ignore,delete or move anyway)
        return False
    
    
    def isTVEp(self,video_name, src_path):
        '''checks if a file is a tv show episode'''
        valdor = PatternChecker()
        if(valdor.isTVEpisode(video_name)):
            self.logDebug(u'File "%s" is a tv episode' % video_name)
            return True
        else:
            self.logDebug(u'File "%s" is not a tv episode' % video_name)
            self.mv_logger.log_custom(u'File %s is not a tv episode' % video_name)
            return False
    
        
    def isinDb(self, episode_obj, createShow=False):    
        '''checks downloaded/extracted show against local database of tv shows
        
        Returns True on a match and False if no match was produced
        '''
        episode = episode_obj
        valdor = PatternChecker()
        path = os.path.abspath(episode.src)
        #        crntShows = {}  #add found tv episodes: {ep_file_name:(path_to_show, show_title, show_index)}  <- obsolete structure; adapt it!
        for e in self.__tvdb.keys(): # where e is an actual name of locally existing show
            if valdor.hasPattern(episode.src_filename, valdor.createPattern(e)) is not None: # if True we got a local match
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
        #TODO: break this up into two methods -> def createShowLocally()
        if(createShow):
            if self.__getShowNameFromRemoteDB(episode) is not None: #actual name of tv show
                if os.path.exists(self.getConfig("tvshows")): # just a precaution - we don't want to leave a trail of folders across the filesystem
                    if self.getConfig("folder_sub") is True:
                        episode.show_name = self.renamer.substituteChars(episode.show_name, self.getConfig("char_sub"))
                    show_name = episode.show_name
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

    #deprecated    
    def __getFromRmteDB(self, file_name, root_folder, query, returnEpisodes=False):
        try:
#            def processQueries(self,list_of_possible_names, episode_name=''):
            if returnEpisodes is False:
                e = query.sendQuery(file_name)
            else:
                e = query.processQueries([file_name,])["episode_names"]
            self.logInfo(u'Episode query successful for "%s". Proceeding...' % file_name)
            return e
        except EMException, eme:
            if returnEpisodes is True:
                return None
        if self.getConfig("folder_search") is True and \
        os.path.split(self.config.plugin["ExtractArchive"]["destination"]["value"])[1] != root_folder and \
        os.path.split(self.config["general"]["download_folder"]) != root_folder:
            try:
                
                e = query.sendQuery(root_folder)
                self.logInfo(u'Episode query successful for "%s" using its enclosing directory ("%s"). Proceeding...' % (file_name, root_folder))
                return e
            except EMException, eme:
                    self.logInfo(eme.error() + " " + eme.args[0])
                    return None
                
    def __getShowNameFromRemoteDB(self, episode):
        full_query_string = episode.full_query_string
        minimal_query_string = PatternChecker().getMinimalQueryString(episode.full_query_string) # cut off file name at series index
        
        # in case PatternChecker() produces no workable result skip querying w/ minimal string 
        # e.g. Anger Mangangement: "poe-ams01e02.avi" -> NONE: poe gets cut off as common occurrence, ams gets cut off by getMinimalQueryString()
        # TODO: disable application of common occurrence removal for querying w/ minimal string (?)
        if minimal_query_string != None:
            try:
                minimal_query_string = [StringCleaner().clean(minimal_query_string, isFile=False),] # clean punctuation and convert to list
                query_handler = QueryHandler(self.number_of_parallel_queries, self.language)
                query_result = query_handler.processQueries(minimal_query_string)
                episode.show_name = query_result["name"]
                episode.episode_names = query_result["episode_names"]
                self.logInfo(u'Show name minimal query successful for "%s". Proceeding...' % episode.src_filename)
                if not episode.episode_name:
                    self.logInfo(u'Episode name determination for %s failed. Likely the particular episode is too recent.' % episode.src_filename)
                return episode
            except EMException, eme:
                # lets try again using the full file name
                pass
        
        # query using the full file name / full query string
        try:
            query = Query(self.getConfig("occurrences"),
                          self.number_of_parallel_queries,
                          self.language)            
            query_result = query.sendQuery(full_query_string)
            episode.show_name = query_result["name"]
            episode.episode_names = query_result["episode_names"]
            self.logInfo(u'Show name full query successful for "%s". Proceeding...' % episode.src_filename)
            if not episode.episode_name:
                self.logInfo(u'Episode name determination for %s failed. Likely the particular episode is too recent.' % episode.src_filename)
            return episode
        except EMException, eme:
            # lets try again with the root_folder if that option is enabled
            pass
        
        # query using the root folder where episode.src_filename resides in
        root_folder = episode.root_folder
        if self.getConfig("folder_search") is True and \
        os.path.split(self.config.plugin["ExtractArchive"]["destination"]["value"])[1] != root_folder and \
        os.path.split(self.config["general"]["download_folder"]) != root_folder:
            try:
                query_result = query.sendQuery(root_folder,isFile=False)
                episode.show_name = query_result["name"]
                episode.episode_names = query_result["episode_names"]
                self.logInfo(u'Show name query successful for "%s" using its enclosing directory ("%s"). Proceeding...' \
                             % (episode.src_filename, root_folder))
                if not episode.episode_name:
                    self.logInfo(u'Episode name determination for %s failed. Likely the particular episode is too recent.' % episode.src_filename)
                return episode
            except EMException, eme:
                self.logInfo(eme.error() + " " + eme.args[0])
                return None
            return None
    
    
    def __getEpisodeNamesFromRemoteDB(self, show_name):
        try:
            query_handler = QueryHandler(self.number_of_parallel_queries, self.language)
            e = query_handler.processQueries([show_name,])["episode_names"]
            self.logInfo(u'Episode query successful for "%s". Proceeding...' % show_name)
            return e
        except EMException, eme:
            return None
        
    
    def hasSeasonDir(self, episode_obj, createSeason=False, arbitrarySeason=True):
        #crntShows = {}  #add found tv episodes: {ep_file_name:(path_to_show, show_title, show_index)}  <- obsolete structure; adapt it!
        episode = episode_obj
        valdor = PatternChecker()
        season = valdor.getSeason(episode.src_filename,
                                  self.getConfig("season_text"),
                                  self.getConfig("leading_zero")) # returns "Season 1" e.g.
        if season == None:
            self.logDebug(u'No valid show index could be extracted from "%s". Skipping...' % episode.src_filename)
            return False
        season_path = os.path.join(episode.dst, season)
        show_index = valdor.getShowIndex(episode.src_filename)
        episode.show_index["raw"] = show_index
        episode.show_index["season"], episode.show_index["episode"] = self.renamer.getShowIndex(show_index)
        if (os.path.exists(season_path)):
            episode.dst = season_path
            self.logDebug(u'Season directory for show "%s" already exists. No creation necessary.' % episode.src_filename)
            return True
        elif arbitrarySeason is True:
            arbSeason = self.getArbSeasonPath(episode.dst, episode.src_filename)
            if arbSeason is not None:
                season_path = os.path.join(episode.dst, arbSeason)
                episode.dst = season_path
                self.logDebug(u'Custom season directory (%s) for show "%s" already exists. No creation necessary.' % (episode.show_name, arbSeason))
                return True
        if createSeason is True and os.path.exists(season_path) is not True:
            os.mkdir(season_path)
            episode.dst = season_path
            self.logInfo(u'Season directory for show "%s" does not exist. Directory "%s" is being created' % (episode.src_filename,season))
            return True
        elif createSeason is False and os.path.exists(season_path) is False:
            self.logDebug(u'Season directory for show "%s" does not exist. Directory "%s" is not being created' % (episode.show_name,season))
            return False
    
    
    def getArbSeasonPath(self,path_to_show, episode_name):
        directories = PathLoader().loadFolders(path_to_show)
        vldr = PatternChecker()
        
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
        valdor = PatternChecker()
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
            #pydevd.settrace("192.168.1.46",stdoutToServer=True,stderrToServer=True)
            episode_name = episode.episode_name(decode=True)
            episode.unicode()
            episode.dst_filename = self.renamer.parseEpisode(self.getConfig('usr_string'), episode.src_filename,
                                                              episode.show_name, episode.show_index['raw'],
                                                              episode_name, self.getConfig('punc'),
                                                              self.getConfig('char_sub'))
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
                if self.__isEmptyDir(file_):
                    if os.path.exists(file_):
                        os.rmdir(file_)
                        filelist.append((u'%s(dir)' % f))
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
    


class Pattern:
    
    
    def __init__(self):
        # this is more or less a stub
        # move all patterns from PatternChecker in here
        # compile and then instantiate once for EpisodeMover
        
        # config strings
        self.is_tv_episode = "is_tv_episode"
        self.is_tv_episode_type1 = "S00E00"
        
        self.pattern = {}
        self.pattern[self.is_tv_episode] = ""

class PatternChecker:



    def isTVEpisode(self, string_to_check):
        '''Checks a string for being a tv episode

        Checking is done by regex on the grounds of a tv episode having
        a progression indicator in terms of its season and episode numbering
        Example: s02e11 <- 11th episode of 2nd season - its trivial I know but had to be mentioned.
        '''

        pattern1 = '(s\d{2}e\d{2})' # S01E01 e.g.
        pattern2 = '(\d{1,2}x\d{1,2})' # 1x1, 10x10, 1x10, 10x1 e.g.
        pattern3 = '((\\s+)|(-+)|(_+)|(\\.+))(\d{3})((\\s+)|(-+)|(_+)|(\\.+))' # ".101-", "_901 " with ESS
        

#        rg = re.compile(re2+re3+re4+re5,re.IGNORECASE|re.DOTALL)
        rg = re.compile(pattern1 + '|' + pattern2 + '|' + pattern3, re.IGNORECASE|re.DOTALL)
        m = rg.search(string_to_check)
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

        p1 = '((\\s+)|(-+)|(_+)|(\\.+))(s\d{2}e\d{2})((\\s+)|(-+)|(_+)|(\\.+))' # S01E01 e.g.
        # recognition of Filenames like blablasxxexx
        # has the potential to produce false positives
        # therefore lets keep an eye on this
        p10 = '(\w{1})(s\d{2}e\d{2})((\\s+)|(-+)|(_+)|(\\.+))' # ShwnmS01E01 e.g.
        p2 = '((\\s+)|(-+)|(_+)|(\\.+))(\d{1,2}x\d{1,2})((\\s+)|(-+)|(_+)|(\\.+))' # 1x1, 10x10, 1x10, 10x1 e.g.
        p3 = '((\\s+)|(-+)|(_+)|(\\.+))([1-9][0-5][0-9])((\\s+)|(-+)|(_+)|(\\.+))' # 100 - 959 
        
        
        m1 = re.search(p1, string_to_check, re.IGNORECASE)
        m10 = re.search(p10, string_to_check, re.IGNORECASE)
        m2 = re.search(p2, string_to_check, re.IGNORECASE)
        m3 = re.search(p3, string_to_check, re.IGNORECASE)

        
        punc = ['.', ' ', '-', '_']
        if m1:
            index = m1.group(0)
            for c in punc:
                index = index.strip(c)
            season_number = int(index[1:3])
        elif m10:
            index = m10.group(0)[1:]
            for c in punc:
                index = index.strip(c)
            season_number = int(index[1:3])
        elif m2:
            index = m2.group(0)
            for c in punc:
                index = index.strip(c)
            index = index[:index.find('x')]
            season_number = int(index)
        elif m3:
            index = m3.group(0)
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
        p1 = '((\\s+)|(-+)|(_+)|(\\.+))(s\d{2}e\d{2})((\\s+)|(-+)|(_+)|(\\.+))' # S01E01 e.g.
        p10 = '(\w{1})(s\d{2}e\d{2})((\\s+)|(-+)|(_+)|(\\.+))' # ShwnmS01E01 e.g.
        p2 = '((\\s+)|(-+)|(_+)|(\\.+))(\d{1,2}x\d{1,2})((\\s+)|(-+)|(_+)|(\\.+))' # 1x1, 10x10, 1x10, 10x1 e.g.
        p3 = '((\\s+)|(-+)|(_+)|(\\.+))([1-9][0-5][0-9]){1}((\\s+)|(-+)|(_+)|(\\.+))' # ".101-", "_901 " with ESS
        
        m1 = re.search(p1, episode, re.IGNORECASE)
        m10 = re.search(p10, episode, re.IGNORECASE)
        m2 = re.search(p2, episode, re.IGNORECASE)
        m3 = re.search(p3, episode, re.IGNORECASE)
        
        if m1:
            m = m1.group(0)
        elif m10:
            m = m10.group(0)[1:]
        elif m2:
            m = m2.group(0)
        elif m3:
            m = m3.group(0)
            
        punc = ['.', ' ', '-', '_']
        for c in punc:
            m = m.strip(c)
        return m
    
    
    def getMinimalQueryString(self, episode_file_name):
        efn = episode_file_name

        p1 = '((\\s+)|(-+)|(_+)|(\\.+))(s\d{2}e\d{2})((\\s+)|(-+)|(_+)|(\\.+))' # S01E01 e.g.
        p2 = '((\\s+)|(-+)|(_+)|(\\.+))(\d{1,2}x\d{1,2})((\\s+)|(-+)|(_+)|(\\.+))' # 1x1, 10x10, 1x10, 10x1 e.g.
        p3 = '((\\s+)|(-+)|(_+)|(\\.+))([1-9][0-5][0-9]){1}((\\s+)|(-+)|(_+)|(\\.+))' # ".101-", "_901 " with ESS
        
        m1 = re.search(p1, efn, re.IGNORECASE)
        m2 = re.search(p2, efn, re.IGNORECASE)
        m3 = re.search(p3, efn, re.IGNORECASE)

        # arg: "a.series.s01e01.blabla.mkv
        # return: "a.series"
        if m1:
            return efn[:efn.find(m1.group(0))]
        elif m2:
            return efn[:efn.find(m2.group(0))]
        elif m3:
            return efn[:efn.find(m3.group(0))]
      

            
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
    
    def __init__(self, num_parallel_queries, language="English"):
        self.query_queue = Queue(num_parallel_queries)
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
            raise EMException(u"%s either unknown or too generic." % episode_name, 1 )
    

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
                id_s = "(<seriesid>)"
                id = "([0-9]+)"
                id_e = "(</seriesid>)"
                p = id_s + id + id_e
                ID = re.search(p, show)
                if ID:
                    ID = ID.group(2)
                    # SeriesName
                    name_s = '(<SeriesName>)'
                    name = '(.{1,})'
                    name_e = '(</SeriesName>)'
                    p = name_s + name + name_e
                    SERIES = re.search(p, show).group(2)
                    self.__shows[ID] = {"name":SERIES,}
    
    
    def __analyzeRespone(self, response): #deprecated - use __getSeries() instead
        '''Looks for TV show names in response and on match calls _unpackResponse'''
        sn_start = '(<SeriesName>)'
        middle = '(.{1,})'
        sn_end = '(</SeriesName>)'
        pattern = sn_start + middle + sn_end
        p = re.compile(pattern)

        match_ = p.findall(response)
        if match_:
            return self.__unpackResponse(match_)
        else:
            return None

        
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
                season_num = re.search("(<Combined_season>)([0-9]{1,3})(</Combined_season>)", episode).group(2)
                ep_num = re.search("(<EpisodeNumber>)([0-9]{1,3})(</EpisodeNumber>)", episode).group(2)
                ep_name = re.search("(<EpisodeName>)(.+)(</EpisodeName>)", episode).group(2)
                
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
    
    def __init__(self, common_occurrences, num_queries, language="English"):
        '''common_occurrences requires a path to a file with common occurrences'''
        self._cleaner = StringCleaner(common_occurrences)
        self._query_generator = QueryGenerator()
        self._query_handler = QueryHandler(num_queries, language)
        
    
    def sendQuery(self,episode_name, isFile=True):
        return self._query_handler.processQueries(self._generateQuery(episode_name, isFile), episode_name)
    
    
    def _clean(self, episode_name, isFile):
        return self._cleaner.clean(episode_name, isFile)
    
    
    def _combine(self, episode_name, isFile):
        return self._query_generator.genQueryElems(self._clean(episode_name, isFile))
    
    
    def _generateQuery(self, episode_name, isFile):
        return self._combine(episode_name, isFile)
    
class FileRenamer:
    '''Allows renaming of tv shows based on an user defined methodology'''
     
     
    def __init__(self, debug_logger):
        self.log = debug_logger
        self.show = "%show"
        self.index1 = "%1index"
        self.episode = "%episode"
        self.reset()
        
    def reset(self):
        '''Resets all variables to default states.
        
        This enables using of a single instance of this class to process multiple episodes. 
        '''
        # I suspect simply setting it to None would do.
        # Serves to demonstrate the employed data structure for renaming.
        self.elements = {self.show:("",), self.index1:("",)} 
        
        
        
        
#------------------------------PUBLIC INTERFACE-----------------------------------------
    def parseEpisode(self, usr_string, episode, show_name, show_index,\
                     episode_name, punctuation, substitute_string):
        '''This is the only public method that should be used'''
        self.reset()
        return self._parseEpisode(usr_string, episode, show_name, show_index,\
                                  episode_name, punctuation, substitute_string)
    
    def getShowIndex(self, show_index):
        return self.__convertShowIndex(show_index, 1, returnRaw=True)
#------------------------------PUBLIC INTERFACE-----------------------------------------    
        
    
    def _parseEpisode(self, usr_string, episode, show_name, show_index,\
                      episode_name, punctuation, substitute_string):
        # Apparently nonsensical. Everything should be either in or converted to UTF8.
        # No point in converting to a string again. Causes UnicodeDecodeErrors as well.
        # unicode -> string
        #usr_string = str(usr_string)
        #episode = episode.encode("utf8")
        #show_name = str(show_name)
        #show_index = str(show_index)
        #if episode_name != None:
        #    episode_name = str(episode_name)
        #punctuation = str(punctuation)
        
        show_index = show_index.strip()
        self.__parseCustomElems(usr_string)
        self.__parseCustomStrings(usr_string)
        self.__assignStdElements(show_name, show_index, episode_name, punctuation, usr_string)
        self.__parseCstmEpElems(episode)
        result = self.__constructName(usr_string, punctuation) + self.__addExtension(episode)
        if substitute_string == '':
            return result
        return self.substituteChars(result, substitute_string)

    def __parseIndexElem(self, usr_string):
        match = re.findall('(%[1-3]index)', usr_string)
        if len(match) > 1:
            return self.index1
        else:
            return match[0]

    def __parseCustomElems(self, usr_string):
        pattern = "(%[A-z]+=)(([A-z_0-9\\-\\.]\\|?)+)"# "%show.%index.%hd=720p|1080p"
        m = re.findall(pattern, usr_string)
        if m:
            return self.__unpackCustomElems(m)

    def __unpackCustomElems(self, list_of_elem_tpls):
        lst = {}
        for tple in list_of_elem_tpls:
            lst[tple[0]] = tple[1]
        return self.__assignCustomElements(lst)
    
    def __assignCustomElements(self, lst_of_cstm_elems):
        '''Analyze previously found custom elements and assign them
        
        
        ingoing: "%elem=val1|val2|valN"
        assign to: self.elements = {'%elem':("val1", "val2", "valN")}
        '''
        
        for cst_elem in lst_of_cstm_elems.keys():
            self.elements[cst_elem[:len(cst_elem)-1]] = tuple(lst_of_cstm_elems.get(cst_elem).split('|'))

    def __parseCustomStrings(self,usr_string):
        pattern = "'([\w\d_ \\(\\)\\[\\]\\-\\.]+)'"# "%show.'('%index.')'"
        m = re.findall(pattern, usr_string)
        if m:
            return self.__assignCustomStrings(m)
            
    def __assignCustomStrings(self,lst_of_cstm_strings):
        '''Analyze previously found custom elements and assign them
        
        
        ingoing: "%elem=val1|val2|valN"
        assign to: self.elements = {'%elem':("val1", "val2", "valN")}
        '''
        for idx,item in enumerate(lst_of_cstm_strings):
            self.elements[idx] = item

    def __parseCstmEpElems(self, episode):
        for key in self.elements.keys():
            if not isinstance(key, int) and key != self.show \
            and re.match('(%[1-3]index)', key) is None and key != self.episode:
                for tpl_ in self.elements.get(key):
                    pattern = '((\\s+)|(-+)|(_+)|(\\.+))' + '(' + tpl_ + ')' + '((\\s+)|(-+)|(_+)|(\\.+))'
                    m_ = re.search(pattern, episode)
                    if m_:
                        self.elements[key] = (m_.group(0)[1:len(m_.group(0)) - 1],)
                    else:
                        tmp = list(self.elements[key])
                        try:
                            tmp.remove(tpl_)
                        except ValueError, e:
                            #TODO: check if there is a more elegant way to do this
                            pass
                        self.elements[key] = tuple(tmp)
                        if len(self.elements.get(key)) == 0:
                            self.elements.pop(key)
        return
    
    def __constructName(self, usr_string, punctuation='.'):
        indices = []
        punctflag = False
        
        for (cnt,cstr) in enumerate(re.finditer("'([\w\d_ \\(\\)\\[\\]\\-\\.]+)'",usr_string)):
            indices.append((cnt,cstr.start()))

        for key in self.elements.keys():
            if not isinstance(key,int):
                index = usr_string.find(key)
                if index != -1:
                    indices.append((key,index))

        indices.sort(key=lambda indices: indices[1])   

        name = ""
        for index in indices:
            if punctflag:
                if not isinstance(index[0],int): 
                    name += punctuation
            punctflag = True
            
            indexElem = re.search("(%[1-3]index)", usr_string).group(0)
            if index[0] == self.show:
                name += self.__encodeShowName(self.elements.get(index[0])[0], punctuation)
            elif index[0] == self.episode:
                name += self.elements[self.episode][0]
            elif index[0] == indexElem:
                name += self.__convertShowIndex(self.elements.get(index[0])[0], int(indexElem[1]))
            elif isinstance(index[0],int):
                name += self.elements[index[0]]
                punctflag = False
            else:
                name += self.elements.get(index[0])[0]
        return name
    
    
    def __encodeShowName(self, show_name, punctuation):
        name = ''
        nme_lst = show_name.split(' ')
        for e in nme_lst:
            if e != nme_lst[len(nme_lst) - 1]:
                name += e + punctuation
            else:
                name += e
        return name
    
    
    def __convertShowIndex(self, show_index, type, returnRaw=False):
        '''Convert show index between certain types
        
        
        (I  )    type = 1 : S01E01, S10E11
        (II )    type = 2 : 1x1, 10x11
        (III)    type = 3 : 101, 1011
        
        if returnRaw: 
            return (SEASON_NUM,EPISODE_NUM) # (1,1) e.g.
        '''
        
        pattern1 = '(S\d{2}E\d{2})' # S01E01 e.g.
        pattern2 = '(\d{1,2}x\d{1,2})' # 1x1, 10x10, 1x10, 10x1 e.g.
        pattern3 = '(\d{1,4})' # 101, 901 with ESS
        pattern = pattern1 + '|' + pattern2 + '|' + pattern3

        match = re.match(pattern, show_index, re.IGNORECASE)
        
        if match.group(1):
            if type == 2:
                return self.__doIndexConversion(match.group(1), 12, returnRaw)
            elif type == 3:
                return self.__doIndexConversion(match.group(1), 13, returnRaw)
            else:
                if returnRaw:
                    return self.__doIndexConversion(match.group(1), 12, returnRaw)
                return show_index.upper()
        elif match.group(2):
            if type == 1:
                return self.__doIndexConversion(match.group(2), 21, returnRaw)
            elif type == 3:
                return self.__doIndexConversion(match.group(2), 23, returnRaw)
            else:
                if returnRaw:
                    return self.__doIndexConversion(match.group(2), 21, returnRaw)
                return show_index
        elif match.group(3):
            if type == 1:
                return self.__doIndexConversion(match.group(3), 31, returnRaw)
            elif type == 2:
                return self.__doIndexConversion(match.group(3), 32, returnRaw)
            else:
                if returnRaw:
                    return self.__doIndexConversion(match.group(3), 31, returnRaw)
                return show_index
        else:
            return show_index
        
    def __doIndexConversion(self, show_index, type, returnRaw=False):
        '''Actual conversion between show index types
        
        type is being composed by concatenating the input type with the output type
        For instance: type 1 to type 2 -> type = 12

        
        (I  )    type = 1 : S01E01, S10E11
        (II )    type = 2 : 1x1, 10x11
        (III)    type = 3 : 101, 1011
        '''        
        season, episode = ('','')
        
        if type == 12:
            season = show_index[1:3]
            if season[0] == '0':
                season = season[1]
            episode = show_index[4:]
            if episode[0] == '0':
                episode = episode[1]
            if returnRaw:
                return (int(season),int(episode))
            return season + 'x' + episode
        
        elif type == 13:
            season = show_index[1:3]
            if season[0] == '0':
                season = season[1]
            episode = show_index[4:]
            if returnRaw:
                return (int(season),int(episode))
            return season + episode
    
        elif type == 21:
            season = show_index[:show_index.find('x')]
            episode = show_index[show_index.find('x')+1:]
            if len(season) == 1:
                season = '0' + season[0]
            if len(episode) == 1:
                episode = '0' + episode[0]
            if returnRaw:
                return (int(season),int(episode))
            return 'S' + season + 'E' + episode
        
        elif type == 23:
            season = show_index[:show_index.find('x')]
            episode = show_index[show_index.find('x')+1:]
            if len(season) == 2 and season[0] == '0':
                season = season[0]
            if len(episode) == 1:
                episode = '0' + episode[0]
            if returnRaw:
                return (int(season),int(episode))
            return season + episode
        
        elif type == 31:
            if len(show_index) == 4:
                season = show_index[:2]
                episode = show_index[2:]
            elif len(show_index) == 3:
                season = '0' + show_index[0]
                episode = show_index[1:]
            if returnRaw:
                return (int(season),int(episode))
            return 'S' + season + 'E' + episode
        
        elif type == 32:
            #2    type = 2 : 1x1, 10x11
            #3    type = 3 : 101, 1011
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
        
        
    def __formatEpisodeName(self, episode_name, punc):
        if episode_name is not None:
            return episode_name.strip().replace(" ", punc)
        return None
        

    def __addExtension(self, episode):
        return episode[episode.rfind("."):]
    
    
    def __assignStdElements(self, show_name, show_index, episode_name, punctuation, usr_string):
        self.elements[self.show] = (self.__encodeShowName(show_name, punctuation),)
        self.elements[self.__parseIndexElem(usr_string)] = (show_index,)
        if episode_name != None:
            self.elements[self.episode] = (self.__formatEpisodeName(episode_name, punctuation),)
            
    def substituteChars(self, renamee, substitute_string):
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

class Transcoder:
        
    def encode(self, output):
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
            
        
    def decode(self, input):
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
        for option in self.config_dict.keys():
            if option not in (u'outline', u'desc'):
                self.config_parser.setPlugin(self.hook_name, option, self.config_dict[option]['value'])
        

class MoveLogger:
    
    def __init__(self, dst):
        self.path = dst
        
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
        if self.path != '':
            l = open(self.path, 'a')
            l.write('%s: %s \n' % (self.timestamp('datetime'), record))
            l.close()