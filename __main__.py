import wx

from plot import SeismicEventsMapPlot

class MainWindow(wx.Frame):
    def __init__(self):
        super().__init__(None, title='Карта сейсмических событий', size=wx.Size(800, 600))
        sz = wx.BoxSizer(wx.VERTICAL)
        self.plot = SeismicEventsMapPlot(self)
        sz.Add(self.plot, 1, wx.EXPAND)
        self.SetSizer(sz)
        self.Layout()
        self.Show()
        self.plot.dxf_load("test.dxf")

if __name__ == '__main__':
    app = wx.App(0)
    MainWindow()
    app.MainLoop()
