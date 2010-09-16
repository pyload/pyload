# -*- coding: utf-8 -*-

from __future__ import with_statement
from time import sleep
from os.path import exists
from os.path import join
from shutil import copy


CONF_VERSION = 1

########################################################################
class ConfigParser:
    """
    holds and manage the configuration
    
    current dict layout:
    
    {
    
     section : { 
      option : { 
            value:
            type:
            desc:
      }
      desc: 
    
    }
    
    
    """

    #----------------------------------------------------------------------
    def __init__(self):
        """Constructor"""
        self.config = {} # the config values
        self.plugin = {} # the config for plugins
        
        self.username = ""
        self.password = ""
        #stored outside and may not modified
        
        
        self.checkVersion()
        
        self.readConfig()
    
    #----------------------------------------------------------------------
    def checkVersion(self, n=0):
        """determines if config need to be copied"""
        try:
            if not exists("pyload.conf"):
                copy(join(pypath,"module", "config", "default.conf"), "pyload.conf")
                
            if not exists("plugin.conf"):
                f = open("plugin.conf", "wb")
                f.write("version: "+str(CONF_VERSION))
                f.close()
            
            f = open("pyload.conf", "rb")
            v = f.readline()
            f.close()
            v = v[v.find(":")+1:].strip()
            
            if not v or int(v) < CONF_VERSION:
                copy(join(pypath,"module", "config", "default.conf"), "pyload.conf")
                print "Old version of config was replaced"
            
            f = open("plugin.conf", "rb")
            v = f.readline()
            f.close()
            v = v[v.find(":")+1:].strip()
              
            if not v or int(v) < CONF_VERSION:
                f = open("plugin.conf", "wb")
                f.write("version: "+str(CONF_VERSION))
                f.close()
                print "Old version of config was replaced"
        except:
            if n < 3:
                sleep(0.3)
                self.checkVersion(n+1)
            else:
                raise
        
    #----------------------------------------------------------------------
    def readConfig(self):
        """reads the config file"""
        
        self.config = self.parseConfig(join(pypath,"module", "config", "default.conf"))
        self.plugin = self.parseConfig("plugin.conf")
        
        try:
            homeconf = self.parseConfig("pyload.conf")
            self.updateValues(homeconf, self.config)
            
        except Exception, e:
            print e
        
            
        self.username = self.config["remote"]["username"]["value"]
        del self.config["remote"]["username"]
        
        self.password = self.config["remote"]["password"]["value"]
        del self.config["remote"]["password"]
        
        
    #----------------------------------------------------------------------
    def parseConfig(self, config):
        """parses a given configfile"""
        
        f = open(config)
        
        config = f.read()

        config = config.split("\n")[1:]
        
        conf = {}
        
        section, option, value, typ, desc = "","","","",""
        
        listmode = False
        
        for line in config:
            
            line = line.rpartition("#") # removes comments
            
            if line[1]:
                line = line[0]
            else:
                line = line[2]
            
            line = line.strip()            
            
            try:
            
                if line == "":
                    continue
                elif line.endswith(":"):
                    section, none, desc = line[:-1].partition('-')
                    section = section.strip()
                    desc = desc.replace('"', "").strip()
                    conf[section] = { "desc" : desc }
                else:
                    if listmode:
                        
                        if line.endswith("]"):
                            listmode = False
                            line = line.replace("]","")
                            
                        value += [self.cast(typ, x.strip()) for x in line.split(",") if x]
                        
                        if not listmode:
                            conf[section][option] = { "desc" : desc,
                                                      "type" : typ,
                                                      "value" : value} 
                        
                        
                    else:
                        content, none, value = line.partition("=")
                        
                        content, none, desc = content.partition(":")
                        
                        desc = desc.replace('"', "").strip()
    
                        typ, option = content.split()
                                                
                        value = value.strip()
                        
                        if value.startswith("["):
                            if value.endswith("]"):                            
                                listmode = False
                                value = value[:-1]
                            else:
                                listmode = True
                          
                            value = [self.cast(typ, x.strip()) for x in value[1:].split(",") if x]
                        else:
                            value = self.cast(typ, value)
                        
                        if not listmode:
                            conf[section][option] = { "desc" : desc,
                                                      "type" : typ,
                                                      "value" : value}
                
            except:
                pass
                    
                        
        f.close()
        return conf
        
    
    
    #----------------------------------------------------------------------
    def updateValues(self, config, dest):
        """sets the config values from a parsed config file to values in destination"""
                                
        for section in config.iterkeys():
    
            if dest.has_key(section):
                
                for option in config[section].iterkeys():
                    
                    if option == "desc": continue
                    
                    if dest[section].has_key(option):
                        dest[section][option]["value"] = config[section][option]["value"]
                        
                    #else:
                    #    dest[section][option] = config[section][option]
                
                
            #else:
            #    dest[section] = config[section]

    #----------------------------------------------------------------------
    def saveConfig(self, config, filename):
        """saves config to filename"""
        with open(filename, "wb") as f:
            f.write("version: %i \n" % CONF_VERSION)
            for section in config.iterkeys():
                f.write('\n%s - "%s":\n' % (section, config[section]["desc"]))
                
                for option, data in config[section].iteritems():
                    
                    if option == "desc": continue
                    
                    if isinstance(data["value"], list):
                        value = "[ \n"
                        for x in data["value"]:
                            value += "\t\t" + str(x) + ",\n"
                        value += "\t\t]\n"
                    else:
                        value = str(data["value"]) + "\n"
                    
                    f.write('\t%s %s : "%s" = %s' % (data["type"], option, data["desc"], value) )
    #----------------------------------------------------------------------
    def cast(self, typ, value):
        """cast value to given format"""
        if type(value) not in (str, unicode):
            return value
        
        if typ == "int":
            return int(value)
        elif typ == "bool":
            return True if value.lower() in ("1","true", "on", "an","yes") else False
        elif typ == "str":
            return str(value)
        else:
            return value
                
    #----------------------------------------------------------------------
    def save(self):
        """saves the configs to disk"""
        
        self.config["remote"]["username"] = {
            "desc" : "Username",
            "type": "str",
            "value": self.username
        }
        
        self.config["remote"]["password"] = {
            "desc" : "Password",
            "type": "str",
            "value": self.password
        } 
        
        self.saveConfig(self.config, "pyload.conf")
        
        del self.config["remote"]["username"]
        del self.config["remote"]["password"]
        
        self.saveConfig(self.plugin, "plugin.conf")
        
    #----------------------------------------------------------------------
    def __getitem__(self, section):
        """provides dictonary like access: c['section']['option']"""
        return Section(self, section)
    
    #----------------------------------------------------------------------
    def get(self, section, option):
        """get value"""
        return self.config[section][option]["value"]
        
    #----------------------------------------------------------------------
    def set(self, section, option, value):
        """set value"""

        value = self.cast(self.config[section][option]["type"], value)
            
        self.config[section][option]["value"] = value
        self.save()
        
    #----------------------------------------------------------------------
    def getPlugin(self, plugin, option):
        """gets a value for a plugin"""
        return self.plugin[plugin][option]["value"]
    
    #----------------------------------------------------------------------
    def setPlugin(self, plugin, option, value):
        """sets a value for a plugin"""

        value = self.cast(self.plugin[plugin][option]["type"], value)
        
        self.plugin[plugin][option]["value"] = value
        self.save()
        
    #----------------------------------------------------------------------
    def addPluginConfig(self, config):
        """adds config option with tuple (plugin, name, type, desc, default)"""
        
        if not self.plugin.has_key(config[0]):
            self.plugin[config[0]] = { "desc" : config[0],
                                       config[1] : {
                                           "desc" : config[3],
                                           "type" : config[2],
                                           "value" : self.cast(config[2], config[4])
                                       } }
        else:
            if not self.plugin[config[0]].has_key(config[1]):
                self.plugin[config[0]][config[1]] = {
                                           "desc" : config[3],
                                           "type" : config[2],
                                           "value" : self.cast(config[2], config[4])
                                       }

########################################################################
class Section:
    """provides dictionary like access for configparser"""

    #----------------------------------------------------------------------
    def __init__(self, parser, section):
        """Constructor"""
        self.parser = parser
        self.section = section
        
    #----------------------------------------------------------------------
    def __getitem__(self, item):
        """getitem"""
        return self.parser.get(self.section, item)
        
    #----------------------------------------------------------------------
    def __setitem__(self, item, value):
        """setitem"""
        self.parser.set(self.section, item, value)
        

    
if __name__ == "__main__":
    pypath = ""

    from time import time
    
    a = time()
    
    c = ConfigParser()
    
    b = time()
    
    print "sec", b-a    
    
    print c.config
    
    c.saveConfig(c.config, "user.conf")
