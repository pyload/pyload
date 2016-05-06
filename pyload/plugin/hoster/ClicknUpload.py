# -*- coding: utf-8 -*-

# Regular expressions
import re



# Dom
import html5lib

# Sleep
import time

# None type
from types import NoneType

# Selenium
from selenium import webdriver
from selenium.webdriver.common.alert import Alert
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait # available since 2.4.0
from selenium.webdriver.support import expected_conditions as EC # available since 2.26.0
from selenium.common.exceptions import TimeoutException,NoSuchElementException,WebDriverException

from httplib import BadStatusLine

# Image cropping
from PIL import Image

# PyLoad imports
from module.plugins.Hoster import Hoster
#from module.plugins.internal.SimpleHoster import parseHtmlForm

#from module.plugins.internal.CaptchaService import SolveMedia

from xvfbwrapper import Xvfb

from selenium.webdriver.chrome.options import Options


def element_screenshot(driver, element, filename):
    bounding_box = (
        element.location['x'], # left
        element.location['y'], # upper
        (element.location['x'] + element.size['width']), # right
        (element.location['y'] + element.size['height']) # bottom
        )
    return bounding_box_screenshot(driver, bounding_box, filename)

def bounding_box_screenshot(driver, bounding_box, filename):
    driver.save_screenshot(filename)
    base_image = Image.open(filename)
    cropped_image = base_image.crop(bounding_box)
    base_image = base_image.resize(cropped_image.size)
    base_image.paste(cropped_image, (0, 0))
    base_image.save(filename)
    return base_image

class ClicknUpload(Hoster):
    __name__ = "ClicknUpload"
    __type__ = "hoster"
    __version__ = "0.01"

    __pattern__ = r'http://(?:www\.)?clicknupload\.(?:com|me|link)/\w{12}'

    __description__ = """Clicknupload.com hoster plugin"""
    __authors__ = [("tbsn", "kommaustash@gmx.net")]
    
    driver = None
    direct_link = None
    seconds_until_timeout = 15
        
    def setup(self):
        self.chunkLimit = 1
        self.resumeDownload = False
        self.download_id = re.search('(\w*$)', self.pyfile.url).group(0)
        self.last_download = ""

        #self.log.setLevel(logging.DEBUG)
        #self.debug = 1
        #self.use_firefox = True

    def process(self, pyfile):
        
        """main function"""
        self.logDebug("Enter. URL: %s DLID: %s" % (self.pyfile.url, self.download_id) )
        
        obtain_direct_link_ret_val = self.obtain_direct_link( )
        
        if ( 0 != obtain_direct_link_ret_val ) or ( None == self.direct_link ):
            self.logError("Failed to obtain direct link!")
            self.fail("Failed to obtain direct link: %i" % obtain_direct_link_ret_val)
        else:
            
            # Extract filename from direct link
            p = re.compile( '(.*/)' )
            self.pyfile.name = p.sub('', self.direct_link)
            # Start download
            self.logInfo("Start download of file %s at URL %s" % (self.pyfile.name, self.direct_link))
            self.download(self.direct_link)
        
    
    def locate_element_and_click( self , elem_type , elem_name, mustBeClicked ):

        elementLoc = None
        
        """Locate a element and click it. Returns 0 on success, a negative int otherwise"""
        try:
            #element = WebDriverWait(self.driver, self.seconds_until_timeout).until(EC.element_to_be_clickable((elem_type,elem_name)))
            elementLoc = WebDriverWait(self.driver, self.seconds_until_timeout).until(EC.element_to_be_clickable((elem_type,elem_name)))
        except TimeoutException:
            self.logError("Element %s not found" % (elem_name))
            return -1
        except WebDriverException:
            self.logError("WebDriverException!")
            return -1
        self.logDebug("Found element %s. Checking for visibility" % (elem_name))
        
        elementIsVisible = False
        try:
            elementIsVisible = elementLoc.is_displayed()
        except StaleElementReferenceException:
            self.logError("Element %s not valid" % (elem_name))
        
        if( False == elementIsVisible ):
            if( True == mustBeClicked ):
                self.logError("Found element %s not visible - Error" % (elem_name))
                return -2
            else:
                self.logInfo("Found element %s not visible - Ignore" % (elem_name))
                return -2
        #self.logDebug("Found element %s. Text: %s" % (elem_name,elementLoc.text))
            self.logDebug("Found element %s. Clicking it now" % (elem_name))
        self.driver.get_screenshot_as_file("/tmp/page_1.png")
        
        try: 
            elem_type = elementLoc.get_attribute("type")
            self.logDebug("Found attribute type: %s. " % (elem_type))
        except NoSuchElementException:
            self.logError("get_attribute failed")
            return -3    
        
        try:
            elementLoc.click()
        except NoSuchElementException:
            self.logError("Click of element %s failed: NoSuchElement" % (elem_name))
            return -3
        except BadStatusLine:
            self.logError("Click of element %s failed: BadStatusLine" % (elem_name))
            self.driver.get_screenshot_as_file("/tmp/page_1_2.png")
            return -4
        self.logDebug("Clicking %s successful" % (elem_name))
        return 0
    
    def handle_first_page( self ):
                
        retVal = 0
        self.logDebug("Enter handle_first_page. Load page %s" % (self.pyfile.url))
        self.driver.get(self.pyfile.url)
        
        # Locate and click button 'method_free'
        if( 0 != self.locate_element_and_click( By.NAME, 'method_free' , True) ):
            self.logError("Failed to locate 'method_free'")
            retVal = -1
        return retVal

    def handle_second_page( self ):
                    
        retVal = 0
        self.logDebug("handle_second_page(): Wait for element 'F1'")
        
        ##### Wait for element 'F1' ####
        try:
            element_f1 = WebDriverWait(self.driver, self.seconds_until_timeout).until(EC.visibility_of_element_located((By.NAME, 'F1' )))
            
            self.logDebug("Found F1")
        except TimeoutException:
            self.logError("Failed to locate 'F1'")
            retVal = -3
        self.driver.get_screenshot_as_file("/tmp/page_2.png")
        
        # Check, if captcha is needed
        if( 0 == retVal ):
            
            element_captcha_code = None
            
            try:
                element_captcha_code = element_f1.find_element_by_name("code")
                self.logDebug("Found captcha 'code'")
                foundCaptchaCode = True
            except NoSuchElementException:
                self.logInfo("Failed to obtain element 'code' in 'F1'")
                element_captcha_code = None
                
            
            if( None != element_captcha_code ):
                self.logDebug("Save screenshot")
                #self.driver.get_screenshot_as_file("/www/pyload_captcha/captcha.png")
                element_screenshot( self.driver , element_f1 , "/www/pyload_captcha/captcha.png" )
                self.logDebug("Saved screenshot")
                captcha_text = self.decryptCaptcha("http://cubie:10080/pyload_captcha/captcha.png")
                self.logDebug("Got captcha %s" % (captcha_text))
                if( None == captcha_text ):
                    self.logInfo("Got no captcha response")
                    retVal = -4
                else:
                    element_captcha_code.send_keys(captcha_text)
                
        # Locate and click button 'btn_download'
        if( 0 == retVal ):
            if( 0 != self.locate_element_and_click( By.ID, 'btn_download' , True ) ):
                self.logError("Failed to locate 'btn_download'")
                retVal = -3
        return retVal        
    
    def locate_direct_link( self ):
        
        self.logDebug("locate_direct_link()")
        retVal = 0
        
        try:
            element_footer = WebDriverWait(self.driver, self.seconds_until_timeout).until(EC.visibility_of_element_located((By.CLASS_NAME, 'footer' )))
            
            self.logDebug("Found footer")
        except TimeoutException:
            self.logError("Failed to locate footer")
            retVal = -1
        
        self.driver.get_screenshot_as_file("/tmp/page_ldl1.png")
            
        if( 0 == retVal ):
            
            isDownloadPage = False
            elements_h3 = self.driver.find_elements_by_tag_name( 'h3' )
            for element_h3 in elements_h3:
                
                self.logDebug("Found h3: %s" % (element_h3.text) )
                
                downloadSiteNeedle = 'Link Generated'
                if( None != re.search( downloadSiteNeedle , element_h3.text )):
                    isDownloadPage = True
            if( True != isDownloadPage ):
                self.logDebug("Not the download page")
                retVal = -2

                    
                        
        # Locate and click button 'btn_download'
        #if( 0 == retVal ):
        #    if( 0 != self.locate_element_and_click( By.ID, 'btn_download' , True ) ):
        #        self.logError("Failed to locate 'btn_download'")
        #        retVal = -3
                
        # Locate and click checkbox 'd_acc_checkbox'
        if( 0 == retVal ):
            if( 0 != self.locate_element_and_click( By.ID, 'd_acc_checkbox' , False ) ):
                self.logError("Failed to locate 'd_acc_checkbox'")
                ###retVal = -4
                
        # Wait until element of class 'file_slot' appears
        # Before 20150504: This element will hold an <a> element, that contains the name of the direct link
        # Since 20150504: When the 'file_slot' element appears, the <a> element with the direct link will appear 
        #                 on the site.
        if( 0 == retVal ):
            self.logDebug("Wait for file_slot")
            try:
                #element = WebDriverWait(self.driver, self.seconds_until_timeout).until(EC.element_to_be_clickable((By.CLASS_NAME, 'file_slot' )))
                element = WebDriverWait(self.driver, self.seconds_until_timeout).until(EC.presence_of_element_located((By.CLASS_NAME, 'file_slot' )))
                self.logDebug("Found file_slot")
            except TimeoutException:
                self.logError("Failed to locate 'file_slot")
                retVal = -5
        
        self.driver.get_screenshot_as_file("/tmp/page_ldl2.png")
        
        # Locate <a> element with 'onclick' attribute that contains the direct link
        if( 0 == retVal ):
            retVal = -6
            elements = self.driver.find_elements_by_tag_name('a')
            #elements = element.find_elements_by_tag_name('a')
            for element in elements:
                attr = element.get_attribute('onclick')
                self.logDebug("Check onclick element %s" % (attr))
                if ( None != attr ) and ( "window.open" in attr):
                    p = re.compile( '(window.open\(\'|\'\);)' )
                    result = p.sub('', attr)
                    if( 0 != len(result) ):
                        self.logDebug("Found link! %s" % (attr))
                        self.direct_link = result
                        retVal = 0
                        break
        return retVal
    
    def obtain_direct_link( self ):
        
        """Determine direct download link of clicknupload.com and store it in self.direct_link. Returns 0 on success"""
        
        # Init worker variables
        retVal = 0
        self.direct_link = None
        self.driver = None
    
        
        
        # Xvfb
        self.xvfb = None
        #self.xvfb = Xvfb()
        
        
        try:
            if( None != self.xvfb ):
                self.xvfb.start()
            # TODO run some selenium tests here
            #xvfb.stop()
        except OSError:
            self.logError("Error: xvfb cannot be found on your system, please install it and try again")
            retVal = -1
                
            
        if( 0 == retVal ):
            try:
                self.driver=webdriver.PhantomJS( )
                #self.driver=webdriver.Firefox()
                
                #self.driver = webdriver.Chrome()
            
            except WebDriverException:
                self.logError("Failed to create webdriver.PhantomJS() class")
                self.driver=None
                retVal = -1
            
        ################# Load first page ####################
        if( 0 == retVal ):
            retVal = self.handle_first_page()
                        
        ################# Load second page ##################
        link_found = False
        retryCounter = 0
        while( 0 == retVal ):
            
            retVal = self.locate_direct_link()
            
            if( retryCounter >= 10 ):
                self.logError("Reached max num of retries")
                retVal = -2
            
            if( 0 == retVal ):
                link_found = True
                break
            else:
                retVal = self.handle_second_page()
                retryCounter += 1
                
        # Evaluate, if direct link was found
        if( None == self.direct_link ):
            retVal = -6
        
        # Cleanup
        if( None != self.driver ):
            self.driver.quit()
            self.driver = None
            
        if( None != self.xvfb ):
            try:
                self.xvfb.stop()
            except OSError:
                self.logError("Error: xvfb cannot be found on your system")
                                            
        return retVal


###################################################################################################################
###################################################################################################################
###################################################################################################################
###################################################################################################################
###################################################################################################################
###################################################################################################################

###################################################################################################################

###################################################################################################################

###################################################################################################################
###################################################################################################################
###################################################################################################################
###################################################################################################################

###################################################################################################################
###################################################################################################################
###################################################################################################################
###################################################################################################################


    
    def page1HandleForm(self,center_element):
        
        retVal = dict()
        isRightForm = False
        
        self.logDebug("form")
        for input_elem in center_element.getElementsByTagName("input"):
            self.logDebug( "input elem : %s %s" % ( input_elem.getAttribute("name") , input_elem.getAttribute("value") ) )
            if ( "method_free" == input_elem.getAttribute("name") ):
                isRightForm = True
            else:
                #retVal[input_elem.getAttribute("name")]  = input_elem.getAttribute("value")
                retVal[input_elem.getAttribute("value")]  = input_elem.getAttribute("name")
                #retVal.append( [input_elem.getAttribute("name") : input_elem.getAttribute("value")] )
            
        return isRightForm,retVal





    def obtain_direct_link_native( self ):
        
        """Determine direct download link of clicknupload.com and store it in self.direct_link. Returns 0 on success"""
        
        # Init worker variables
        retVal = 0
        self.direct_link = None
        self.driver = None

        self.logDebug("Load page %s" % (self.pyfile.url))
        #self.driver.get(self.pyfile.url)
        self.html = self.load(self.pyfile.url)
        #, get={}, post={}, ref=True, cookies=True, just_header=False, decode=False)[source]
        
        self.logDebug("Page: %s" % self.html )

        
                

        dom = html5lib.parse(self.html,treebuilder="dom")


        for form_element in dom.getElementsByTagName("form"):
            isRightForm,post_list = self.page1HandleForm(form_element)
            if( True == isRightForm ):
                self.logDebug("Is right form!")
                break

        self.logDebug("Post list: %s" % post_list )
                              
            
        self.logDebug("Load next site")
            
            
        self.html = self.load(self.pyfile.url , post=post_list , decode=False )

        
        self.logDebug("Page2: %s" % self.html )

        #parse download form
        #action, inputs = parseHtmlForm('method_free', self.html)
        
        #self.logDebug("Action: %s" % action )
        #self.logDebug("Inputs: %s" % inputs )
        
                
        self.logDebug("Minidom" )

        #center_elements = dom.getElementsByTagName("center")
        
        self.logDebug("Minidom 2")
        
        #for center_element in center_elements:
        #    self.logDebug("Center ")
        
        return retVal
