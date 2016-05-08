# -*- coding: utf-8 -*-

import re
import time

from module.network.HTTPRequest import BadHeader
from module.plugins.internal.Hoster import Hoster

class ClicknUpload(Hoster):
    __name__ = "ClicknUpload"
    __type__ = "hoster"
    __version__ = "0.02"
    __status__  = "testing"

    __pattern__ = r'http://(?:www\.)?clicknupload\.(?:com|me|link)/\w{12}'

    __description__ = """Clicknupload.com hoster plugin"""
    __authors__ = [("tbsn", "tbsnpy_github@gmx.de")]

    __config__  = [("activated"   , "bool", "Activated"                                        , True),
                   ("use_premium" , "bool", "Use premium account if available"                 , False)]

    __license__     = "GPLv3"

    BADHEADER_PATTERN = r'Refresh: (?P<refresh_timeout>\w+);URL=(?P<refresh_link>\S+)'
    DIRECTLINK_PATTERN = r'<a (href="javascript:void\(0\);")? onClick="window.open\(\'(?P<direct_link>\S+)\'\);"'
    
    """
    @function processBadHeader()
    Extract self.refreshTimeout and self.refreshLink from BadHeader 503
    """
    def processBadHeader(self, e):
        
        retVal = -1
        
        self.log_debug("Received Header Code: %i" % e.code)
            
        if( 503 == e.code ):
            m = re.search(ClicknUpload.BADHEADER_PATTERN, self.req.http.header)
            if( None == m ):
                self.log_debug("Refresh pattern not found")
            else:
                self.refreshTimeout = int(m.group('refresh_timeout'))
                self.refreshLink = m.group('refresh_link')
                self.log_debug("Timeout: %s, Link %s" % (self.refreshTimeout,self.refreshLink))
                retVal = 0
                
        return retVal
    
    """
    @function
    Load refresh site that was extracted from the first BadHeader 503
    Reset self.refreshTimeout to 0, when page was loaded successfully
    """
    def handleForTempUnavailPage(self):
        
        retVal = 0
        
        refreshLinkComplete = "http://clicknupload.link" + self.refreshLink
        
        self.log_debug("Wait for %i seconds" % (self.refreshTimeout+1) )
        time.sleep(self.refreshTimeout+1)
        self.log_debug("Waiting done. Load \"%s\"" % refreshLinkComplete )
        
        
        try:
            refreshPage = self.load( refreshLinkComplete , just_header=True )
            self.log_debug("Refresh page loaded")
            self.refreshTimeout = 0
            
            
        except BadHeader, e:
            retVal = self.processBadHeader(e)
        
        return retVal
    
    """
    @function extendPostList() 
    Searches for <input...> fields whose name attribute matches the passed
    variable inputName and extract the corresponding value attribute
    Valid name/value pairs are added to the given post dict
    """
    def extendPostList(self, html, post, inputName, allowedValueList=None):
        
        retVal = 0
        postVal = None
        
        # Adapt regex to match only input fields whose name attribute is identical to 'inputName'
        inputPattern = r'<input type="hidden" name="'+inputName+r'" value="(?P<input_value>\S+)">'
        
        # Find all matching input fields in 'html'
        inputList = re.findall(inputPattern, html, re.MULTILINE )
                
        if( ( None == inputList ) | ( 0 == len(inputList) ) ):
            # No matches - return error
            retVal = -1
        elif( None == allowedValueList ):
            # All values allowed - return first match
            postVal = inputList[0]
        else:
            # Only given values allowed. Return the first allowed match
            for inputVal in inputList:
                if( inputVal in allowedValueList ):
                    postVal = inputVal
        
        # Append (name,value) pair of input field to given post dict
        if( None != postVal ):
            post[str(inputName)] = str(postVal)
            
    def handleDownloadPage(self, post=None ):
        retVal = 0
        downloadPage = ""
                
        # Try to load page with supplied 'post' parameters
        try:

            downloadPage = self.load( self.pyfile.url , post=post )
            
            if( "File Download Link Generated" in downloadPage ):
                m = re.search(ClicknUpload.DIRECTLINK_PATTERN, downloadPage )
                if( None != m ):
                    self.directLink = m.group('direct_link')
                                    
        except BadHeader, e:
            # A 503 code is expected the first time.
            badHeaderRetVal = self.processBadHeader(e)
            if( 0 == badHeaderRetVal ):
                retVal = 1
            else:
                retVal = -1
                
        # Assemble post parameters for next load
        if( ( 0 == retVal ) & ( None == self.directLink ) ):
            
            post = dict()
            
            self.extendPostList( downloadPage, post, "op" , allowedValueList=["download1","download2"])
            self.extendPostList( downloadPage, post, "id" )
            self.extendPostList( downloadPage, post, "fname" )
            self.extendPostList( downloadPage, post, "referer" )
            self.extendPostList( downloadPage, post, "rand" )

            post['method_free'] = "Free Download"
            post['usr_login'] = ""
            
            opVal = ""
            fnameVal = ""
            try:
                opVal = post['op']
                fnameVal = post['fname']
            except KeyError:
                pass
            
            # Wait for 6 seconds before pressing the second download button
            if( "download2" == opVal ):
                self.log_debug("Wait 6 seconds before proceeding")
                time.sleep(6)
                # Set referrer
                post['referer'] = self.pyfile.url
            
            # Store file name to pyfile object
            if( "" != fnameVal ):
                self.pyfile.name = fnameVal

        return retVal, post


    def process(self, pyfile):

        # refreshTimeout and refreshLink are set, when a BadHeader 503 temporary unavailable is read
        # This header is sent by Clicknupload, when a client without Javascript support is detected
        # The received BadHeader contains information, how long the client shall wait before loading
        # A supplied 'refresh' link.
        # refreshTimeout is set to 0, when this link was successfully loaded.
        self.refreshTimeout = 0
        self.refreshLink = ""
        
        # Variable to hold the extracted direct link
        self.directLink = None

        post = dict()
        
        retVal = 0
        retryCount = 0
        while( ( 0 <= retVal ) & ( None == self.directLink ) & ( 10 > retryCount ) ):
                        
            if( 0 != self.refreshTimeout ):
                # Load refresh link
                retVal = self.handleForTempUnavailPage()
            else:
                # Load download page
                retVal,post = self.handleDownloadPage(post)
                
            retryCount += 1
            
        # Check, if direct link was found and download it
        if( None != self.directLink ):
            self.log_info("Start download of file %s at URL %s" % (self.pyfile.name, self.directLink))
            self.download(self.directLink)
            
            
