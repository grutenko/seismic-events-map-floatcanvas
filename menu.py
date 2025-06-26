import wx

from icon import get_icon

class MainMenu(wx.MenuBar):
    def __init__(self):
        super().__init__()
        m = wx.Menu()
        i = m.Append(wx.ID_FILE1, "Загрузить DXF подложку")
        i.SetBitmap(get_icon("dxf"))
        i = m.Append(wx.ID_FILE2, "Загрузить сейсмические события")
        i.SetBitmap(get_icon("csv"))
        self.Append(m, "Файл")
        m = wx.Menu()
        self.Append(m, "Правка")
        m = wx.Menu()
        self.Append(m, "Вид")
        m = wx.Menu()
        i = m.Append(wx.ID_FILE3, "Смена системы координат")
        self.Append(m, "Операции")
        m = wx.Menu()
        self.Append(m, "Помощь")
