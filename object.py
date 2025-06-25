import wx
import os

from object_data import DxfPlot
from icon import get_icon

class ObjectsPanel(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent)
        sz = wx.BoxSizer(wx.VERTICAL)
        self.tree = wx.TreeCtrl(self, style=wx.TR_DEFAULT_STYLE | wx.TR_HIDE_ROOT)
        sz.Add(self.tree, 1, wx.EXPAND)
        self.SetSizer(sz)
        self.Layout()

    def update(self, objects):
        self.tree.DeleteAllItems()
        self.tree.AddRoot("Объекты")
        for o in objects:
            if isinstance(o, DxfPlot):
                plot = self.tree.AppendItem(self.tree.GetRootItem(), os.path.basename(o.filename))
                for layer in o.layers:
                    self.tree.AppendItem(plot, layer.name)
