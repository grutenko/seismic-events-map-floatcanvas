import wx
import lib.litecad as lc
import ctypes
import ctypes.wintypes as wt
from dataclasses import dataclass
from typing import List
import time

from src.ui.widgets.color_scheme import ColorScheme, get_interpol_color_by_pos
from src.ui.widgets.ruler import RulerWidget


@dataclass
class Event:
    x: float
    y: float
    z: float
    energy: float
    primitives: List[wt.HANDLE]


@dataclass
class EventsCollection:
    lc_layer_handle: wt.HANDLE
    events: List[Event]


class PlotWidget(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent)
        self.lc_drw = None
        self.lc_wnd = None
        self.color_scheme = None
        self.objects = []
        self.ruler_update_time = time.time()
        sz = wx.FlexGridSizer(2, 2, 0, 0)
        sz.AddGrowableCol(1)
        sz.AddGrowableRow(1)
        deputy = wx.Panel(self)
        deputy.SetBackgroundColour(wx.Colour(255, 255, 255))
        self.hz_ruler = RulerWidget(self, parts=10)
        self.vt_ruler = RulerWidget(self, orientation=wx.VERTICAL, invert=True, parts=10)
        self.canvas = wx.Panel(self)
        sz.Add(deputy)
        sz.Add(self.hz_ruler, 1, wx.EXPAND)
        sz.Add(self.vt_ruler, 1, wx.EXPAND)
        sz.Add(self.canvas, 1, wx.EXPAND)
        self.SetSizer(sz)
        self.Layout()

        self.canvas.Bind(wx.EVT_SIZE, self.on_canvas_size)
        self.init_litecad(self.canvas)

    def update_rulers(self):
        #Временный(скорей всего) костыль, чтобы не тормозило панаромирование чертежа. Нужно найти более элегантное решение
        #которое будет сочетать этот костыль и конечное обновление линейки после отпускания EVT_MIDDLE_UP чтобы
        #обновить линейку по окончании процедуры панаромирования а так же не подвешивать постоянной её перерисовкой
        t = time.time()
        if (time.time() - self.ruler_update_time) >=(1 / 60):
            x0 = ctypes.c_double()
            y0 = ctypes.c_double()
            x1 = ctypes.c_double()
            y1 = ctypes.c_double()
            width, height = self.GetSize().Get()
            if width == 0 or height == 0:
                return
            lc.lcCoordWndToDrw(self.lc_wnd, 0, 0, ctypes.pointer(x0), ctypes.pointer(y0))
            lc.lcCoordWndToDrw(self.lc_wnd, width, height, ctypes.pointer(x1), ctypes.pointer(y1))
            width, height = self.GetSize().Get()
            self.hz_ruler.set_offset(-x0.value, False)
            self.hz_ruler.set_scale(width / abs(x1.value - x0.value), False)
            self.vt_ruler.set_offset(-y1.value, False)
            self.vt_ruler.set_scale(height / (y0.value - y1.value), False)
            self.vt_ruler.draw()
            self.hz_ruler.draw()
            self.ruler_update_time = t

    def on_canvas_size(self, event):
        rc = lc.lcWndResize(
            self.lc_wnd, 0, 0, event.GetSize().GetWidth(), event.GetSize().GetHeight()
        )
        if rc == 0:
            raise Exception(lc.lcGetErrorStr())
        event.Skip()
        self.update_rulers()

    def init_litecad(self, panel):
        w, h = panel.Size  # Размеры рабочего поля 2D
        lc_wnd = lc.lcCreateWindow(
            panel.GetHandle(), lc.LC_WS_DEFAULT
        )  # ^lc.LC_WS_RULERS #Sozdanie okna s privyazkoy k okny interfeisa
        print("Инициализация окна CADa lc_wnd=", lc_wnd)
        lc.lcWndResize(lc_wnd, 0, 0, w, h)  #
        lc.lcPropPutBool(lc_wnd, lc.LC_PROP_WND_SELECT, True)
        # On/Off vydelenye mysh'y
        lc.lcPropPutBool(lc_wnd, lc.LC_PROP_WND_GRIDSHOW, True)
        # On/Off setka na fone
        lc_drw = lc.lcCreateDrawing()  # Sozdanie objecta otrisovki
        print("Инициализация изображения CAD" "a lc_drw=", lc_drw)
        lc.lcPropPutInt(
            lc_drw, lc.LC_PROP_DRW_COLORBACKP, 255 * 65536 + 255 * 256 + 255
        )
        lc.lcPropPutInt(
            lc_drw, lc.LC_PROP_DRW_COLORBACKM, 255 * 65536 + 255 * 256 + 255
        )  # Cvet zadnego fona B*65535_G*256_R
        lc.lcPropPutInt(
            lc_wnd, lc.LC_PROP_WND_GRIDCOLOR, 252 * 65536 + 86 * 256 + 97
        )  # Cvet GRID'a B*65535_G*256_R
        hBlock = lc.lcPropGetHandle(lc_drw, lc.LC_PROP_DRW_BLOCK_MODEL)
        lc.lcPropPutBool(lc_wnd, lc.LC_PROP_WND_DRAWPAPER, False)
        print("Инициализация блока CAD" "a hBlock=", hBlock)
        lc.lcWndSetBlock(lc_wnd, hBlock)
        # Vybrat' block kotoriy bydet otobrajat'sya v okne
        lc.lcBlockUpdate(hBlock, True, 0)
        # Obnovlyaet block i vse objekty
        lc.lcWndExeCommand(lc_wnd, lc.LC_CMD_ZOOM_EXT, 0)
        # Vypolnyaet comandy 'Priblizit' k ob'ekty otrisovki'
        lc.lcWndSetFocus(lc_wnd)
        # Delaet aktivnym dlya klaviatury okino
        lc.lcPropPutBool(lc_wnd, lc.LC_PROP_WND_STDBLKFRAME, False)
        # On/Off Ramka blocka
        lc.lcPropPutBool(
            lc_drw, lc.LC_PROP_DRW_LOCKSEL, True
        )  # On/Off Select locked elements
        lc.lcPropPutFloat(lc_wnd, lc.LC_PROP_WND_GRIDDX, 10.0)
        lc.lcPropPutFloat(lc_wnd, lc.LC_PROP_WND_GRIDDY, 10.0)
        lc.lcPropPutBool(lc_wnd, lc.LC_PROP_WND_GRIDDOTTED, True)
        # lc.lcPropPutBool( lc_wnd, lc.LC_PROP_WND_RULERS, True) #Отображение линейки LiteCAD'a
        self.text_style = lc.lcDrwAddTextStyle(self.lc_drw, "ArialStyle", "Arial", True)
        self.lc_wnd = lc_wnd
        self.lc_drw = lc_drw

    def on_lc_event(self, EventType, action):
        if EventType == lc.LC_EVENT_WNDVIEW:
            self.update_rulers()
        return 0

    def save(self, path):
        pass

    def can_save(self):
        return False

    def can_undo(self):
        return True

    def undo(self):
        lc.lcWndExeCommand(self.lc_wnd, lc.LC_CMD_UNDO, 0)

    def can_redo(self):
        return True

    def redo(self):
        lc.lcWndExeCommand(self.lc_wnd, lc.LC_CMD_REDO, 0)

    def can_copy(self):
        return True

    def copy(self):
        pass

    def can_cut(self):
        return True

    def cut(self):
        pass

    def can_paste(self):
        return True

    def paste(self):
        pass

    def zoom_in(self):
        lc.lcWndExeCommand(self.lc_wnd, lc.LC_CMD_ZOOM_IN, 0)

    def zoom_out(self):
        lc.lcWndExeCommand(self.lc_wnd, lc.LC_CMD_ZOOM_OUT, 0)

    def zoom_to_bb(self):
        lc.lcWndExeCommand(self.lc_wnd, lc.LC_CMD_ZOOM_EXT, 0)

    def add_events(self, table, coord_system):
        def n2text(n):
            n_text = ""
            if n < 100:
                return str(n)
            else:
                e = 0
                while n >= 10:
                    n /= 10
                    e += 1
                n_text = f"{n:.2f}".rstrip("0").rstrip(".") + f"x10^{e}"
            return str(n_text)

        import math

        hBlock = lc.lcPropGetHandle(self.lc_wnd, lc.LC_PROP_WND_BLOCK)
        LayerLineType = lc.lcDrwGetObjectByName(
            self.lc_drw, lc.LC_OBJ_LINETYPE, "CONTINUOUS"
        )
        Layer = lc.lcDrwAddLayer(self.lc_drw, "Контуры", "0,0,0", LayerLineType, 0)
        lc.lcPropPutInt(Layer, lc.LC_PROP_LAYER_COLORI, 255)
        lc.lcPropPutBool(Layer, lc.LC_PROP_LAYER_LOCKED, True)
        lc.lcPropPutBool(Layer, lc.LC_PROP_LAYER_VISIBLE, True)
        collection = EventsCollection(Layer, [])
        for event in table:
            x = float(event[0])
            y = float(event[1])
            z = float(event[2])
            energy = float(event[3])
            if self.color_scheme is not None:
                r, g, b, a = get_interpol_color_by_pos(self.color_scheme, energy).Get()
                color = "%d,%d,%d" % (r, g, b)
            else:
                color = "0,0,0"
            radius = 5 * math.log(energy)
            p = lc.lcBlockAddCircle(hBlock, x, y, 5 * math.log(energy), False)
            hLineType = lc.lcDrwGetObjectByName(
                self.lc_drw, lc.LC_OBJ_LINETYPE, "CONTINUOUS"
            )
            lc.lcPropPutHandle(p, lc.LC_PROP_ENT_LINETYPE, hLineType)
            lc.lcPropPutStr(p, lc.LC_PROP_ENT_COLOR, color)
            lc.lcPropPutFloat(p, lc.LC_PROP_ENT_LTSCALE, 1.0)
            lc.lcPropPutHandle(p, lc.LC_PROP_ENT_LAYER, Layer)
            t = lc.lcBlockAddTextWin2(
                hBlock, n2text(energy), x, y - 8, 0, 16.0, 1.0, 0, 0
            )
            lc.lcPropPutStr(t, lc.LC_PROP_ENT_COLOR, color)
            lc.lcPropPutHandle(t, lc.LC_PROP_TEXT_STYLE, self.text_style)
            lc.lcPropPutHandle(t, lc.LC_PROP_ENT_LAYER, Layer)
            point = lc.lcBlockAddPoint(hBlock, x, y)
            lc.lcPropPutStr(point, lc.LC_PROP_ENT_COLOR, color)
            lc.lcPropPutHandle(point, lc.LC_PROP_ENT_LAYER, Layer)
            collection.events.append(Event(x, y, z, energy, [p, t, point]))
        self.objects.append(collection)
        lc.lcBlockUpdate(hBlock, True, 0)

        lc.lcWndExeCommand(self.lc_wnd, lc.LC_CMD_ZOOM_EXT, 0)

    def apply_color_scheme(self, color_scheme: ColorScheme):
        self.color_scheme = color_scheme
        self.repaint()

    def repaint(self):
        hBlock = lc.lcPropGetHandle(self.lc_wnd, lc.LC_PROP_WND_BLOCK)
        for object in self.objects:
            if isinstance(object, EventsCollection):
                for event in object.events:
                    for prim in event.primitives:
                        energy = event.energy
                        if self.color_scheme is not None:
                            r, g, b, a = get_interpol_color_by_pos(self.color_scheme, energy).Get()
                            color = "%d,%d,%d" % (r, g, b)
                        else:
                            color = "0,0,0"
                        print(color)
                        lc.lcPropPutStr(prim, lc.LC_PROP_ENT_COLOR, color)
        lc.lcBlockUpdate(hBlock, True, 0)
        lc.lcWndRedraw(self.lc_wnd)
