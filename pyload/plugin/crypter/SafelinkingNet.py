# -*- coding: utf-8 -*-

"""
PyLoad plugin for Safelinking.net support

Dependencies:

  Package name | Tested version
  -------------+--------------- 
  selenium     | 2.44
  phantomjs    | 2.1.1
  Pillow       | 2.3.0
  httplib2     | 0.9

"""

### Imports ###
# Regular expressions
import re

# None type
from types import NoneType

# Selenium
from selenium import webdriver
from selenium.webdriver.common.alert import Alert
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait # available since 2.4.0
from selenium.webdriver.support import expected_conditions as EC # available since 2.26.0
from selenium.common.exceptions import TimeoutException,NoSuchElementException,WebDriverException
from selenium.webdriver.chrome.options import Options

# BadStatusLine exception
from httplib import BadStatusLine

# Image cropping
from PIL import Image

# PyLoad imports
from module.plugins.internal.Crypter import Crypter
from module.plugins.internal.Captcha import Captcha

### Helper functions ###
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


### SafelinkingNet class ###
class SafelinkingNet(Crypter):
    __name__    = "SafelinkingNet"
    __type__    = "crypter"
    __version__ = "0.17"

    __pattern__ = r'https?://(?:www\.)?safelinking\.net/\w+'
    __config__  = [("use_subfolder"     , "bool", "Save package to subfolder"          , True),
                   ("subfolder_per_pack", "bool", "Create a subfolder for each package", True)]

    __description__ = """Safelinking.net decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("tbsnpy", "tbsnpy@gmx.de")]

    seconds_until_timeout = 15
    
    def decrypt(self, pyfile):
        
        url = pyfile.url
        self.links = []
        self.obtain_links()
        
    def obtain_links(self):

        retVal = 0
        gotLink = 0
        
        # Create webdriver instance
        self.driver = None
        if( 0 == retVal ):
            try:
                self.driver=webdriver.PhantomJS( )
                # Other webdrivers can be used as well
                #   self.driver=webdriver.Firefox()
                #   self.driver = webdriver.Chrome()
            
            except WebDriverException:
                self.log_error("Failed to create webdriver.PhantomJS() class")
                self.driver=None
                retVal = -1
        

        link_found = False
        retryCounter = 0
        if( 0 == retVal ):
            retVal = self.handle_first_page()
                
            if( 0 != retVal ):
                self.retry(wait=10, msg="Failed to process first page")
            else:
                retVal = self.handle_second_page()
                
                if( 0 != retVal ):
                    self.retry(wait=10, msg="Captcha not correct")
            
        # Delete webdriver instance
        if( None != self.driver ):
            self.driver.quit()
            self.driver = None

    """ Returns: retVal,progress """
    def wait_for_progress_bar(self):
    
        retVal = 0
        data_progress_text = ""
        
        while ( 0 == retVal ) & ( "100%" != data_progress_text ):
        
            try:
                element_progress = WebDriverWait(self.driver, self.seconds_until_timeout).until(EC.visibility_of_element_located((By.CLASS_NAME, 'pace-progress' )))
                       
                data_progress_text = element_progress.get_attribute('data-progress-text')
                data_progress = element_progress.get_attribute('data-progress')
            
                self.log_debug("wait_for_progress_bar(): pace-progresss-text: %s" % data_progress_text )
            
            except TimeoutException:
                self.log_error("Failed to locate 'pace-progress progres'")
                retVal = -1
                
        return retVal,data_progress_text
            
    def handle_first_page(self):
        
        retVal = 0
        data_progress_text = ""
        
        self.log_debug("handle_first_page(): Load page %s" % (self.pyfile.url))
        self.driver.get(self.pyfile.url)
                
        # Wait until progress bar at top of site reached 100%
        self.log_debug("handle_first_page(): Wait for progress bar to reach 100%")
        retVal,data_progress_text = self.wait_for_progress_bar()
                    

        # Locate captcha puzzle image
        if( 0 == retVal ):
            captcha_image_id = "adcopy-puzzle-image"
            self.log_debug("handle_first_page(): Wait for element '%s'" % captcha_image_id)
            
            ##### Wait for element 'captcha_image_id' ####
            element_captcha = None
            try:
                element_captcha = WebDriverWait(self.driver, self.seconds_until_timeout).until(EC.visibility_of_element_located((By.ID, captcha_image_id )))
                self.log_debug("handle_first_page(): Found %s" % captcha_image_id)
            except TimeoutException:
                self.log_error("handle_first_page(): Failed to locate '%s'" % captcha_image_id )
                retVal = -3

        # Locate captcha response field    
        if( 0 == retVal ):
            # Locate response element
            element_captcha_response = None
            captcha_response_name = "adcopy_response"

            self.log_debug("handle_first_page(): Locate element '%s'" % captcha_response_name)
            try:
                element_captcha_response = self.driver.find_element_by_name(captcha_response_name)
                self.log_debug("handle_first_page(): Found captcha response element")
                foundCaptchaCode = True
            except NoSuchElementException:
                self.log_error("handle_first_page(): Failed to locate element '%s'" % captcha_response_name )
                element_captcha_response = None
                retVal = -4

        # Decrypt captcha
        if( 0 == retVal ):
            
            # 1.  Make screenshot of captcha image and store to file
            captcha_filename = "/tmp/captcha.png"
            captcha_screenshot_pil_obj = element_screenshot( self.driver , element_captcha , captcha_filename )
            
            # 2. Read data from file to variable            
            f = open(captcha_filename, 'r')
            captcha_screenshot = f.read()
            f.close()

            # 3. Pass binary data to Captcha.decrypt_image()
            captchaObj = Captcha(self.pyfile)
            captcha_text = captchaObj.decrypt_image( captcha_screenshot, 'png' , output_type='textual', ocr=True, timeout=120)

            # 4. Write return value of Captcha.decrypt_image() to "adcopy_response" text field
            self.log_debug("handle_first_page(): Got captcha text: \'%s\'" % captcha_text)
            try:
                element_captcha_response.send_keys(captcha_text)
            except WebDriverException:
                retVal = -5
                


        # Locate for "Unlock protection" button
        self.element_ng_click = None
        if( 0 == retVal ):
            
            self.log_debug("handle_first_page(): Search for \'Unlock protection\' button")

            elements = self.driver.find_elements_by_tag_name('a')
            
            for element in elements:
                attr = element.get_attribute('ng-click')
                
                if ( None != attr ) and ( "validate()" in attr):
                    self.element_ng_click = element
                    break
                
            if( None != self.element_ng_click ):
                self.log_debug("handle_first_page(): Found \'Unlock protection\' button")
            else:
                retVal = -6
        
        # Click "Unlock protection" button
        if( 0 == retVal ):
            elem_name = "a ng-click"
            try:
                self.element_ng_click.click()
            except NoSuchElementException:
                self.log_error("handle_first_page(): Click of element %s failed: NoSuchElement" % (elem_name))
                return -7
            except BadStatusLine:
                self.log_error("handle_first_page(): Click of element %s failed: BadStatusLine" % (elem_name))
                #self.driver.get_screenshot_as_file("/tmp/page_1_2.png")
                return -8
            self.log_debug("handle_first_page(): Clicked \'Unlock protection\' button")
            
        self.log_debug("handle_first_page(): exit. retVal: %i" % retVal )

        return retVal

    def handle_second_page(self):
        retVal = 0
        data_progress_text = ""

        # Wait until progress bar at top of site reached 100%
        self.log_debug("handle_second_page(): Wait for progress bar to reach 100%")
        retVal,data_progress_text = self.wait_for_progress_bar()
                        
        # Wait for element 'links'
        if( 0 == retVal ):
            
            links_id = "links"
            self.element_links = None

            self.log_debug("handle_second_page(): Wait for element \'%s\'" % links_id )
            try:
                self.element_links = WebDriverWait(self.driver, self.seconds_until_timeout).until(EC.visibility_of_element_located((By.ID, links_id )))
                
            except TimeoutException:
                self.log_error("Failed to locate '%s'" % links_id )
                retVal = -2
                
        # Parse links from 'links' element
        if( 0 == retVal ):
            elements = self.element_links.find_elements_by_tag_name('a')
            
            for element in elements:
                target = element.get_attribute('target')
                href   = element.get_attribute('href')
                #self.log_debug("handle_second_page() Check element_links target: %s href: %s" % (target,href))
                
                if ( None != target ) and (None != href) and ( "_blank" in target ):
                    
                    if( href in self.links ):
                        self.log_debug("handle_second_page(): Ignore duplicate" )
                    else:
                        self.log_info("handle_second_page(): Found link: \'%s\'" % href )
                        self.links.append(href)
    
            if( 0 != len(self.links) ):
                self.log_debug("Found %i links" % len(self.links ) )
            else:
                retVal = -3
        
        self.log_debug("handle_second_page() exit. retVal: %i" % retVal )
        return retVal
