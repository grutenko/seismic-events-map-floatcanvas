import wx
import wx.aui
import os

from ctx import app_ctx
from icon import get_art
from object_data import DxfPlot 
from plot import EVT_PLOT_CLICK, PlotClickEvent

class ChangeCoordSystemOperation:
    def __init__(self, mgr, plot, end):
        self.mgr = mgr
        self.plot = plot
        self.end_fn = end
        self.mgr_pane_info = None

    class Panel(wx.Panel):
        def __init__(self, parent):
            super().__init__(parent)
            self.points = []

            sz = wx.BoxSizer(wx.VERTICAL)
            self.choice = wx.Choice(self)
            for o in app_ctx().main.objects:
                if isinstance(o, DxfPlot):
                    self.choice.Append(os.path.basename(o.filename))
            label = wx.StaticText(self, label="Объект DXF")
            sz.Add(label, 0, wx.EXPAND)
            sz.Add(self.choice, 0, wx.EXPAND | wx.BOTTOM, border=10)
            self.list_toolbar = wx.ToolBar(self)
            self.list_toolbar.AddTool(wx.ID_ADD, "Добавить", get_art(wx.ART_PLUS))
            self.list_toolbar.AddTool(wx.ID_REMOVE, "Удалить", get_art(wx.ART_MINUS))
            self.list_toolbar.EnableTool(wx.ID_REMOVE, False)
            self.list_toolbar.Realize()
            sz.Add(self.list_toolbar, 0, wx.EXPAND)
            self.list = wx.ListCtrl(self, style=wx.LC_REPORT)
            self.list.AppendColumn("X0")
            self.list.AppendColumn("Y0")
            self.list.AppendColumn("X1")
            self.list.AppendColumn("Y1")
            sz.Add(self.list, 1, wx.EXPAND | wx.BOTTOM, border=10)
            self.btn_apply = wx.Button(self, label="Приаменить")
            self.btn_apply.Disable()
            sz.Add(self.btn_apply, 0, wx.EXPAND)
            self.SetSizer(sz)
            self.Layout()

    def init(self):
        panel = self.__class__.Panel(app_ctx().main)
        self.mgr_pane_info = (wx.aui.AuiPaneInfo()
            .Float()
            .FloatingPosition((100, 100))
            .FloatingSize((200, 400))
            .Dockable(False)
            .DestroyOnClose(True)
            .Name("change_coord_system_pane")
            .Caption("Операция: смена системы"))
        self.mgr.AddPane(panel, self.mgr_pane_info)
        self.plot.SetCursor(wx.Cursor(wx.CURSOR_HAND))
        self.mgr.Update()

    def cancel(self):
        self.plot.SetCursor(wx.NullCursor)
        self.mgr.ClosePane(self.mgr_pane_info)
        self.mgr.Update()
        self.mgr_pane_info = None

    def update_list(self): ...

    def on_event(self, event):
        if isinstance(event, wx.aui.AuiManagerEvent) and event.GetEventType() == wx.aui.EVT_AUI_PANE_CLOSE.typeId:
            pane = event.GetPane()
            if pane.name == "change_coord_system_pane":
                ret = wx.MessageBox("Отменить операцию?", style=wx.YES | wx.NO | wx.YES_DEFAULT | wx.ICON_ASTERISK)
                if ret == wx.NO:
                    event.Veto()
                else:
                    self.plot.SetCursor(wx.NullCursor)
                    self.end_fn()
        elif isinstance(event, PlotClickEvent):
            dlg = wx.Dialog(app_ctx().main, title="Кординаты точки в другой системе")
            dlg.ShowModal()

