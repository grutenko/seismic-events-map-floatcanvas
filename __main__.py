import wx
import wx.aui
from typing import List
from dataclasses import dataclass, field

from plot import SeismicEventsMapPlot, SeismicPlotGroup
from toolbar import MainToolbar
from menu import MainMenu
from properties import PropertiesPanel
from object import ObjectsPanel
from seismic_import import SeismicImport
from object_data import DxfPlot, DxfPlotLayer, SeismicEvents

class MainWindow(wx.Frame):
    def __init__(self):
        super().__init__(None, title='Карта сейсмических событий', size=wx.Size(800, 600))

        self.objects = []
        self.menu = MainMenu()
        self.SetMenuBar(self.menu)
        self.toolbar = MainToolbar(self)
        self.mgr = wx.aui.AuiManager(self)
        self.mgr.AddPane(self.toolbar, wx.aui.AuiPaneInfo().ToolbarPane().Top())
        self.plot = SeismicEventsMapPlot(self)
        self.mgr.AddPane(self.plot, wx.aui.AuiPaneInfo().CenterPane())
        self.object = ObjectsPanel(self)
        self.mgr.AddPane(self.object, wx.aui.AuiPaneInfo().Right().MinSize(300, 200).Caption("Объекты").MaxSize(600, 1200))
        self.properties = PropertiesPanel(self)
        self.mgr.AddPane(self.properties, wx.aui.AuiPaneInfo().Right().MinSize(300, 200).Caption("Свойства").MaxSize(600, 1200))
        self.mgr.Update()

        self.bind_all()
        self.Show()

    def bind_all(self):
        self.menu.Bind(wx.EVT_MENU, self.on_open_dxf, id=wx.ID_FILE1)
        self.menu.Bind(wx.EVT_MENU, self.on_open_csv, id=wx.ID_FILE2)
        self.toolbar.Bind(wx.EVT_TOOL, self.on_open_dxf, id=wx.ID_FILE1)
        self.toolbar.Bind(wx.EVT_TOOL, self.on_open_csv, id=wx.ID_FILE2)

    def on_open_dxf(self, event):
        import ezdxf
        with wx.FileDialog(self, "Open XYZ file", wildcard="DXF files (*.dxf)|*.dxf", style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return
            doc = ezdxf.readfile(fileDialog.GetPath())
            object = DxfPlot(fileDialog.GetPath(), affine_transform_filename=None, data=doc)
            object.data = doc
            msp = doc.modelspace
            for layer in doc.layers:
                object.layers.append(DxfPlotLayer(layer.dxf.name, self.plot.add_group()))
            layer_group_mapping = {}
            for layer in object.layers:
                layer_group_mapping[layer.name] = layer.group 
            self.plot.dxf_load(doc, layer_group_mapping, affine=None)
            self.objects.append(object)
            self.object.update(self.objects)
                
    def on_open_csv(self, event):
        dlg = SeismicImport(self)
        if dlg.ShowModal() == wx.ID_OK:
            ...

if __name__ == '__main__':
    app = wx.App(0)
    MainWindow()
    app.MainLoop()
