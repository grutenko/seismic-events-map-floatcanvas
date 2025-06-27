import wx
import wx.aui
import wx.dataview as dv
import os

from ctx import app_ctx
from icon import get_art
from object_data import DxfPlot
from plot import PlotClickEvent

class FloatEditor(dv.DataViewTextRenderer):
    def __init__(self, *args, **kwds):
        super().__init__(*args, **kwds)

    def OnEditingDone(self, value):
        try:
            fval = float(value)
            return str(fval)
        except ValueError:
            return None

class Panel(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent)
        self.points = []
        sz_box = wx.BoxSizer(wx.VERTICAL)
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
        self.list_store = dv.DataViewListStore()
        self.list_store.AppendColumn("string")
        self.list_store.AppendColumn("string")
        self.list_store.AppendColumn("string")
        self.list_store.AppendColumn("string")
        self.list = dv.DataViewCtrl(self, style=dv.DV_ROW_LINES | dv.DV_VERT_RULES)
        self.list.AppendColumn(dv.DataViewColumn('X0', FloatEditor(varianttype="string", mode=dv.DATAVIEW_CELL_EDITABLE), 0, 50))
        self.list.AppendColumn(dv.DataViewColumn('Y0', FloatEditor(varianttype="string", mode=dv.DATAVIEW_CELL_EDITABLE), 1, 50))
        self.list.AppendColumn(dv.DataViewColumn('X1', FloatEditor(varianttype="string", mode=dv.DATAVIEW_CELL_EDITABLE), 2, 50))
        self.list.AppendColumn(dv.DataViewColumn('Y1', FloatEditor(varianttype="string", mode=dv.DATAVIEW_CELL_EDITABLE), 3, 50))
        self.list.AssociateModel(self.list_store)
        sz.Add(self.list, 1, wx.EXPAND | wx.BOTTOM, border=10)
        self.btn_apply = wx.Button(self, label="Применить")
        self.btn_apply.Disable()
        sz.Add(self.btn_apply, 0, wx.EXPAND)
        sz_box = wx.BoxSizer(wx.VERTICAL)
        sz_box.Add(sz, 1, wx.EXPAND | wx.ALL, border=5)
        self.SetSizer(sz_box)
        self.Layout()

class SetCoordsDialog(wx.Dialog):
    def __init__(self, parent):
        super().__init__(parent, title="Кординаты точки в другой системе")
        sz_border = wx.BoxSizer(wx.VERTICAL)
        sz = wx.BoxSizer(wx.VERTICAL)
        label = wx.StaticText(self, label="X")
        sz.Add(label, 0, wx.EXPAND)
        self.x_field = wx.SpinCtrlDouble(self, min=-1000000.0, max=10000000.0)
        self.x_field.SetDigits(5)
        sz.Add(self.x_field, 0, wx.EXPAND | wx.BOTTOM, border=10)
        self.y_field = wx.SpinCtrlDouble(self, min=-1000000.0, max=10000000.0)
        self.y_field.SetDigits(5)
        sz.Add(self.y_field, 0, wx.EXPAND | wx.BOTTOM, border=10)
        self.btn_ok = wx.Button(self, label="ОК")
        self.btn_ok.Bind(wx.EVT_BUTTON, self.on_apply)
        sz.Add(self.btn_ok, 0, wx.RIGHT)
        sz_border.Add(sz, 1, wx.EXPAND | wx.ALL, border=10)
        self.SetSizer(sz_border)
        self.Layout()
        self.Fit()

    def on_apply(self, event):
        print(event)
        self.EndModal(wx.ID_OK)

class ChangeCoordSystemOperation:
    def __init__(self, mgr, plot, end):
        self.mgr = mgr
        self.plot = plot
        self.end_fn = end
        self.mgr_pane_info = None
        self.points = []

    def init(self):
        panel = Panel(app_ctx().main)
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
        panel.list.Bind(dv.EVT_DATAVIEW_SELECTION_CHANGED, self.on_item_selection_changed)
        self.panel = panel

    def on_item_selection_changed(self, event):
        self.update_controls_state()

    def on_add_handmade(self, event):
      import wx.lib.floatcanvas.FCObjects
      self.panel.list_store.AppendItem(["0.0", "0.0", "0.0", "0.0"])
      point = wx.lib.floatcanvas.FCObjects.Point((event.world_pos[0], event.world_pos[1]),
        Diameter=5,              # диаметр в пикселях на экране
        Color="RED",
        InForeground=True)
      self.plot.canvas.AddObject(point)
      self.plot.canvas.Draw()
      self.points.append((0.0, 0.0, point))

    def on_remove(self, event):
        if self.panel.list.GetSelection() != -1:
            row = self.panel.list_store.GetRow(self.panel.list.GetSelection())
            self.panel.list_store.DeleteItem(row)
            self.plot.canvas.RemoveObject(self.points[row][2])
            self.points.pop(row)
            self.plot.canvas.Draw()

    def cancel(self):
        self.plot.SetCursor(wx.NullCursor)
        self.mgr.ClosePane(self.mgr_pane_info)
        self.mgr.Update()
        self.mgr_pane_info = None
        for x, y, obj in self.points:
            self.plot.canvas.RemoveObject(obj)
        self.points = []
        self.plot.canvas.Draw()

    def update_list(self): ...

    def update_controls_state(self):
        self.panel.list_toolbar.EnableTool(wx.ID_REMOVE, self.panel.list.GetSelection() != -1)

    def on_plot_click(self, event):
        import wx.lib.floatcanvas.FCObjects
        dlg = SetCoordsDialog(app_ctx().main)
        if dlg.ShowModal() == wx.ID_OK:
            point = wx.lib.floatcanvas.FCObjects.Point((event.world_pos[0], event.world_pos[1]),
              Diameter=5,              # диаметр в пикселях на экране
              Color="RED",
              InForeground=True)
            self.plot.canvas.AddObject(point)
            self.plot.canvas.Draw()
            self.points.append((event.world_pos[0], event.world_pos[1], point))
            self.panel.list_store.AppendItem([str(event.world_pos[0]), str(event.world_pos[1]), str(dlg.x_field.GetValue()), str(dlg.y_field.GetValue())])

    def on_aui_pane_close(self, event):
      ret = wx.MessageBox("Отменить операцию?", style=wx.YES | wx.NO | wx.YES_DEFAULT | wx.ICON_ASTERISK)
      if ret == wx.NO:
          event.Veto()
      else:
          self.plot.SetCursor(wx.NullCursor)
          for x, y, obj in self.points:
              self.plot.canvas.RemoveObject(obj)
          self.points = []
          self.plot.canvas.Draw()
          self.end_fn()

    def on_event(self, event):
        if isinstance(event, wx.aui.AuiManagerEvent) and event.GetEventType() == wx.aui.EVT_AUI_PANE_CLOSE.typeId:
            pane = event.GetPane()
            if pane.name == "change_coord_system_pane":
                self.on_aui_pane_close(event)
        elif isinstance(event, PlotClickEvent):
          self.on_plot_click(event)
