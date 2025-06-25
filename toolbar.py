import wx
import wx.aui

from icon import get_icon

class MainToolbar(wx.aui.AuiToolBar):
    def __init__(self, parent):
        super().__init__(parent)
        self.AddTool(wx.ID_FILE1, "Загрузить DXF подложку", get_icon("dxf"))
        self.AddTool(wx.ID_FILE2, "Загрузить данные", get_icon("csv"))
        self.Realize()

