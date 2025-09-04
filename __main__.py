import wx

from src.ui.windows.main import MainWindow

if __name__ == "__main__":
    app = wx.App(0)
    m = MainWindow()
    app.SetTopWindow(m)
    app.MainLoop()