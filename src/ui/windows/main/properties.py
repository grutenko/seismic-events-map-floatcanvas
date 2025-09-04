import wx
import wx.lib.newevent
import wx.propgrid
from wx.lib.agw.flatnotebook import (
    FlatNotebook,
    FNB_NO_NAV_BUTTONS,
    EVT_FLATNOTEBOOK_PAGE_CLOSING,
)

from src.ui.widgets.color_scheme import (
    draw_gradient,
    ColorScheme,
    INTERPOL_MODE_LINEAR,
    ColorSchemeProperty,
    GradientEditor
)

CloseEvent, EVT_PROPS_CLOSE = wx.lib.newevent.NewEvent()
ChangedEvent, EVT_PROPS_CHANGED = wx.lib.newevent.NewEvent()


class Properties(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent)
        sz = wx.BoxSizer(wx.VERTICAL)
        self.n = FlatNotebook(self, agwStyle=FNB_NO_NAV_BUTTONS)
        self.pg = wx.propgrid.PropertyGrid(self, style=wx.propgrid.PG_SPLITTER_AUTO_CENTER)
        self.pg.RegisterEditor(GradientEditor(), "gradient")
        pp: wx.propgrid.PGProperty = self.pg.Append(
            ColorSchemeProperty(
                "Цветовая схема",
                "levels",
                ColorScheme.basic(
                    wx.Colour(0, 0, 255), 0, wx.Colour(255, 0, 0), 100
                ), 
            )
        )
        pp.SetEditor("gradient")
        self.n.AddPage(self.pg, "Параметры отрисовки")
        sz.Add(self.n, 1, wx.EXPAND)
        self.SetSizer(sz)
        self.Layout()
        self.Bind(EVT_FLATNOTEBOOK_PAGE_CLOSING, self.on_close)
        self.pg.Bind(wx.propgrid.EVT_PG_CHANGED, self.on_changed)

    def on_changed(self, event):
        wx.PostEvent(self, ChangedEvent())

    def set_color_scheme(self, color_scheme: ColorScheme):
        self.pg.SetPropertyValue("levels", color_scheme)

    def get_color_scheme(self) -> ColorScheme:
        return self.pg.GetPropertyValue('levels')

    def on_close(self, event):
        event.Veto()
        wx.PostEvent(self, CloseEvent())
