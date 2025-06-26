import wx
import wx.aui

from plot import SeismicEventsMapPlot, EVT_PLOT_CLICK
from toolbar import MainToolbar
from menu import MainMenu
from properties import PropertiesPanel
from object import ObjectsPanel
from seismic_import import SeismicImport
from object_data import DxfPlot, DxfPlotLayer
from operations import ChangeCoordSystemOperation

class MainWindow(wx.Frame):
    def __init__(self):
        super().__init__(None, title='Карта сейсмических событий', size=wx.Size(800, 600))

        self.objects = []
        self.operation = None
        self.menu = MainMenu()
        self.statusbar = wx.StatusBar(self)
        self.SetStatusBar(self.statusbar)
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
        self.menu.Bind(wx.EVT_MENU, self.on_start_change_coord_system_operation, id=wx.ID_FILE3)
        self.toolbar.Bind(wx.EVT_TOOL, self.on_open_dxf, id=wx.ID_FILE1)
        self.toolbar.Bind(wx.EVT_TOOL, self.on_open_csv, id=wx.ID_FILE2)
        self.mgr.Bind(wx.aui.EVT_AUI_PANE_CLOSE, self.on_pane_closed)
        self.plot.Bind(EVT_PLOT_CLICK, self.on_plot_click)

    def on_plot_click(self, event):
        if self.operation is not None:
            self.operation.on_event(event)

    def on_pane_closed(self, event):
        if self.operation is not None:
            self.operation.on_event(event)

    def on_open_dxf(self, event):
        with wx.FileDialog(self, "Open XYZ file", wildcard="DXF files (*.dxf)|*.dxf", style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return
            import ezdxf
            
            doc = ezdxf.readfile(fileDialog.GetPath())
            object = DxfPlot(fileDialog.GetPath(), affine_transform_filename=None, data=doc)
            object.data = doc
            for layer in doc.layers:
                object.layers.append(DxfPlotLayer(layer.dxf.name, self.plot.add_group()))
            layer_group_mapping = {}
            for layer in object.layers:
                layer_group_mapping[layer.name] = layer.group 
            self.plot.dxf_load(doc, layer_group_mapping, affine=None)
            self.objects.append(object)
            self.object.update(self.objects)

    def delete_object(self, object):
        if object in self.objects:
            self.objects.remove(object)
            if isinstance(object, DxfPlot):
                for layer in object.layers:
                    if layer.visible:
                        self.plot.clear_group(layer.group)

    def update_visibility(self, object):
        if isinstance(object, DxfPlot):
            for layer in object.layers:
                self.plot.set_group_visibility(layer.group, layer.visible)
                
    def on_open_csv(self, event):
        dlg = SeismicImport(self)
        if dlg.ShowModal() == wx.ID_OK:
            ...

    def on_start_change_coord_system_operation(self, event):
        def end():
            self.operation = None

        self.operation = ChangeCoordSystemOperation(self.mgr, self.plot, end)
        self.operation.init()

if __name__ == '__main__':
    from ctx import app_ctx

    app = wx.App(0)
    main = MainWindow()
    app_ctx().main = main
    app.MainLoop()
