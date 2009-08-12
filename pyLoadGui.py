#!/usr/bin/env python
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

import socket
import subprocess
from os import sep
from os.path import abspath, dirname
from time import sleep

import wxversion
wxversion.select('2.8')

import wx
import wx.lib.newevent
import wx.lib.sized_controls as sized_control
from module.remote.ClientSocket import SocketThread

(DataArrived, EVT_DATA_ARRIVED) = wx.lib.newevent.NewEvent()

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

        #Clipboard
        self.data = wx.TextDataObject()
        if wx.TheClipboard.Open():
            wx.TheClipboard.GetData(self.data)
            for link in self.data.GetText().split('\n'):
                if link.startswith("http"):
                    self.links.write(link + "\n")
            wx.TheClipboard.Close()

class Download_Liste(wx.ListCtrl):
    def __init__(self, parent):
        wx.ListCtrl.__init__(self, parent, -1, style=wx.LC_REPORT | wx.LC_VIRTUAL)

        # columns
        self.InsertColumn(0, 'Name', width=300)
        self.InsertColumn(1, 'Status', width=120)
        self.InsertColumn(2, 'Größe')
        self.InsertColumn(3, 'Übertragen', width=100)
        self.InsertColumn(4, 'Prozent', width=60)
        self.InsertColumn(5, 'Dauer', width=100)
        self.InsertColumn(7, 'Geschwindigkeit', width=120)


        self.itemDataMap = {}
        self.itemIndexMap = []
        self.SetItemCount(len(self.itemIndexMap))

    def reload(self, links, data):

        self.itemIndexMap = data['order']

        self.create_data(links, data)
        
        self.SetItemCount(len(self.itemIndexMap))
        self.Refresh()

    def create_data(self, links, data):

        self.itemDataMap = {}

        for key, value in data.iteritems():
            if key != 'version' and key != 'order':
                self.itemDataMap[key] = [value.url]

        for link in links:
            self.itemDataMap[link['id']][0] = link['name']
            self.itemDataMap[link['id']].append(link['status'])
            self.itemDataMap[link['id']].append(str(link['size']) + " kb")
            self.itemDataMap[link['id']].append(str(link['size'] - link['kbleft']) + " kb")
            self.itemDataMap[link['id']].append(str(link['percent']) + " %")
            self.itemDataMap[link['id']].append(format_time(link['eta']))
            self.itemDataMap[link['id']].append(str(int(link['speed'])) + " kb/s")

    # virtual methods
    def OnGetItemText(self, item, col):
        index = self.itemIndexMap[item]
        try:
            s = self.itemDataMap[index][col]
        except:
            s = ""
        return s

    def OnGetItemAttr(self, item):
        return None

class _Upper_Panel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.parent = parent

        self.list = Download_Liste(self)

        sizer.Add(self.list, 1, wx.EXPAND)
        self.SetSizer(sizer)

    def refresh(self, links, data):        
        self.list.reload(links, data)

    def get_selected_ids(self, deselect=False):
        """return ids and deselect items"""
        item = self.list.GetFirstSelected()
        if deselect: self.list.Select(item, on=0)

        if item == -1:
            return False

        links = []
        links.append(self.parent.data['order'][item])

        while self.list.GetNextSelected(item) != -1:
            item = self.list.GetNextSelected(item)
            if deselect: self.list.Select(item, on=0)
            links.append(self.parent.data['order'][item])

        return links

class _Lower_Panel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        self.SetBackgroundColour(wx.BLACK)
        
class _Host_Dialog(wx.Dialog):
    def __init__(self, parent, id, title):
        wx.Dialog.__init__(self, parent, id, title, size=(250, 170))
        
        self.host = wx.TextCtrl(self, -1, '127.0.0.1')
        host_name = wx.StaticText(self, -1, 'Host:')
        self.port = wx.TextCtrl(self, -1, '7272')
        port_name = wx.StaticText(self, -1, 'Port:')
        self.password = wx.TextCtrl(self, -1, 'pwhere')
        password_name = wx.StaticText(self, -1, 'Password:')
        button_ok = wx.Button(self, wx.ID_OK, 'Ok', size=(90, 28))
        button_cancel = wx.Button(self, wx.ID_CANCEL, 'Close', size=(90, 28))
        
        
        fgs = wx.FlexGridSizer(3, 2, 9, 25)
        
        fgs.AddMany([(host_name), (self.host, 0, wx.EXPAND), (port_name), (self.port, 1, wx.EXPAND), (password_name), (self.password, 1, wx.EXPAND), (button_ok, 1, wx.EXPAND), (button_cancel, 1, wx.EXPAND)])
        
        fgs.AddGrowableCol(1, 1)
        
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(fgs, 1, wx.ALL | wx.EXPAND, 15)
        
        
        self.SetSizer(hbox)
        
class Pyload_Main_Gui(wx.Frame):
    def __init__(self, parent, id, title="pyLoad"):

        wx.Frame.__init__(self, parent, id, title, size=(910, 500))

        app_path = dirname(abspath(__file__)) + sep

        #   vars
        self.links = []
        self.data = {}

        #   Menubar
        menubar = wx.MenuBar()
        menu_file = wx.Menu()
        submenu_exit = menu_file.Append(-1, 'Schliessen', 'pyLoad beenden')
        menubar.Append(menu_file, '&Datei')
        menu_pyload = wx.Menu()
        self.submenu_pyload_connect = menu_pyload.Append(-1, 'Connect', 'Connect to pyLoad')
        self.submenu_pyload_disconnect = menu_pyload.Append(-1, 'Disconnect', 'Disconnect')
        self.submenu_pyload_shutdown = menu_pyload.Append(-1, 'Shutdown', 'Shutdown pyLoad Core')
        menubar.Append(menu_pyload, '&pyLoad')
        self.SetMenuBar(menubar)
        
        #    Statusbar
        self.CreateStatusBar()

        # icon
        icon1 = wx.Icon(app_path + '/icons/pyload.ico', wx.BITMAP_TYPE_ICO)
        self.SetIcon(icon1)

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

        #splitter = wx.SplitterWindow(self)
        self.panel_up = _Upper_Panel(self)
        #panel_down = _Lower_Panel(splitter)
        #splitter.SplitHorizontally(panel_up, panel_down, 300)

        #   Binds
        self.Bind(wx.EVT_MENU, self.exit_button_clicked, submenu_exit)
        self.Bind(wx.EVT_MENU, self.connect, self.submenu_pyload_connect)
        self.Bind(wx.EVT_MENU, self.disconnect, self.submenu_pyload_disconnect)
        self.Bind(wx.EVT_MENU, self.shutdown, self.submenu_pyload_shutdown)
        self.Bind(wx.EVT_TOOL, self.add_button_clicked, add)
        self.Bind(wx.EVT_TOOL, self.delete_button_clicked, delete)
        self.Bind(wx.EVT_TOOL, self.up_button_clicked, up)
        self.Bind(wx.EVT_TOOL, self.down_button_clicked, down)
        self.Bind(EVT_DATA_ARRIVED, self.onUpdate)

        self.Centre()
        self.Show(True)
        

    def exit_button_clicked(self, event):
        self.Close()
    
    def connect(self, event):
        socket_host = _Host_Dialog(self, -1, 'Connect to:')
        res_socket = socket_host.ShowModal()
        if (res_socket == wx.ID_OK):
            try:
                self.thread = SocketThread(socket_host.host.GetValue(), int(socket_host.port.GetValue()), socket_host.password.GetValue(), self)
                self.SetStatusText('Connected to: %s:%s' % (socket_host.host.GetValue(), socket_host.port.GetValue()))
            except socket.error:
                if (socket_host.host.GetValue() in ['localhost', '127.0.0.1']):
                    if (wx.MessageDialog(None, 'Do you want to start pyLoadCore locally?', 'Start pyLoad', wx.OK | wx.CANCEL).ShowModal() == wx.ID_OK):
                        cmd = ['python', 'pyLoadCore.py']
                        subprocess.Popen(cmd)
                        sleep(2)
                        self.thread = SocketThread(socket_host.host.GetValue(), int(socket_host.port.GetValue()), socket_host.password.GetValue(), self)
                        self.SetStatusText('Connected to: %s:%s' % (socket_host.host.GetValue(), socket_host.port.GetValue()))
                    else:
                        wx.MessageDialog(None, 'Cant connect to: %s:%s' % (socket_host.host.GetValue(), socket_host.port.GetValue()), 'Error', wx.OK | wx.ICON_ERROR).ShowModal()
                else:
                    wx.MessageDialog(None, 'Cant connect to: %s:%s' % (socket_host.host.GetValue(), socket_host.port.GetValue()), 'Error', wx.OK | wx.ICON_ERROR).ShowModal()

            self.thread.push_exec("get_links")

    def disconnect(self, event):
        self.thread.socket.close_when_done()
        self.SetStatusText('')

    def shutdown(self, event):
        self.thread.push_exec("kill")

    def add_button_clicked(self, event):
        #test
        #self.thread.push_exec("get_downloads")

        add_download = _Download_Dialog(None, -1)
        result = add_download.ShowModal()
        add_download.Destroy()
        downloads = add_download.links.GetValue().split()
        self.thread.push_exec('add_links', [downloads])

    def delete_button_clicked(self, event):

        links = self.panel_up.get_selected_ids(True)

        self.thread.push_exec('remove_links', [links])

    def up_button_clicked(self, event):

        links = self.panel_up.get_selected_ids()
        self.thread.push_exec('move_links_up', [links])


    def down_button_clicked(self, event):

        links = self.panel_up.get_selected_ids()

        self.thread.push_exec('move_links_down', [links])

    def show_links(self, links):
        for link in links:
            #wx.MessageDialog(self, str(link), 'info', style=wx.OK).ShowModal()
            print str(link)

    def data_arrived(self, rep):
        evt = DataArrived(obj=rep)
        wx.PostEvent(self, evt)

    def onUpdate(self, evt):

        if evt.obj.function == "get_downloads":
            pass
            #self.show_links(evt.obj.response)

        if evt.obj.command == "update":
            self.links = evt.obj.data
            self.panel_up.refresh(self.links, self.data)
            
        if evt.obj.command == "file_list" or evt.obj.function == "get_links":
            self.data = evt.obj.data
            self.panel_up.refresh(self.links, self.data)


def format_time(seconds):
    seconds = int(seconds)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    return "%.2i:%.2i:%.2i" % (hours, minutes, seconds)


app = wx.App()
Pyload_Main_Gui(None, -1)
app.MainLoop()
