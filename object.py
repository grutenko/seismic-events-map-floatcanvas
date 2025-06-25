import wx
import os

from object_data import DxfPlot, DxfPlotLayer
from icon import get_icon
from ctx import app_ctx

class ObjectsPanel(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent)
        sz = wx.BoxSizer(wx.VERTICAL)
        self.state_image_list = wx.ImageList(16, 16)
        self.icon_checked = self.state_image_list.Add(get_icon("checkbox-checked"))
        self.icon_unchecked = self.state_image_list.Add(get_icon("checkbox"))
        self.image_list = wx.ImageList(16, 16)
        self.icon_dxf = self.image_list.Add(get_icon("dxf"))
        self.icon_layer = self.image_list.Add(get_icon("layer"))
        self.tree = wx.TreeCtrl(self, style=wx.TR_DEFAULT_STYLE | wx.TR_HIDE_ROOT)
        self.tree.AssignImageList(self.image_list)
        self.tree.SetStateImageList(self.state_image_list)
        sz.Add(self.tree, 1, wx.EXPAND)
        self.SetSizer(sz)
        self.Layout()
        self.bind_all()
        self.current_object = None

    def bind_all(self):
        self.tree.Bind(wx.EVT_TREE_ITEM_ACTIVATED, self.on_object_activated)
        self.tree.Bind(wx.EVT_TREE_ITEM_MENU, self.on_object_menu_click)
        self.tree.Bind(wx.EVT_TREE_SEL_CHANGED, self.on_object_selected)
        self.tree.Bind(wx.EVT_TREE_STATE_IMAGE_CLICK, self.on_tree_state_image_click)

    def on_object_activated(self, event): ...

    def on_object_menu_click(self, event):
        item = event.GetItem()
        if not item.IsOk():
            return
        data = self.tree.GetItemData(item)
        self.current_object = data
        if isinstance(data, DxfPlot):
            m = wx.Menu()
            m.Append(wx.ID_DELETE, "Удалить объект")
            m.Bind(wx.EVT_MENU, lambda e: self.on_object_menu_delete(e, item), id=wx.ID_DELETE)
            self.PopupMenu(m, event.GetPoint())
        elif isinstance(data, DxfPlotLayer):
            app_ctx().main.delete_object(data)
            self.tree.Delete(item)

    def on_object_menu_delete(self, event, item):
        data = self.tree.GetItemData(item)
        if isinstance(data, DxfPlot):
            app_ctx().main.delete_object(data)
            self.tree.Delete(item)
        elif isinstance(data, DxfPlotLayer):
            app_ctx().main.delete_object(data)
            self.tree.Delete(item)

    def on_object_selected(self, event): ...

    def on_tree_state_image_click(self, event):
        item = event.GetItem()
        if not item.IsOk():
            return
        data = self.tree.GetItemData(item)
        if isinstance(data, DxfPlot):
            data.visible = not data.visible
            self.tree.SetItemState(item, self.icon_checked if data.visible else self.icon_unchecked)
            self.tree.Refresh()
            child, cookie = self.tree.GetFirstChild(item)
            while child.IsOk():
                layer_data = self.tree.GetItemData(child)
                if isinstance(layer_data, DxfPlotLayer):
                    layer_data.visible = data.visible
                    self.tree.SetItemState(child, self.icon_checked if layer_data.visible else self.icon_unchecked)
                child, cookie = self.tree.GetNextChild(item, cookie)
            app_ctx().main.update_visibility(data)
        elif isinstance(data, DxfPlotLayer):
            data.visible = not data.visible
            self.tree.SetItemState(item, self.icon_checked if data.visible else self.icon_unchecked)
            self.tree.Refresh()
            parent = self.tree.GetItemParent(item)
            if not parent.IsOk():
                return
            self.tree.SetItemState(parent, self.icon_checked if data.visible else self.icon_unchecked)
            parent_data = self.tree.GetItemData(parent)
            app_ctx().main.update_visibility(parent_data)

    def update(self, objects):
        self.tree.DeleteAllItems()
        self.tree.AddRoot("Объекты")
        for o in objects:
            if isinstance(o, DxfPlot):
                plot = self.tree.AppendItem(self.tree.GetRootItem(), "(объект)" + os.path.basename(o.filename), self.icon_dxf)
                self.tree.SetItemState(plot, self.icon_checked if o.visible else self.icon_unchecked)
                self.tree.SetItemData(plot, o)
                self.tree.SetItemBold(plot, True)
                for layer in o.layers:
                    item = self.tree.AppendItem(plot, layer.name, self.icon_layer, self.icon_layer)
                    self.tree.SetItemState(item, self.icon_checked if layer.visible else self.icon_unchecked)
                    self.tree.SetItemData(item, layer)
