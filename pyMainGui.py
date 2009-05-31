#!/usr/bin/python
# -*- coding: utf-8 -*- 
# 
#Copyright (C) 2009 KingZero
#
#This program is free software; you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation; either version 3 of the License,
#or (at your option) any later version.
#
#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#See the GNU General Public License for more details.
#
#You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>.
#
###

from os import sep
from os.path import abspath
from os.path import dirname

import wx
import wx.lib.sized_controls as sized_control
from module.remote.ClientSocket import ClientSocket
from Core import Core
#from module.Py_Load_File import PyLoadFile
from module.remote.SocketServer import ServerThread
#from module.thread_list import Thread_List

class _Download_Dialog(sized_control.SizedDialog):
    def __init__(self, parent, id):
        sized_control.SizedDialog.__init__(self, parent, id, "Downloads hinzufügen",
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
       
        pane = self.GetContentsPane()

        self.links = wx.TextCtrl(pane, -1, style=wx.TE_MULTILINE, size=(500, 200))
        self.links.SetSizerProps(expand=True, proportion=1)

        self.SetButtonSizer(self.CreateStdDialogButtonSizer(wx.OK | wx.CANCEL))

        self.Fit()
        self.SetMinSize(self.GetSize())

class _Upper_Panel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        download_liste = wx.ListCtrl(self, style=wx.LC_REPORT)
        download_liste.InsertColumn(0, 'Name', width=250)
        download_liste.InsertColumn(1, 'Status')
        download_liste.InsertColumn(2, 'Groesse')
        download_liste.InsertColumn(3, 'Uebertragen', width=100)
        download_liste.InsertColumn(4, 'Prozent', width=100)
        download_liste.InsertColumn(5, 'Dauer', width=100)
        download_liste.InsertColumn(7, 'Geschwindigkeit', width=150)

        sizer.Add(download_liste, 1, wx.EXPAND)
        self.SetSizer(sizer)


class _Lower_Panel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        self.SetBackgroundColour(wx.BLACK)
        
        
class Pyload_Main_Gui(wx.Frame):
    def __init__(self, parent, id, title="pyLoad"):
        
        wx.Frame.__init__(self, parent, id, title, size=(910, 500))
        
        app_path = dirname(abspath(__file__)) + sep
        # Core
        testLoader = Core()
        if testLoader.config['remote_activated']:
            print _("Server Mode")
            server = ServerThread(testLoader)
            server.start()

	    #   socket
        self.socket = ClientSocket(self)
        self.socket.connect(('localhost', 7272))
        self.socket.sendall("nonsense\n")
        
        #   Menubar
        menubar = wx.MenuBar()
        menu_file = wx.Menu()
        submenu_exit = menu_file.Append(-1, 'Schliessen', 'pyLoad beenden')
        menubar.Append(menu_file, '&Datei')
        self.SetMenuBar(menubar)
        
        #   Toolbar
        toolbar = self.CreateToolBar()
        toolbar.SetToolBitmapSize((32, 32))
        add = toolbar.AddLabelTool(2, '', wx.Bitmap(app_path + '/icons/add.png'))
        delete = toolbar.AddLabelTool(3, '', wx.Bitmap(app_path + '/icons/del.png'))
        start = toolbar.AddLabelTool(4, '', wx.Bitmap(app_path + '/icons/start.png'))
        pause = toolbar.AddLabelTool(5, '', wx.Bitmap(app_path + '/icons/pause.png'))
        stop = toolbar.AddLabelTool(6, '', wx.Bitmap(app_path + '/icons/stop.png'))
        up = toolbar.AddLabelTool(7, '', wx.Bitmap(app_path + '/icons/up.png'))
        down = toolbar.AddLabelTool(8, '', wx.Bitmap(app_path + '/icons/down.png'))
        config = toolbar.AddLabelTool(9, '', wx.Bitmap(app_path + '/icons/setup.png'))
        toolbar.Realize()
        
        splitter = wx.SplitterWindow(self)
        panel_up = _Upper_Panel(splitter)
        panel_down = _Lower_Panel(splitter)
        splitter.SplitHorizontally(panel_up,panel_down,300)

        #   Binds
        self.Bind(wx.EVT_MENU, self.exit_button_clicked, submenu_exit)
        self.Bind(wx.EVT_TOOL, self.add_button_clicked, add)
        
        
        
        self.Centre()
        self.Show(True)
        
    def exit_button_clicked(self, event):
        self.Close()
        
    def add_button_clicked(self, event):
        adddownload = _Download_Dialog(None, -1)
        result = adddownload.ShowModal()
        adddownload.Destroy()

if __name__ == "__main__":
    app = wx.App()
    Pyload_Main_Gui(None,-1)
    app.MainLoop()
