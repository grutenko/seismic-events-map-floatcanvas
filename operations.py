import wx
import wx.aui
import wx.dataview
import os

from ctx import app_ctx
from icon import get_art
from object_data import DxfPlot

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
            self.list_toolbar.AddTool(wx.ID_ADD, "Добавить", wx.BitmapBundle(get_art(wx.ART_PLUS)))
            self.list_toolbar.AddTool(wx.ID_REMOVE, "Удалить", wx.BitmapBundle(get_art(wx.ART_MINUS)))
            self.list_toolbar.EnableTool(wx.ID_REMOVE, False)
            self.list_toolbar.Realize()
            sz.Add(self.list_toolbar, 0, wx.EXPAND)
            self.list_store = wx.dataview.DataViewListStore()
            self.list_store.AppendColumn("float")
            self.list_store.AppendColumn("float")
            self.list_store.AppendColumn("float")
            self.list_store.AppendColumn("float")
            self.list = wx.dataview.DataViewListCtrl(self, style=wx.dataview.DV_ROW_LINES | wx.dataview.DV_VERT_RULES)
            self.list.AppendTextColumn("X0", width=50, mode=wx.dataview.DATAVIEW_CELL_EDITABLE)
            self.list.AppendTextColumn("Y0", width=50, mode=wx.dataview.DATAVIEW_CELL_EDITABLE)
            self.list.AppendTextColumn("X1", width=50, mode=wx.dataview.DATAVIEW_CELL_EDITABLE)
            self.list.AppendTextColumn("Y1", width=50, mode=wx.dataview.DATAVIEW_CELL_EDITABLE)
            self.list.AssociateModel(self.list_store)
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
            .FloatingPosition(100, 100)
            .FloatingSize(200, 400)
            .Dockable(False)
            .DestroyOnClose(True)
            .Name("change_coord_system_pane")
            .Caption("Операция: смена системы"))
        self.mgr.AddPane(panel, self.mgr_pane_info)
        self.plot.SetCursor(wx.Cursor(wx.CURSOR_HAND))
        self.mgr.Update()
        panel.list_toolbar.Bind(wx.EVT_TOOL, self.on_add_handmade, id=wx.ID_ADD)
        panel.list_toolbar.Bind(wx.EVT_TOOL, self.on_remove, id=wx.ID_REMOVE)
        panel.list.Bind(wx.dataview.EVT_DATAVIEW_ITEM_ACTIVATED, self.on_item_activated)
        self.panel = panel

    def on_item_activated(self, event):
        self.update_controls_state()

    def on_add_handmade(self, event):
        self.panel.list_store.AppendItem(["", "", "", ""])

    def on_remove(self, event):
        ...

    def cancel(self):
        self.plot.SetCursor(wx.NullCursor)
        self.mgr.ClosePane(self.mgr_pane_info)
        self.mgr.Update()
        self.mgr_pane_info = None

    def update_list(self): ...

    def update_controls_state(self):
        self.panel.list_toolbar.EnableTool(wx.ID_REMOVE, self.panel.list.GetSelectedRow() != -1)

    class SetCoordsDialog(wx.Dialog):
      def __init__(self, parent):
        super().__init__(parent, title="Кординаты точки в другой системе")

    def on_plot_click(self, event):
        dlg = self.__class__.SetCoordsDialog(app_ctx().main)
        if dlg.ShowModal() == wx.ID_OK:
            ...

    def on_aui_pane_close(self, event):
      ret = wx.MessageBox("Отменить операцию?", style=wx.YES | wx.NO | wx.YES_DEFAULT | wx.ICON_ASTERISK)
      if ret == wx.NO:
          event.Veto()
      else:
          self.plot.SetCursor(wx.NullCursor)
          self.end_fn()

    def on_event(self, event):
        if isinstance(event, wx.aui.AuiManagerEvent) and event.GetEventType() == wx.aui.EVT_AUI_PANE_CLOSE.typeId:
            pane = event.GetPane()
            if pane.name == "change_coord_system_pane":
                self.on_aui_pane_close(event)
        elif isinstance(event, PlotClickEvent):
          self.on_plot_click(event)
