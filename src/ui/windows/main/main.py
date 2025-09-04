import wx
import wx.lib.agw.flatnotebook
import lib.litecad as lc
import ctypes as ct
import ctypes.wintypes as wt

from src.ui.windows.import_seismic_data import SeismicImport
from .plot import PlotWidget
from .menu import MainMenu
from .toolbar import MainToolbar
from .statusbar import MainStatubar
from .properties import Properties, EVT_PROPS_CLOSE, EVT_PROPS_CHANGED


class MainWindow(wx.Frame):
    def __init__(self):
        super().__init__(None, title="Карта сейсмических событий", size=wx.Size(800, 600))
        self.menu = MainMenu()
        self.toolbar = MainToolbar(self)
        self.statusbar = MainStatubar(self)
        self.SetMenuBar(self.menu)
        self.SetToolBar(self.toolbar)
        self.SetStatusBar(self.statusbar)
        sz = wx.BoxSizer(wx.VERTICAL)
        self.sw = wx.SplitterWindow(self, style=wx.SP_3D | wx.SP_LIVE_UPDATE)
        self.sw.SetSashGravity(1)
        self.sw.SetMinimumPaneSize(250)
        self.plot = PlotWidget(self.sw)
        self.properties = Properties(self.sw)
        self.plot.apply_color_scheme(self.properties.pg.GetPropertyValue("levels"))
        self.sw.SplitVertically(self.plot, self.properties, 300)
        sz.Add(self.sw, 1, wx.EXPAND)
        self.SetSizer(sz)
        self.Layout()
        self.InitLiteCad_DLL()
        self.bind_all()
        self.Show()

    def bind_all(self):
        self.menu.Bind(wx.EVT_MENU, self.on_open, id=wx.ID_OPEN)
        self.menu.Bind(wx.EVT_MENU, self.on_undo, id=wx.ID_UNDO)
        self.menu.Bind(wx.EVT_MENU, self.on_redo, id=wx.ID_REDO)
        self.toolbar.Bind(wx.EVT_TOOL, self.on_open, id=wx.ID_OPEN)
        self.toolbar.Bind(wx.EVT_TOOL, self.on_undo, id=wx.ID_UNDO)
        self.toolbar.Bind(wx.EVT_TOOL, self.on_redo, id=wx.ID_REDO)
        self.toolbar.Bind(wx.EVT_TOOL, self.on_zoom_in, id=wx.ID_ZOOM_IN)
        self.toolbar.Bind(wx.EVT_TOOL, self.on_zoom_out, id=wx.ID_ZOOM_OUT)
        self.toolbar.Bind(wx.EVT_TOOL, self.on_zoom_fit, id=wx.ID_ZOOM_FIT)
        self.properties.Bind(EVT_PROPS_CLOSE, self.on_props_close)
        self.properties.Bind(EVT_PROPS_CHANGED, self.on_props_changed)
        self.Bind(wx.EVT_CLOSE, self.on_close)

        CMPFUNC = ct.CFUNCTYPE(None, wt.HANDLE)  # Регистрация процедуры событий
        self.LcEventProc = CMPFUNC(self.LcEventProc)  # Регистрация процедуры событий
        lc.lcEventSetProc(lc.LC_EVENT_MOUSEMOVE, self.LcEventProc, 0, self.LcEventProc)
        lc.lcEventSetProc(lc.LC_EVENT_WNDVIEW, self.LcEventProc, 0, self.LcEventProc)

    def on_props_changed(self, event):
        self.plot.apply_color_scheme(self.properties.get_color_scheme())

    def on_props_close(self, event):
        self.sw.Unsplit(self.properties)

    def InitLiteCad_DLL(self):
        lc.lcPropPutStr(
            0, lc.LC_PROP_G_REGCODE, "cdda-e9ce-9eb7-1d89"
        )  # Серийник от библиотеки
        # lc.lcPropPutStr( 0, lc.LC_PROP_G_RULERBMP, "C:\Serg\sigmaview\icon.bmp")
        lc.lcPropPutBool(0, lc.LC_PROP_G_PANREDQUAL, True)
        print("Version:", lc.lcPropGetStr(0, lc.LC_PROP_G_VERSION))
        print("Directory:", lc.lcPropGetStr(0, lc.LC_PROP_G_DIRDLL))
        self.lc_job = lc.lcInitialize()  # Инициализация CAD'a)
        print("Инициализация CADa lc_job=", self.lc_job)
        print(lc.lcPropPutBool(0, lc.LC_PROP_SEL_PICKADD, True))
        # Настройка цветов и режимов выделения примитивов
        lc.lcPropPutBool(0, lc.LC_PROP_SEL_GRIPNUM, False)  # Отключаем нумирацию точек
        lc.lcPropPutBool(
            0, lc.LC_PROP_SEL_HATCHFILL, False
        )  # Отключаем штриховку замкнутых областей
        lc.lcPropPutInt(
            0, lc.LC_PROP_SEL_GRIPCOLORF, 0
        )  # Цвет точек на римитивах - черный
        lc.lcPropPutInt(
            0, lc.LC_PROP_SEL_COLORF, lc.lcColorRGB(255, 255, 255)
        )  # Цвет заливки выбранной области - белый

    def LcEventProc(self, action):
        return self.plot.on_lc_event(
            lc.lcPropGetInt(action, lc.LC_PROP_EVENT_TYPE), action
        )
    
    def on_close(self, event):
        event.Skip()

    def on_undo(self, event):
        self.plot.undo()

    def on_redo(self, event):
        self.plot.redo()

    def on_zoom_fit(self, event):
        self.plot.zoom_to_bb()

    def on_zoom_in(self, event):
        self.plot.zoom_in()

    def on_zoom_out(self, event):
        self.plot.zoom_out()

    def on_open(self, event):
        dlg = SeismicImport(self)
        if dlg.ShowModal() == wx.ID_OK:
            self.plot.add_events(dlg.get_table(), dlg.get_coord_system())
