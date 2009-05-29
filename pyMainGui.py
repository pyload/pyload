#!/usr/bin/python
import wx
from os import sep
from os.path import abspath, dirname

class pyAddDownloadDialog(wx.Dialog):
    def __init__(self, parent, id, title):
        wx.Dialog.__init__(self, parent, id, title, size=(700,400))
        pass
        
        
        
class pyPanelUp(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        #self.SetBackgroundColour(wx.WHITE)
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        downloadliste = wx.ListCtrl(self, style=wx.LC_REPORT)
        downloadliste.InsertColumn(0, 'Name', width=250)
        downloadliste.InsertColumn(1, 'Status')
        downloadliste.InsertColumn(2, 'Groesse')
        downloadliste.InsertColumn(3, 'Uebertragen')
        downloadliste.InsertColumn(4, 'Prozent',width=50)
        downloadliste.InsertColumn(5, 'Dauer',width=50)
        downloadliste.InsertColumn(6, 'Uebrig',width=50)
        downloadliste.InsertColumn(7, 'Geschwindigkeit',width=50)
        downloadliste.InsertColumn(8, 'Download FOrdner', width=200)

        sizer.Add(downloadliste, 1, wx.EXPAND)
        self.SetSizer(sizer)


class pyPanelDown(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        self.SetBackgroundColour(wx.BLACK)
        
        
class pyMain(wx.Frame):
    def __init__(self, parent, id, title="pyLoad"):
        
        wx.Frame.__init__(self,parent,id,title, size=(910,500))
        
        appPath = dirname(abspath(__file__)) + sep
        
        #   Menubar
        menubar = wx.MenuBar()
        file = wx.Menu()
        exit = file.Append(-1,'Exit','Close pyLoad')
        menubar.Append(file, '&File')
        self.SetMenuBar(menubar)
        
        #   Toolbar
        toolbar = self.CreateToolBar()
        toolbar.SetToolBitmapSize((32,32))
        add = toolbar.AddLabelTool(2,'',wx.Bitmap(appPath + '/icons/add.png'))
        delete = toolbar.AddLabelTool(3,'',wx.Bitmap(appPath + '/icons/del.png'))
        start = toolbar.AddLabelTool(4,'',wx.Bitmap(appPath + '/icons/start.png'))
        pause = toolbar.AddLabelTool(5,'',wx.Bitmap(appPath + '/icons/pause.png'))
        stop = toolbar.AddLabelTool(6,'',wx.Bitmap(appPath + '/icons/stop.png'))
        up = toolbar.AddLabelTool(7,'',wx.Bitmap(appPath + '/icons/up.png'))
        down = toolbar.AddLabelTool(8,'',wx.Bitmap(appPath + '/icons/down.png'))
        toolbar.Realize()
        
        splitter = wx.SplitterWindow(self)
        
        
        panelUp = pyPanelUp(splitter)
        #panelUp.SetBackgroundColour(wx.WHITE)
        
        panelDown = pyPanelDown(splitter)
        #panelDown.SetBackgroundColour(wx.BLACK)
        
        splitter.SplitHorizontally(panelUp,panelDown,300)
        
        #   Binds
        self.Bind(wx.EVT_MENU, self.OnExit,exit)
        self.Bind(wx.EVT_TOOL, self.onAddButtonClicked, add)
        
        
        
        self.Centre()
        self.Show(True)
        
    def OnExit(self, event):
        self.Close()
        
    def onAddButtonClicked(self, event):
        adddownload = pyAddDownloadDialog(None, -1, 'Download hinzufuegen')
        adddownload.ShowModal()
        adddownload.Destroy()
                
app = wx.App()
pyMain(None,-1)
app.MainLoop()
