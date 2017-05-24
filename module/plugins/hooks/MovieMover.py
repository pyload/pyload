#!/usr/bin/env python
# -*- coding: utf-8 -*-
from Queue import Queue
from datetime import datetime
from module.plugins.Hook import Hook
from threading import RLock, Thread
from urllib import urlencode
from urllib2 import HTTPError, URLError
from module.utils import fs_encode,save_path
from module.common.json_layer import json_loads 
import os
import re
import shutil
import time
import urllib2
import sys
#from module.common.pydevsrc import pydevd 
#pydevd.settrace("192.168.1.29",stdoutToServer=True,stderrToServer=True)

class MovieMover(Hook):
    __name__ = "MovieMover"
    __version__ = "0.395"
    __description__ = "MovieMover(MM) moves your movies for you"
    __config__ = [("activated" , "bool" , "Activated"  , "False" ),
                  ("extension", "str", "List of supported extensions", "mkv,avi,mp4,wmv"),
                  ("movies", "path", "Path to your local movies", ""),
                  ("common", "path", "Path to a file with common occurrences(one per line)", "/path/to/file.txt"),
                  ("rename", "str", "Rename movies based on provided string(Check Documentation for Syntax)", "%title"),
                  ("punc","str","Punctuation used for movie renaming","."),
                  ("subfolder", "bool", "Create subfolder for each movie", "False"),
                  ("startup", "bool", "On startup peruse download/extraction directory for movies", "False"),
                  ("language", """English;German;Danish;Finnish;Dutch;Italian;Spanish;French;Polish;
                    Hungarian;Greek;Turkish;Russian;Hebrew;Japanese;Portugese;Chinese;Czech;
                    Slovene;Croatian;Korean;Swedish;Norwegian""","Choose a language for your movie titles","English"),
                  ("folder", "bool", "On a matching failure use enclosing folder name to determine movie title", "False"),
                  ("rename_options", """File only;File and Folder;Folder only;Nothing""", "Choose the extent of the renaming", "Nothing"),
                  ("sample", "bool", "Ignore sample files", "False"),
                  ("blacklist", "path", "/path/to/blacklist.txt (or relative to pyload config folder)", ""),
                  ("bl_switch", "bool", "Blacklisting", "False"),]
    __author_name__ = ("rusk")
    __author_mail__ = ("troggs@gmx.net")
    
    event_map = {"unrarFinished":"unrarFinished",} #add event notATVShow:processFile dispatched from EM (?)
    
    __movie_queue = Queue(1) # one moving operation at a time

    #TODO:
    #-- 02.02.2014 --
    #-Order in which to match against particular sources (filename, dirname, remote db)
    #-Enforce matching only for a particular date if provided
    #-- LEGACY -- 
    #-Convenience features such as overwriting/moving of single files within a package
    #-On failing to match a movie assume articles for local combinations
    #-Add separator element (?)
    #-allow user to build subfolder for movie; add a config entry for a list of 4 options: only file/file&folder/folder only/nothing
    #-Overwrite if size(src) > size(dst)
    #-check into meaning of "original_title" and "title" for moviedb api. \
    #-Seems "original_title" is the actual non-localised title from the country of origin
    #-Look into subfolder creation of 'ExtractArchive'
    #-prevent too many queries at the same time! use locks or something or implement a dedicated queue system for queries
    #-Check if implementation of moving queue specifically the moving of only one file at a time was done in the right way
    #-Overhaul _loadMovies() by outsourcing its non-essential functionality; in the end it really only should _loadMovies while delegating \
    #-the creation of Movie_Objects and the retrieval of movie information to other methods: __createMovie(), __getMovieInformation()
    #-Do a final clean after renaming in order to remove multiple occurrences of special characters: ' .-_'
    #-Bug: In case a title exists more than once for one movie the first match is assumed to be correct. Implement release date checking.     


    def coreReady(self):
        if self.getConfig("startup") is True:
            self.doInitialSearch()
    
    
    def doInitialSearch(self):
        extract_path = self.config.plugin["ExtractArchive"]["destination"]["value"]
        dl_path = self.config["general"]["download_folder"]
        
        if self.config.plugin["ExtractArchive"]["activated"]["value"] is False or \
             len(self.config.plugin["ExtractArchive"]["destination"]["value"]) == 0:
            self.logDebug('Initial search on startup activated. Proceeding...')
            self.doProcessing(dl_path)
        elif dl_path.find(extract_path) != -1:
            self.logDebug('Initial search on startup activated. Proceeding...')
            self.doProcessing(extract_path)
        elif extract_path.find(dl_path) != -1:
            self.logDebug('Initial search on startup activated. Proceeding...')
            self.doProcessing(dl_path)
        else:
            self.logDebug('Initial search on startup activated. Proceeding...')
            self.doProcessing(extract_path)
            self.doProcessing(dl_path)

    
    # event dispatched on completion of single file   
    def downloadFinished(self, pyfile):
        try:
            p = pyfile.package()
            path_to_file = os.path.join(self.config["general"]["download_folder"], p.folder, pyfile.name)
            for ext in ['rar', 'zsip']:
                if ext == self.__getExtension(path_to_file):
                    return
            self.doProcessing(path_to_file)
        except AttributeError, ae:
            if ae.args[0] == "plugin":
                self.logDebug("caught and ignored AttributeError: 'plugin'.")
    
    
#    def packageFinished(self, pypack):
#        self.doProcessing(os.path.join(self.config["general"]["download_folder"], pypack.folder))
    
    
    def unrarFinished(self,path_to_extracted_files,path_to_downloads):
        self.doProcessing(path_to_extracted_files)
    
    
    def doProcessing(self, src):
        src = Utils(self.logDebug_).decode(src)
        if os.path.exists(self.getConfig('movies')) is False:
            self.logError(u"No or invalid movie destination directory specified. Aborting...")
            return
        movies = self._loadMovies(src)
        if movies != None:
            self._startMovingThreads(movies)
        else:
            if os.path.isdir(src):
                self.logInfo('No movies in "%s" to process.' % src )
            elif os.path.isfile(src):
                self.logInfo('"%s" is not a movie.' % src )
            else:
                self.logInfo('"%s" cannot be processed.' % src)
                
    
    
    def _loadMovies(self, root_path):
        files_ = []
        root_path = str(root_path)
        if not os.path.isfile(root_path):
            for dirpath, dirs, files in os.walk(root_path):
                for file_ in files:
                    fpath = os.path.join(dirpath,file_)
                    try:
#                        fpath = Utils().decode(fpath)
#                        fpath = Utils().encode(fpath)
                        fpath = Transcoder(self.logDebug_).decode(fpath)
                    except Exception, e:
                        self.logDebug(e.args[0] +' while processing ' + file_)
                        break
                    if self.__isVideo(fpath) and \
                    not self.__isTVEpisode(fpath) and \
                    not self.__isBlacklisted(fpath) and \
                    not self.__isSample(file_):
                        movie = self.__isMovie(file_, os.path.split(dirpath)[1])
                        if movie != None:
                            language = self.getConfig("language")
                            if movie["title"].has_key(language):
                                self.logInfo('Using %s title "%s" for movie "%s"' % (language, movie["title"][language][0], file_))
                                title = movie["title"][language][0]
                            elif movie["title"].has_key("standard"):
                                self.logInfo('Using "%s" as title for movie "%s"' % (movie["title"]["standard"][0], file_))
                                title = movie["title"]['standard'][0]
                            else:
                                self.logInfo('Using original title "%s" for movie "%s"' % (movie["title"]["original"][0], file_))
                                title = movie["title"]['original'][0]
                            files_.append(Movie(title,
                                               fpath,
                                               self.getConfig('movies'),
                                               self.__rename(file_, title, movie["year"][0:4], self.__getPunctuation())))
                        else:
                            pass
#                            self.logDebug('No or no conclusive match on video "%s"' % file_)
        else:
            bn, file_ = os.path.split(root_path)
            try:
                bn = Transcoder(self.logDebug_).decode(bn)
                file_ = Transcoder(self.logDebug_).decode(file_)
            except Exception, e:
                self.logDebug(e.args[0] +' while processing ' + root_path)
                return None
            if self.__isVideo(file_) and \
            not self.__isTVEpisode(file_) and \
            not self.__isBlacklisted(fpath) and \
            not self.__isSample(file_):
                movie = self.__isMovie(file_, os.path.split(bn)[1])
                if movie != None:
                    language = self.getConfig("language")
                    if movie["title"].has_key(language):
                        self.logInfo('Using %s title "%s" for movie "%s"' % (language, movie["title"][language][0], file_))
                        title = movie["title"][language][0]
                    elif movie["title"].has_key("standard"):
                        self.logInfo('Using "%s" as title for movie "%s"' % (movie["title"]["standard"][0], file_))
                        title = movie["title"]['standard'][0]
                    else:
                        self.logInfo('Using original title "%s" for movie "%s"' % (movie["title"]["original"][0], file_))
                        title = movie["title"]['original'][0]
                    files_.append(Movie(title,
                                       root_path,
                                       self.getConfig('movies'),
                                       self.__rename(file_, title, movie["year"][0:4], self.__getPunctuation())))
                else:
                    pass
#                    self.logDebug('No or no conclusive match on video "{0}"' % file_)
        if files_ != []:
            return files_
        else:
            return None
    
    
    def __isVideo(self, file_name):
        for ext in self.getConfig("extension").split(","):
            if ext == file_name[file_name.rfind('.')+1:]:
                return True
        return False
    

    def __isSample(self, file_name):
        if self.getConfig("sample") is False:
            return False
        match_ = re.search(
                           "((^)|(\\.+)|(-+)|(_+)|(\\s+))(sample)(($)|(\\.+)|(-+)|(\\s+)|(_+))", \
                           file_name, \
                           re.IGNORECASE
                          )
        if match_:
            return True
        else:
            return False    
    
    
    def __getExtension(self, file_name):
        return file_name[file_name.rfind('.')+1:]
    
    
    def __cutFile(self, file_name, returnExt):
        if returnExt is True:
            return self.__getExtension(file_name)
        else:
            return file_name[:file_name.rfind('.')]
            
            
    def __overwrite(self, src, dst):
        pass
    
    
    def __getPunctuation(self):
        p = self.getConfig("punc")
        if len(p) == 0:
            return " "
        else:
            return p
        
        
    def __getYear(self, file_name):
        pa = "((\\s)|(\\.)|(_)|(-)|(^))"
        pe = "((\\s)|(\\.)|(_)|(-)|($))"
        d = pa + "(\\d{4})" + pe
        crnt = re.search(d, file_name)
        if crnt:
            crnt = crnt.group(7)
            if int(crnt) >= 1920 and \
            int(crnt) <= datetime.today().year:
                return crnt
            else:
                return None
         
    
    def __isTVEpisode(self, video_name):
        """Checks a string for being a tv episode

        Checking is done by regex on the grounds of a tv episode having
        a progression indicator in terms of its season and episode numbering
        Example: s02e11 <- 11th episode of 2nd season - its trivial I know but had to be mentioned.
        """

        pattern1 = '(s\d{2}e\d{2})' # S01E01 e.g.
        pattern2 = '(\d{1,2}x\d{1,2})' # 1x1, 10x10, 1x10, 10x1 e.g.
        pattern3 = '((\\s+)|(-+)|(_+)|(\\.+))([1-9][0-5][0-9])((\\s+)|(-+)|(_+)|(\\.+))' # ".101-", "_901 " with ESS
        
        rg = re.compile(pattern1 + '|' + pattern2 + '|' + pattern3, re.IGNORECASE|re.DOTALL)
        m = rg.search(video_name)

        if m:
            return True
        else:
            return False
        
    def __isBlacklisted(self, path_to_file):
        """checks if a file should not be processed based on part of its path"""
        if self.getConfig("bl_switch") is False:
            return False
        
        path_to_file = os.path.split(path_to_file)[0] # we don't care for filename
        path_to_blacklist = self.getConfig("blacklist")
        if not os.path.exists(path_to_blacklist):
            return False
        
        blacklist = []
        for line in open("blacklist.txt"):
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

    
    def __isMovie(self, video_name, root_folder):
        q = Query(self.getConfig("common"), self.getConfig("language"), self.logDebug_, 10)
        year = self.__getYear(video_name)
        self.logInfo('Searching corresponding title for "%s". Please wait...' % video_name)
        m = q.query(video_name, year, isFile=True)
        if m == None:
            self.logDebug('No match on title for "%s"' % video_name)
        if m != None:
            self.logInfo('"%s" recognised as movie "%s"' % (video_name, m["title"]["original"][0]))
            return m
        elif self.getConfig("folder") is True and \
        (os.path.split(self.config.plugin["ExtractArchive"]["destination"]["value"])[1] != root_folder) and \
        (os.path.split(self.config["general"]["download_folder"])[1] != root_folder): 
            year = self.__getYear(root_folder)
            m = q.query(root_folder, year, isFile=False)
            if m != None:
                self.logInfo('"%s" recognised as movie "%s"' % (video_name, m["title"]["original"][0]))
                return m
            else:
                self.logDebug('No match on title for "%s" using its enclosing folder "%s"' % (video_name, root_folder))
        self.logInfo('No match on title for video file "%s"' % video_name)
        return None
    
    
    
    def __rename(self, movie_name, movie_title, movie_year, punctuation):
        try:
            if self.getConfig("rename") is not "":
                new = UserString(self.logDebug_)
                name = new.processMovie(self.getConfig("rename"), movie_title, movie_name, punctuation, movie_year)
                return name
            else:
                return "" #no impact on os.path.join()
        except AttributeError, ea:
            if ea.args[0] == "'%title' element was not provided!":
                self.logWarning(ea.args[0] + " Skipping renaming.")
                return movie_name
            

    def __setDestination(self, movie_obj):
        
        if self.getConfig("rename_options") == 'File only':
            return #set that earlier; no need to re-adjust that here
        elif self.getConfig("rename_options") == 'File and Folder' \
        and self.getConfig("subfolder") is True: 
            movie_obj.folder_name = self.__cutFile(movie_obj.file_name, False)
            return
        elif self.getConfig("rename_options") == 'Folder only' \
        and self.getConfig("subfolder") is True: 
            movie_obj.folder_name = self.__cutFile(movie_obj.file_name, False)
            movie_obj.file_name = os.path.split(movie_obj.source)[1]
            return
        else:
            movie_obj.file_name = os.path.split(movie_obj.source)[1]
            if self.getConfig("subfolder") is True:
                movie_obj.folder_name = self.__cutFile(movie_obj.file_name, False) 
            return #use src_filename as dst_filename 
        
    
    def _startMovingThreads(self, movies):
        if movies != None:
            for movie in movies:
                put = Thread(target=self.__putMvQueue, args=(movie,))
                put.setDaemon(True)
                put.start()
                get = Thread(target=self.__getMvQueue)
                get.setDaemon(True)
                get.start()
            return True
        else:
            return False
        
    
    def __putMvQueue(self, movie):
        self.__movie_queue.put(movie)
    
    
    def __getMvQueue(self):
        movie = self.__movie_queue.get()
        self.__setDestination(movie)
        dst = movie.destination
        src = movie.source
        if os.path.exists(src) and os.path.exists(dst):
            self.__moveMovie(src, dst, movie.folder_name, movie.file_name)
        else:
            self.__movie_queue.task_done()
              
              
    def __moveMovie(self, src, dst, folder, file_name):
        try:
            file_name = save_path(file_name)
            if self.getConfig("subfolder") is True:
                dst = os.path.join(dst,folder)
                os.mkdir(Utils(self.logDebug_).encode(dst))
        except OSError, e:
            if e.args[0] == 17:
                self.logDebug(u'Cannot create folder "%s". It already exists.' % os.path.join(dst))
        try:
            full_dst = Utils(self.logDebug_).encode(os.path.join(dst,file_name))
            if os.path.exists(full_dst):
                pass
            shutil.move(src, full_dst)
            self.logInfo(u'Movie "%s" moved to "%s"' % (os.path.split(src)[1], os.path.join(dst,file_name)))
            self.__movie_queue.task_done()
        except OSError, e:
            if e.args[0] == 21:
                self.logDebug(u'Cannot move "%s" to "%s". "%s" is a directory.' % (os.path.split(src)[1],
                                                                                   os.path.join(dst, file_name),
                                                                                   os.path.join(dst, file_name)))
                self.__movie_queue.task_done()
                
                   
                
    def logDebug_(self):
        
        traceback_template = '''Traceback (most recent call last):
          File "%(filename)s", line %(lineno)s, in %(name)s
        %(type)s: %(message)s\n'''
        
        exc_type, exc_value, exc_traceback = sys.exc_info()
        
        traceback_details = {
                             'filename': exc_traceback.tb_frame.f_code.co_filename,
                             'lineno'  : exc_traceback.tb_lineno,
                             'name'    : exc_traceback.tb_frame.f_code.co_name,
                             'type'    : exc_type.__name__,
                             'message' : exc_value.message, # or see traceback._some_str()
                            }
        
        self.logDebug(traceback_template % traceback_details)
                
            
    
        


class Query:
    
    
    def __init__(self, path_to_common_occurences, language, logger, query_num=10):
        self.config = {}
        self.config["occurrences"] = self.__loadOccurences(path_to_common_occurences)
        self.__loadStdOccurrences()
        self.config["host"] = 'http://api.themoviedb.org/3/'
        self.config["api"] = 'search/movie?'
        self.config["api_titles"] = 'movie/%(ID)s/alternative_titles?'  
        self.config["api_key"] = u"27551137b83f1a8775a41e91e8d68b0d"
        self.config["selected_language"] = language
        self.config['valid_languages'] = self.__init_languages()
        self.config['movie_year'] = None 
        self.query_queue = Queue(query_num)
        self.combines = None # all possible combinations
        self.__movies = None
        self.__movies_lock = RLock()
        self.logDebug = logger
        
    
    
    def __init_languages(self):
        return {
                "Danish":"da", "Finnish":"fi", "Dutch":"nl", "German":"de", "Italian":"it",
                "Spanish":"es", "French":"fr", "Polish":"pl", "Hungarian":"hu", "Greek":"el",
                "Turkish":"tr","Russian":"ru", "Hebrew":"he", "Japanese":"ja", "Portuguese":"pt", "Chinese":"zh",
                "Czech":"cs", "Slovene":"sl", "Croatian":"hr", "Korean":"ko", "English":"en", "Swedish":"sv",
                "Norwegian":"no"
                }
        
        
    def __get_language(self, iso_3166_1): #
        """Maps ISO 3166-1 to ISO 639-1 "Language name" which should be accurate for the most part"""
#        langs = { # this actually is the wrong ISO code but keep it for some other occasion maybe ?!
#                "en":"English", "da":"Danish", "fi":"Finnish", "de":"German", "it":"Italian", 
#                "es":"Spanish", "fr":"French", "pl":"Polish", "hu":"Hungarian", "el":"Greek",
#                "tr":"Turkish", "ru":"Russian", "he":"Hebrew", "ja":"Japanese", "pt":"Portugese",
#                "zh":"Chinese", "cs":"Czech", "sl":"Slovene", "hr":"Croatian", "ko":"Korean",
#                "sv":"Swedish", "no":"Norwegian" 
#                }
        langs = {
                 "US":"English", "GB":"English", "DE":"German", "DK":"Danish", "FI":"Finnish",
                 "NL":"Dutch", "IT":"Italian", "ES":"Spanish", "FR":"French", "PL":"Polish", "HU":"Hungarian",
                 "GR":"Greek", "TR":"Turkish", "RU":"Russian", "IL":"Hebrew", "JP":"Japanese", "PT":"Portugese",
                 "CN":"Chinese", "CZ":"Czech", "SI":"Slovene", "HR":"Croatian", "KR":"Korean", "SE":"Swedish",
                 "NO":"Norwegian"
                }
        if langs.has_key(iso_3166_1):
            return langs[iso_3166_1]
        else:
            return None
        
    def __map_iso_31661_6391(self, iso_3166_1):
        # US -> en
        # DE -> de
        # DE -> German -> de
        return self.config['valid_languages'][self.__get_language(iso_3166_1)]
    
    
    def __loadOccurences(self, path_to_file):
            if os.path.exists(path_to_file):
                o = []
                try:
                    for line in open(path_to_file,'r+'):
                        if re.search("\n", line) is False:
                            raise TypeError('"%s" is not a text file' % os.path.split(path_to_file)[1])
                        line = line[:len(line) - 1]
                        if len(line) > 2:
                            o.append(line.lower()) #remove \n at the end of line
                    return o
                except TypeError, t:
                    print t
                    return None
                except Exception, e:
                    print e # do something!
            else:
                return None
    
    def __loadStdOccurrences(self):
        """Add occurrences here you feel have no business at all in being used for querying."""
        if self.config["occurrences"] == None:
            self.config["occurrences"] = []
        for o in [
                 '720p',
                 '1080p',
                 'DTS5.1',
                 'DTS',
                 'AC3',
                 'German',
                 'English',
                            #your occurrence here!
                 ]:
            if self.config["occurrences"].count(o.lower()) == 0:
                self.config["occurrences"].append(o.lower())
    
    
    def query(self, file_name, year=None, isFile=True):
        try:
            self.__reset()
            return self._query(file_name, year, isFile)
        except Exception, e:
            self.logDebug()
            raise
        except BaseException, be:
            self.logDebug()
            raise
    
    
    def _query(self, file_name, year, isFile):
        """If nothing was found returns None"""
        self.config['movie_year'] = year
        self._prepareQuery(file_name, year, isFile)
        self._start_threads(self.combines["queries"])
        self.query_queue.join() # halt main thread and wait for completion
        if self.__movies is None or \
        len(self.__movies) == 0:
            return None
        self._start_Alt_Title_Search()
        self.query_queue.join() # halt main thread and wait for completion
        self._matchResults()
        if isFile is True:
            file_name = self.__cutExtension(file_name)
        fnl_rslt = self._validateNameResult(file_name)
        return self.__checkFinalResult(fnl_rslt)


    def _prepareQuery(self, file_name, year, isFile):
        file_name = Utils(self.logDebug).encode(file_name)
        if isFile is True:
            file_name = self.__cutExtension(file_name)
        if self.config["occurrences"] != None:  #remove common occurrences from file_name
            for o in self.config["occurrences"]:
                o = o.replace(".", "\\.")
                p = re.compile("((\\s+)|(\\.+)|(-+)|(_+)|(^))(" + o + ")((\\s+)|(\\.+)|(-+)|(_+)|($))", re.IGNORECASE)
                file_name = re.sub(p," ", file_name)
        file_name = self.__strip(file_name).strip()
        q = re.split(('\\s|\\.|-|_'), file_name)
        self.combines = {} # declare and initialize combinations
        self.combines["amount"] = 0
        num = 0
        if year != None:
            # 1st Query
            num += 1
            q.remove(year)
            self.combines["amount"] = num 
            self.combines[num] = {}
            self.combines[num]["query"] = self._generateCombinations(q)
            self.combines[num]["year"] = year
            # 2nd Query
            num += 1
            q.append(year)
            self.combines["amount"] = num 
            self.combines[num] = {}
            self.combines[num]["query"] = self._generateCombinations(q)
            self.combines[num]["year"] = None
            # 3nd Query
            num += 1
            q.remove(year)
            self.combines["amount"] = num 
            self.combines[num] = {}
            self.combines[num]["query"] = self._generateCombinations(q)
            self.combines[num]["year"] = None
        if year == None:
            num += 1
            self.combines["amount"] = num 
            self.combines[num] = {}
            self.combines[num]["query"] = self._generateCombinations(q)
            self.combines[num]["year"] = None
        self.__finalizeQuery(self.combines)
        return self.combines


    #deprecated pending removal
    def _prepareGeneration(self, file_name, remove_file_yr): # cleaning
        if len(file_name) == file_name.rfind('.') + 4:
            file_name = file_name[:file_name.rfind('.')]
        if self.config["occurrences"] != None:
            for o in self.config["occurrences"]:
                o = o.replace(".", "\\.")
                p = re.compile("((\\.+)|(-+)|(_+)|(^))(" + o + ")((\\.+)|(-+)|(_+)|($))", re.IGNORECASE)
                file_name = re.sub(p," ", file_name)
        file_name = self.__strip(file_name).strip()
        elem_lst = re.split(('\\s|\\.|-|_'), file_name)
        if self.config['movie_year'] != None and \
        remove_file_yr is True:
            try:
                elem_lst.remove(self.config['movie_year'])
            except ValueError("No element %s in list"):
                pass
        for tgt in elem_lst: 
            if len(tgt) < 3 and \
            re.match('(\d{1,2})|(I){1,2}|(IV)|(V)|(VI)|(IX)|(X)', tgt, re.IGNORECASE) == None: # don't remove latin 2-digit/ roman numeral between 1-10
                elem_lst.remove(tgt) # remove elements that are shorter than 3 chars
        return elem_lst            
    

    def _generateCombinations(self, list_of_elements):
        result = self._unpackAltCombinations(self.__alt_combine(list_of_elements))[:]
        return result

    
    def __alt_combine(self,list_of_elements):
        result = []
        ingoing_list = list_of_elements[:]
        for elem in list_of_elements:
            self.__start_alt_combine(ingoing_list[:], result)
            ingoing_list.remove(elem)
        return result
    
    
    def __start_alt_combine(self, remainder, result): 
        result.append(tuple(remainder))
        remainder.pop(len(remainder) - 1)
        if len(remainder) == 0:
            return
        self.__start_alt_combine(remainder, result)


    def _unpackAltCombinations(self,list_of_tuples):
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

    def __finalizeQuery(self, prelim_query):
        prelim_query['queries'] = []
        for num in range(1,prelim_query["amount"]+1):
            year = prelim_query[num]["year"]
            for q in prelim_query[num]["query"]:
                prelim_query['queries'].append((q, year))
                
         





    def _start_threads(self, query_list):
        for query in query_list:
            addToQueue = Thread(target=self.__add_to_queue_sendRequest, args=(query,))
            addToQueue.setDaemon(True)
            addToQueue.start()
        for i in range (len(query_list)): # number of queries to process
            getFromQueue = Thread(target=self.__get_from_queue_searchMovie)
            getFromQueue.setDaemon(True)
            getFromQueue.start()    
    

    def __add_to_queue_sendRequest(self, single_combination):
        self.query_queue.put(single_combination)
    
    
    def __get_from_queue_searchMovie(self):
        single_combination = self.query_queue.get()
        self.__searchMovie(single_combination)
        self.query_queue.task_done()
        
        
    def _start_Alt_Title_Search(self):
        for movie_id in self.__movies:
            put = Thread(target=self.__add_to_queue_MovieID, args=(movie_id,))
            put.setDaemon(True)
            put.start()
        for i in range(len(self.__movies)):
            get = Thread(target=self.__get_from_queue_MovieID)
            get.setDaemon(True)
            get.start()
        
        
    def __add_to_queue_MovieID(self, movie_id):
        self.query_queue.put(movie_id) 
        
        
    def __get_from_queue_MovieID(self):
        movie_id = self.query_queue.get()
        self.__searchTitles(movie_id)
        self.query_queue.task_done()   
    
       
    def __searchMovie(self, single_combination):
            '''sends actual queries and calls _analyzeResponse'''
            data = self.__setData(single_combination)
            url_ = self.config["host"] + self.config["api"] + data
            request = urllib2.Request(url_)
            request.add_header('Accept', 'application/json')
            try:
                connection = None
                connection = urllib2.urlopen(request)
            except HTTPError, e:
                if len(e.args) > 0:
                    if e.args[0] == "HTTP Error 503: Service Unavailable":
                        time.sleep(10)
                        connection = urllib2.urlopen(request)
                else:
                    return None
            except URLError, ue:
                if ue.args[0] == "<urlopen error [Errno -2] Name or service not known>":
                        time.sleep(10)
                        connection = urllib2.urlopen(request)
            if connection is None:
                    try:
                        raise EnvironmentError("Missing response")
                    except EnvironmentError, ee:
                        if ee.args[0] == "Missing response":
                            time.sleep(10)
                            self.__searchMovie(single_combination)
                            return
            resp = connection.read()
            self.__analyzeResponse(resp)


    def __analyzeResponse(self, response):
        response = Utils(self.logDebug).decode(response)
        r = json_loads(response)
        if r['total_results'] > 0:
            self.__movies_lock.acquire()
            for result in r['results']:
                if result is not None:  
                    self.__addMovie(result)
            self.__movies_lock.release()
            return True
            
        
    def __addMovie(self, result):
        if self.__movies is None:
            self.__movies = {}
        self.__movies[result["id"]] = {} 
        self.__movies[result["id"]]["title"] = {}
        self.__movies[result["id"]]["year"] = {}
        self.__movies[result["id"]]["title"]['original'] = [] 
        self.__movies[result["id"]]["title"]['original'].append(result["original_title"])

        if len(result["title"]) > 0:
            self.__movies[result["id"]]["title"]['standard'] = [] 
            self.__movies[result["id"]]["title"]['standard'].append(result["title"])
            title = self.__convert(result["title"], self.config['selected_language'])
            if title != result['title']:
                self.__movies[result["id"]]["title"]['standard'].append(title)
        self.__movies[result["id"]]["year"] = result["release_date"]
        

    def __searchTitles(self, movie_id):
            '''Retrieves all alternative titles for a movie based on its TmDB movie ID'''
            data = urlencode({'api_key' : self.config["api_key"]})
            api = self.config["api_titles"] % {"ID" : movie_id}
            url_ = self.config["host"] + api + data
            request = urllib2.Request(url_)
            request.add_header('Accept', 'application/json')
            try:
                connection = urllib2.urlopen(request)
            except HTTPError, e:
                if len(e.args) > 0:
                    if e.args[0] == u"HTTP Error 503: Service Unavailable":
                        time.sleep(10)
                        connection = urllib2.urlopen(request)
                else:
                    return None
            except URLError, ue:
                if len(ue.args) > 0 and \
                ue.args[0] == u'<urlopen error [Errno 104] Connection reset by peer>':
                    time.sleep(10)
                    connection = urllib2.urlopen(request)
                elif ue.args[0] == "<urlopen error [Errno -2] Name or service not known>":
                    time.sleep(10)
                    connection = urllib2.urlopen(request)
                    
                else:
                    return None
            resp = connection.read()
            self.__addTitles(resp)
            
            
    def __addTitles(self, response):
        response = Utils(self.logDebug).decode(response)
        r = json_loads(response)
        ID = r["id"]
        if len(r["titles"]) > 0:
            self.__movies_lock.acquire()
            for title in r["titles"]:
                if self.__movies[ID]["title"].has_key(self.__get_language(title["iso_3166_1"])) is False:
                    self.__movies[ID]["title"][self.__get_language(title["iso_3166_1"])] = []
                self.__movies[ID]["title"][self.__get_language(title["iso_3166_1"])].append(title["title"])
                c_title = self.__convert(title["title"], self.__get_language(title["iso_3166_1"]))
                if c_title != title:
                    self.__movies[ID]["title"][self.__get_language(title["iso_3166_1"])].append(c_title)
            self.__movies_lock.release()
        

    def _matchResults(self):
        '''Checks every local combination against every retrieved/acquired movie title
        
        This is a good way to remove utterly impossible matches:
        A response may consist of more word than what was initially conveyed (children -> Children of Men)
        Now in order to discard of those a pattern using each local combination is checked against all results. 
        To avoid redundancies a set is returned 
        including possible matches using remotely acquired names
        '''
        IDs = []
        for comb in self.combines["queries"]:
            if True:
#            if not comb.find(" ") == -1: # single word 
                p = re.compile(self.__generatePattern(comb[0]), re.IGNORECASE) # use local combination as pattern
                for id in self.__movies.keys():
                    for language in self.__movies[id]["title"]:
                        for title in self.__movies[id]["title"][language]:
                            match_ = p.search(self.__strip(title)) #match against remote results
                            if match_:
                                IDs.append(id)
#            else:
#                for id in self.__movies:
#                    for language in self.__movies[id]["title"]:
#                        for title in self.__movies[id]["title"][language]:
#                            if comb.lower() == self.__strip(title.lower()): #compare single word
#                                IDs.append(id)
        IDs = list(set(IDs))
        for id in self.__movies.keys():
            if IDs.count(id) == 0:
                self.__movies.pop(id)


    def _validateNameResult(self, movie_name):
        '''Tries to validate acquired movie titles by checking them against the local movie __name in question.
        
        For this a pattern on basis of the acquired movie titles/ remote self.__movies is being generated and
        checked against our actual episode __name. 
        Only the longest match in terms of len(match) is being returned with the assumption that this must
        be our wanted show name. Other matches might be false positives.
        In case match has less than 3 chars it will be discarded to avoid false positives.
        '''
        if len(self.__movies) == 0:
            return None
        
        matches = ""
        match_id = -1
        for id in self.__movies:
            for language in self.__movies[id]["title"]:
                for title in self.__movies[id]["title"][language]:
                    try:
                        p = re.compile(self.__generatePattern(self.__strip(title),False,True), re.IGNORECASE)
                        match_ = p.search(self.__strip(movie_name))
                        if match_:
                            if len(matches) < len(match_.group(7)): #crucial!:
                                match_id = id
                                matches = match_.group(7)
                    except Exception, e:
                        if e.args[0] == "nothing to repeat":
                            pass
                        else:
                            raise                        
        if len(matches) > 2:
            if self.config['movie_year'] != None:
                match_id = self._dateValidation(matches, match_id, self.config['movie_year'])
            return self.__movies[match_id]
        return None
            
    
    def _dateValidation(self, matched_title, match_id, given_release_yr):
        """On existence of multiple identical titles try to narrow them further down by release year"""
        
        c = Utils(self.logDebug)
        id_list = []
        # find matching titles and add to list
        for id in self.__movies:
            for language in self.__movies[id]['title']:
                for title in self.__movies[id]['title'][language]:
#                    p = re.compile(self.__generatePattern(self.__strip(title),False,True), re.IGNORECASE)
#                    match_ = p.search(self.__strip(matched_title))
                    if c.stripclean(title) == c.stripclean(matched_title) \
                    and id != match_id:
                        id_list.append(id)
        id_list = list(set(id_list))
        id_list.append(match_id)
        if len(id_list) == 1:
            return match_id
        else:
            # compare release year and return first match
            for id in id_list:
                if int(given_release_yr) == int(c.cut(self.__movies[id]['year'], '-')):
                    return id
            return match_id
        


    
    def __setData(self, data_tuple):
        query, year = data_tuple
        query = query.decode("utf-8")
        query = query.encode("utf-8")
        if year != None:
            data = urlencode({
                              'api_key' : self.config["api_key"],
                              'query' : query.replace(" ","%20"),
                              'language' : self.config["valid_languages"][self.config["selected_language"]],
                              'year' : year
                            })
        else:
            data = urlencode({
                              'api_key' : self.config["api_key"],
                              'query' : query.replace(" ","%20"),
                              'language' : self.config["valid_languages"][self.config["selected_language"]],
                            })
        return data
        
    
    
    def __generatePattern(self,
                          a_ws_sep_combination,
                          rightAnchored=True,
                          puncuated=False):
        pattern = ''
        for strg in a_ws_sep_combination.split():
            pattern += strg + '.'
        pattern = pattern[:pattern.rfind('.')]
        if rightAnchored:
            pattern = '(' + pattern[:] + ')$'
            return pattern
        else:
            pattern = '(' + pattern[:] + ')'
        if puncuated is True:
            pa = "((\\s+)|(-+)|(_+)|(\\.+)|(^))"
            pe = "((\\s+)|(-+)|(_+)|(\\.+)|($))"
            pattern = pa + pattern + pe
        return pattern
    
    
    def __convert(self, movie_title, language):
        """Special conversions you want to do yourself you can do here
        
        Every language listed in config['valid_languages'] is passed through here
        """
        if self.config['valid_languages'].has_key(language):
            if language == 'German': #conversions for German Umlauts like so: u'ö' -> u'oe'
                c = Umlaute(self.logDebug)
                new = c.convertString(movie_title, 'utf8')
                if new != movie_title:
                    return new
        return movie_title
    
    
    def __strip(self, result):
        result = re.sub("(\\.+)|(-+)|(_+)|(:+)|(!+)|(\\?+)", " ", result)
        result = re.sub("(\\s+)", " ", result)
        return result

    def __cutExtension(self, file_name):
            return file_name[:file_name.rfind('.')] #remove extensions
        

    def __reset(self):
        if self.__movies != None or \
        self.combines != None:
            self.__movies = None
            self.combines = None
    
    
    def __checkFinalResult(self, retVal):
        """Checks results for a existing title as well as a release year"""
        if retVal != None:
            if len(retVal["title"]['original']) > 0 and retVal["year"] != None:
                return retVal
        return None
            
    


class Movie:
    
    def __init__(self, title='', source='', destination='', file_name=''):
        self.title = title #the actual offical title
        self.source = source #the full path to the movie file
        self.src_folder = self.__src_folder(source) 
        self.destination = destination #destination path for the movie file
        self.folder_name = self.__setFolder_Name(source) #a possible subfolder
        self.file_name = file_name #destination file name
        
    def __setFolder_Name(self, src_path):
        bn, folder = os.path.split(src_path)
        return folder[:folder.rfind('.')]
    
    def __src_folder(self, source):
        return os.path.split(os.path.split(source)[0])[1]
    
  
    
class UserString:

   
    def __init__(self, logger):
        self.__title = None
        self.__year = None
        self.__usr_elems = []
        self.logDebug = logger
    
    
    def processMovie(self, user_string, movie_title, movie_name, punc, movie_year=None):
        '''Constructs a new name for a provided movie based on user_string.
        
        Raises AttributeError if '%title' element is missing.
        '''
        try:
            return self._processMovie(user_string, movie_title, movie_name, punc, movie_year)
        except AttributeError, ae:
            if ae.args[0] == "'%title' element was not provided!":
                self.logDebug()
                raise
        except Exception, e:
            self.logDebug()
            raise
        except BaseException, be:
            self.logDebug()
            raise
            
            
        
    
    def _processMovie(self, user_string, movie_title, movie_name, punc, movie_year):
        self.__parseUserString(user_string)
        self.__parseMovieName(movie_title, movie_year, movie_name)
        return self.__constructName(punc) + self.__getExtension(movie_name)


    def __parseUserString(self, user_string):
        self.__parseTitleElem(user_string)
        self.__parseYearElem(user_string)
        self.__parseUserElems(user_string)
    
    
    def __parseMovieName(self, movie_title, movie_year, movie_name):
        self.__setTitle(movie_title)
        self.__setYear(movie_year)
        self.__setUsrElements(self.__cutExtension(movie_name))
     
     
    def __constructName(self, punc='.'):
        name = ""
        
        self.__title.convertTitle(punc)
        for e in self.__getAllElements():
            name += e.getValue() + punc
        name = name[:name.rfind(punc)]
        return name
        
    def __getExtension(self, movie_name):
        return movie_name[movie_name.rfind('.'):]
    
    def __cutExtension(self, movie_name):
        return movie_name[:movie_name.rfind('.')]
    
    def __setTitle(self, movie_title):
        self.__title.setTitle(movie_title)


    def __setYear(self, movie_year):
        if movie_year is not None and self.__year is not None:
            self.__year.setYear(movie_year)

    
    def __setUsrElements(self, movie_name):
        for e in self.__usr_elems:
            e.setValue(movie_name) 


    def __parseTitleElem(self, user_string):
        title = '%title'
        
        match_ = re.search("(" + title + ")", user_string)
        if match_ is not None:
            pos = self.__getElemPos(user_string, title)
            self.__title = TitleElement(pos)
        else:
            raise AttributeError("'%title' element was not provided!")
                
                
    def __parseYearElem(self, user_string):
        year = '%year'
        try:
            if re.search('(' + year + ')', user_string).groups() is not None:
                pos = self.__getElemPos(user_string, year)
                self.__year = YearElement(pos)
            else:
                self.__year = None
        except AttributeError, e:
            self.__year = None
  
    
    def __parseUserElems(self, user_string):
        matches = re.findall("(%[A-z]+=)(([A-z_0-9\\-\\.]\\|?)+)", user_string)
        for match in matches:
            self.__addUserElement(self.__getElemPos(user_string, match[0]), self.__getUsrElemTags(match[1]))
        
    
    def __getUsrElemTags(self, tags):
        t = tags.split('|')
        for e in t:
            e.replace(".", "\\.")
        try:
            t.remove("")
        except ValueError, e:
            pass # "" does not exist which is fine
        return t
    
    
    def __getElemPos(self, user_string, elem):
        return user_string.find(elem)


    def __addUserElement(self, position, tags):
        self.__usr_elems.append(UserElement(position, tags))

    
    def __getAllElements(self):
        e = []
        e.append(self.__title)
        if self.__year is not None:
            e.append(self.__year)
        for usr_e in self.__usr_elems:
            if usr_e.getValue() is not None:
                e.append(usr_e)
        return self.__sortElements(e)

    
    def __sortElements(self, elements):
        elements.sort(key=lambda elements: elements.getPosition())
        return elements


        
class BaseElement(object):
    
    def __init__(self, position):
        self.__position = position
        
    
    def getPosition(self):
        return self.__position
    
    
    def getElement(self):
        return self.__toDict()
    
    
    def setValue(self, value):
        self.__value = value
        
        
    def getValue(self):
        return self.__value
    
    
    def __toDict(self):
        return {"position": self.__position, }


class TitleElement(BaseElement):
    
    def __init__(self, position):
        super(TitleElement, self).__init__(position)
    
    def setTitle(self, title):
        self.__title = title
        
    def getValue(self):
        return self.__title
    
    def convertTitle(self,puncutation):
        self.__title = self.__title.replace(" ", puncutation)
    
    def __toDict(self):
        d = BaseElement.__toDict(self)
        d["title"] = self.__title
        return d
    
    
        
class YearElement(BaseElement):

    def __init__(self, position):
        super(YearElement, self).__init__(position)
            
    def setYear(self, year):
        if self.__validYear(year):
            self.__year = year
        else:
            self.__year = None
            
            
    def getValue(self):
        return self.__year
    
    
        
    def __validYear(self, year):
        yr_digit = (str)(datetime.today().year)[3]
        if re.search("([1][9][2-9][0-9])|([2][0][0][0-9])|([2][0][1][0-"+ yr_digit +"])", year):
            return True
        else:
            try:
                raise ValueError('"%s" is not a valid date. Allowed range is from 1920 to "%s" with format yyyy' % (year, datetime.today().year))
                return False
            except ValueError,e:
                print e
                return False
                
    
    def __toDict(self):
        d = BaseElement.__toDict(self)
        d["year"] = self.__year
        return d            
            

class UserElement(BaseElement):
    
    def __init__(self, position, tags):
        super(UserElement, self).__init__(position)
        self.__tags = tags # ["tag1","tag2","tagN"]
        
        
    def __toDict(self):
        d = BaseElement.__toDict(self)
        d = super(UserElement,self).__toDict()
        d["tags"] = self.__tags
        return d
    
    
    def setValue(self, movie_name):
        value = self.__setValue(self.__tags, movie_name)
        super(UserElement, self).setValue(value)
        
    
    def __setValue(self, tags, movie_name):
        for tag in tags:
            try:
                if re.search("((\\.)|(_)|(-)|(^))(" + tag + ")((\\.)|(_)|(-)|($))", movie_name).group(1) is not None:
                    return tag
            except AttributeError, e:
                pass #no match!


class Utils:
    
    def __init__(self, logger):
        self.logDebug = logger
    
    def encode(self, string): # on the way out
#        return string.encode("utf_8", 'ignore')
        try:
            return fs_encode(string)
        except Exception, e:
            self.logDebug()
            raise
        except BaseException, be:
            self.logDebug()
            raise
    
    def decode(self, string): # on the way in 
        try:
            return self.encode(string).decode("utf-8", 'ignore')
        except UnicodeDecodeError, ude:
            return string
        except UnicodeEncodeError, uee:
            return string
        except Exception, e:
            self.logDebug()
            raise
        except BaseException, be:
            self.logDebug()
            raise
        
        
    def cut(self, string, char, fromLeft=True):
        if fromLeft == True:
            return string[:string.find(char)]
        else:
            return string[string.find(char)+1:]

    
    def stripclean(self, cleanee):
        # remove chars such as ':','-',''
        cleanee = re.sub("(:+)|(_+)|(-+)|(\\.+)|(\\))|(\\()"," ", cleanee)
        cleanee = re.sub("(\\s+)"," ", cleanee)
        cleanee = cleanee.strip()
        cleanee = self.clean_apostrophe(cleanee)
        return cleanee
        
    
    def clean_apostrophe(self, cleanee):
        """Clean any apostrophes(') followed by (s )"""
        if cleanee.find("'s ") != -1:     
            cleanee = re.sub("'s\\s", "s ", cleanee)
        if re.search("('s$)", cleanee, re.IGNORECASE) != None:
            cleanee = re.sub("'s$", "s", cleanee)
        return cleanee 
        
        
class Transcoder:
    
    def __init__(self, logger):
        self.logDebug = logger
        
    def encode(self, output):
        try:
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
        except Exception, e:
            self.logDebug
            raise
        except BaseException, e:
            self.logDebug
            raise
            
        
    def decode(self, input):
        try:
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
        except Exception, e:
            self.logDebug
            raise
        except BaseException, be:
            self.logDebug
            raise
        
    
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
    
        
class Umlaute:
    
    def __init__(self, logger):
        self.umlaute = {}
        self.umlaute['codecs'] = ['utf8', 'ascii']
        self.umlaute['utf8'] = self.__init_utf8_ascii_mapping()
        self.umlaute['ascii'] = self.__init_ascii_utf8_mapping()
        self.logDebug = logger
        
    def __init_utf8_ascii_mapping(self):
        return {
                u'ü':u'ue',
                u'ä':u'ae',
                u'ö':u'oe',
                u'ß':u'ss',
               }
        
    def __init_ascii_utf8_mapping(self):
        return {
               u'ue':u'ü',
               u'ae':u'ä',
               u'oe':u'ö',
               u'ss':u'ß', 
               }
        
        
    def _getASCII(self, unicode_char):
        """Attempts to return an ASCII-encoded German Umlaut by its UTF8-encoded pendant"""
        if self.umlaute['utf8'].has_key(unicode_char.lower()):
            return self.umlaute['utf8'][unicode_char.lower()]
        else:
            return None
        
        
    def _getUTF8(self, ascii_encoded_utf8_char):
        """Attempts to return an UTF8-encoded German Umlaut by its ASCII-encoded pendant"""
        ascii = ascii_encoded_utf8_char
        if self.umlaute['ascii'].has_key(ascii):
            return self.umlaute['ascii'][ascii]
        else:
            return None
        
    
    def get(self, unknown_char):
        """In case the encoding is unknown this tries both ASCII as well as UTF8 
        
        If its ASCII-encoded UTF8 is returned.
        If its UTF8-encoded ASCII is returned.
        If its neither None is returned.
        """
        try:
            x = self._getASCII(unknown_char)
            if x != None:
                return x
            else:
                x = self._getUTF8(unknown_char)
                if x != None:
                    return x
                else:
                    return None
        except Exception, e:
            self.logDebug
            raise
        except BaseException, be:
            self.logDebug
            raise
            
            
    def convertString(self, string, encoding):
        try:
            if self.umlaute['codecs'].count(encoding) == 0: # wrong codec supplied
                return None
            for umlaut in self.umlaute[encoding]:
                p = re.compile('('+ umlaut +')', re.IGNORECASE)
                string = re.sub(p, self.umlaute[encoding][umlaut], string)
            return string
        except Exception, e:
            self.logDebug
            raise
        except BaseException, be:
            self.logDebug
            raise
        