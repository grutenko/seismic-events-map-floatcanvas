import wx
import wx.propgrid
import dataclasses
import json
from typing import List

from src.ui.widgets.ruler import RulerWidget

INTERPOL_MODE_LINEAR = 0
INTERPOL_MODE_REVERSE = 1
INTERPOL_MODE_COSINE = 2
INTERPOL_MODE_FLAT_START = 3
INTERPOL_MODE_FLAT_MIDDLE = 4
INTERPOL_MODE_FLAT_END = 5


@dataclasses.dataclass
class ColorScheme:
    schema: List

    def min_pos(self):
        return min(map(lambda o: o[3], self.schema))

    def max_pos(self):
        return max(map(lambda o: o[3], self.schema))

    @classmethod
    def basic(cls, c0: wx.Colour, p0: float, c1: wx.Colour, p1: float):
        return cls(
            schema=[
                (c0.GetRed(), c0.GetGreen(), c0.GetBlue(), p0),
                (c1.GetRed(), c1.GetGreen(), c1.GetBlue(), p1),
            ]
        )

    def range(self):
        return abs(self.min_pos() - self.max_pos())

    def save(self, f):
        f.write(self.to_string())

    @classmethod
    def load(cls, f):
        s = f.read()
        return cls.from_string(s)

    def to_string(self):
        schema = list(map(lambda o: list(o), self.schema))
        return json.dumps(schema)

    @classmethod
    def from_string(cls, json_str: str):
        schema = json.loads(json_str)
        schema = list(map(lambda o: (o[0], o[1], o[2], o[3]), schema))
        return cls(sorted(schema, key=lambda o: o[3]))

    @classmethod
    def from_paraview(cls, paraview_rgb_list):
        def chunks(lst, n):
            """Yield successive n-sized chunks from lst."""
            for i in range(0, len(lst), n):
                yield lst[i : i + n]

        schema = []
        for o in chunks(paraview_rgb_list, 4):
            schema.append(
                (
                    int(255 * o[1]),
                    int(255 * o[2]),
                    int(255 * o[3]),
                    o[0],
                )
            )

        return cls(sorted(schema, key=lambda o: o[3]))

    def to_paraview(self):
        schema = []
        for o in self.schema:
            schema.append(o[3])
            schema.append(o[0] / 256)
            schema.append(o[1] / 256)
            schema.append(o[2] / 256)
        return schema
    
    def clone(self) -> 'ColorScheme':
        return ColorScheme(schema=self.schema)


def interpol(c0, c1, ratio):
    r = int(c0[0] + ratio * (c1[0] - c0[0]))
    g = int(c0[1] + ratio * (c1[1] - c0[1]))
    b = int(c0[2] + ratio * (c1[2] - c0[2]))
    return wx.Colour(r, g, b)


def get_interpol_color_by_pos(
    color_scheme: ColorScheme, pos: float, mode=INTERPOL_MODE_LINEAR
):
    if len(color_scheme.schema) == 0:
        return wx.Colour(0, 0, 0)

    if pos < color_scheme.min_pos():
        return color_scheme.schema[0].slice(0, 3)

    for i in range(len(color_scheme.schema) - 1):
        c0 = color_scheme.schema[i]
        c1 = color_scheme.schema[i + 1]

        if c0[3] <= pos <= c1[3]:
            ratio = (pos - c0[3]) / (c1[3] - c0[3])
            if mode == INTERPOL_MODE_LINEAR:
                return interpol(c0, c1, ratio)
            elif mode == INTERPOL_MODE_REVERSE:
                return interpol(c0, c1, 1 - ratio)
            elif mode == INTERPOL_MODE_COSINE:
                return interpol(c0, c1, (1 - wx.math.cos(ratio * wx.math.pi)) / 2)
            elif mode == INTERPOL_MODE_FLAT_START:
                return c0
            elif mode == INTERPOL_MODE_FLAT_MIDDLE:
                return interpol(c0, c1, 0.5)
            elif mode == INTERPOL_MODE_FLAT_END:
                return c1
            else:
                raise ValueError("Unknown interpolation mode")

    # Если не нашли, значит pos больше максимума
    r, g, b = color_scheme.schema[-1][:3]
    return wx.Colour(r, g, b)


def draw_gradient(
    dc: wx.DC, rect: wx.Rect, scheme: ColorScheme, mode=INTERPOL_MODE_LINEAR
):
    if rect.GetWidth() <= 0 or rect.GetHeight() <= 0:
        return
    min_pos = scheme.min_pos()
    range_s = scheme.range()
    x = rect.GetLeft()
    y = rect.GetTop()
    w = rect.GetWidth()
    h = rect.GetHeight()
    l_ = len(scheme.schema)
    # Вместо условия в цикле применяю функцию исходя из выбранного метода
    if mode == INTERPOL_MODE_LINEAR:
        fn = lambda c0, c1, ratio: interpol(c0, c1, ratio)
    elif mode == INTERPOL_MODE_REVERSE:
        fn = lambda c0, c1, ratio: interpol(c0, c1, 1 - ratio)
    elif mode == INTERPOL_MODE_COSINE:
        fn = lambda c0, c1, ratio: interpol(
            c0, c1, (1 - wx.math.cos(ratio * wx.math.pi)) / 2
        )
    elif mode == INTERPOL_MODE_FLAT_START:
        fn = lambda c0, c1, ratio: c0
    elif mode == INTERPOL_MODE_FLAT_MIDDLE:
        fn = lambda c0, c1, ratio: interpol(c0, c1, 0.5)
    elif mode == INTERPOL_MODE_FLAT_END:
        fn = lambda c0, c1, ratio: c1
    else:
        raise ValueError("Unknown interpolation mode")

    # Если схема пустая заполняем белым
    if l_ == 0:
        dc.SetPen(wx.Pen(wx.Colour(255, 255, 255)))
        dc.SetBrush(wx.Brush(wx.Colour(255, 255, 255)))
        dc.DrawRectangle(rect)
    # Если один цвет им из заполняем 
    elif l_ == 1:
        dc.SetPen(wx.Pen(wx.Colour(*scheme.schema[0][:3])))
        dc.SetBrush(wx.Brush(wx.Colour(*scheme.schema[0][:3])))
        dc.DrawRectangle(rect)
    else:
        c = 0
        c0 = scheme.schema[0]
        c1 = scheme.schema[1]
        for i in range(x, x + w):
            pos = min_pos + (i - x) * (range_s / w)
            if not (c0[3] <= pos <= c1[3]):
                c += 1
                c0 = scheme.schema[c] 
                c1 = scheme.schema[c + 1]
            color = fn(c0[:3], c1[:3], (pos - c0[3]) / (c1[3] - c0[3]))
            dc.SetPen(wx.Pen(color))
            dc.DrawLine(i, y, i, y + h)


class ColorSchemePicker(wx.Panel):
    def __init__(
        self,
        parent,
        value: ColorScheme,
        mode=INTERPOL_MODE_FLAT_START,
        size=wx.DefaultSize,
    ):
        super().__init__(parent, size=size)
        self.value = value
        self.mode = mode
        sz = wx.BoxSizer(wx.VERTICAL)
        self.ruler = RulerWidget(self, threshold=50)
        sz.Add(self.ruler, 0, wx.EXPAND)
        self.gradient = wx.Panel(
            self, style=wx.WANTS_CHARS | wx.NO_FULL_REPAINT_ON_RESIZE | wx.CLIP_CHILDREN
        )
        self.gradient.SetDoubleBuffered(True)
        self.gradient.SetCursor(wx.Cursor(wx.CURSOR_CROSS))
        sz.Add(self.gradient, 1, wx.EXPAND)
        self.SetSizer(sz)
        self.Layout()
        self.dragged_index = None
        self.dragged_last_pos = None
        self.dragged = False
        self.gradient.Bind(wx.EVT_MOTION, self.on_motion)
        self.gradient.Bind(wx.EVT_SIZE, self.on_size)
        self.gradient.Bind(wx.EVT_PAINT, self.on_paint)
        self.gradient.Bind(wx.EVT_LEFT_DOWN, self.on_left_down)
        self.gradient.Bind(wx.EVT_LEFT_UP, self.on_left_up)
        self.gradient.Bind(wx.EVT_ENTER_WINDOW, self.on_enter_window)
        self.gradient.Bind(wx.EVT_RIGHT_DOWN, self.on_right_down)

    def delete_color(self, index):
        if 0 <= index < len(self.value.schema):
            del self.value.schema[index]
            self.ruler.draw()
            self.gradient.Refresh()

    def on_right_down(self, event):
        index = self.pick_index(event.GetPosition().Get()[0])
        if index != -1:
            m = wx.Menu()
            m.Append(wx.ID_DELETE, "Удалить цвет")
            self.Bind(
                wx.EVT_MENU,
                lambda e: self.delete_color(index),
                m.FindItemById(wx.ID_DELETE),
            )
            m.Append(wx.ID_EDIT, "Изменить цвет")
            self.Bind(
                wx.EVT_MENU,
                lambda e: self.edit_color(index),
                m.FindItemById(wx.ID_EDIT),
            )
            self.PopupMenu(m, event.GetPosition())
        else:
            if self.gradient.HasCapture():
                self.gradient.ReleaseMouse()
            m = wx.Menu()
            m.Append(wx.ID_ADD, "Добавить цвет")
            self.Bind(wx.EVT_MENU, self.on_add_color, m.FindItemById(wx.ID_ADD))
            self.PopupMenu(m, event.GetPosition())

    def edit_color(self, index):
        r, g, b, p = self.value.schema[index]
        data = wx.ColourData()
        data.SetColour(wx.Colour(r, g, b))
        data.SetChooseFull(True)
        dlg = wx.ColourDialog(None, data)
        if dlg.ShowModal() == wx.ID_OK:
            c = dlg.GetColourData().GetColour()
            self.value.schema[index] = (c.GetRed(), c.GetGreen(), c.GetBlue(), p)
            self.gradient.Refresh()

    def on_add_color(self, event):
        data = wx.ColourData()
        data.SetColour(wx.Colour(0, 0, 0))
        data.SetChooseFull(True)
        dlg = wx.ColourDialog(None, data)
        if dlg.ShowModal() == wx.ID_OK:
            c = dlg.GetColourData().GetColour()
            x = self.gradient.GetSize().GetWidth() / 2
            p = (
                x / self.gradient.GetSize().GetWidth()
            ) * self.value.range() + self.value.min_pos()
            self.value.schema.append((c.Red(), c.Green(), c.Blue(), p))
            self.value.schema.sort(key=lambda o: o[3])
            self.ruler.draw()
            self.gradient.Refresh()
        dlg.Destroy()

    def on_enter_window(self, event):
        self.gradient.SetCursor(wx.Cursor(wx.CURSOR_CROSS))
        self.ruler.set_cursor(None)
        self.gradient.Refresh()

    def on_left_down(self, event):
        self.dragged_index = self.pick_index(event.GetPosition().Get()[0])
        self.dragged_last_pos = event.GetPosition().Get()[0]

    def on_left_up(self, event):
        self.dragged_index = None
        self.dragged_last_pos = None

        if not self.dragged:
            x = event.GetPosition().Get()[0]
            index = self.pick_index(x)
            if index == -1:
                data = wx.ColourData()
                data.SetColour(wx.Colour(0, 0, 0))
                data.SetChooseFull(True)
                dlg = wx.ColourDialog(None, data)
                if dlg.ShowModal() == wx.ID_OK:
                    c = dlg.GetColourData().GetColour()
                    p = (
                        x / self.gradient.GetSize().GetWidth()
                    ) * self.value.range() + self.value.min_pos()
                    self.value.schema.append((c.Red(), c.Green(), c.Blue(), p))
                    self.value.schema.sort(key=lambda o: o[3])
                    self.ruler.draw()
                    self.gradient.Refresh()
                dlg.Destroy()
            else:
                r, g, b, p = self.value.schema[index]
                data = wx.ColourData()
                data.SetColour(wx.Colour(r, g, b))
                data.SetChooseFull(True)
                dlg = wx.ColourDialog(None, data)
                if dlg.ShowModal() == wx.ID_OK:
                    c = dlg.GetColourData().GetColour()
                    self.value.schema[index] = (c.Red(), c.Green(), c.Blue(), p)
                    self.ruler.draw()
                    self.gradient.Refresh()
                dlg.Destroy()
        else:
            self.value.schema.sort(key=lambda o: o[3])
            self.Refresh()
            self.Update()

        self.dragged = False

        if self.gradient.HasCapture():
            self.gradient.ReleaseMouse()

    def pick_index(self, x):
        width = self.gradient.GetSize().GetWidth()
        for i, (r, g, b, p) in enumerate(self.value.schema):
            pos = (p - self.value.min_pos()) * (width / self.value.range())
            if abs(x - pos) < 5:
                return i
        return -1

    def on_motion(self, event):
        width = self.gradient.GetSize().GetWidth()
        self.ruler.set_cursor(event.GetPosition().Get()[0])
        if self.dragged_index is not None:
            self.dragged = event.Dragging() and event.LeftIsDown()
        self.dragged = True
        if self.dragged_index != -1 and event.Dragging() and event.LeftIsDown():
            self.gradient.SetCursor(wx.Cursor(wx.CURSOR_CROSS))
            if not self.gradient.HasCapture():
                self.gradient.CaptureMouse()
            self.gradient.SetCursor(wx.Cursor(wx.CURSOR_SIZEWE))
            x = event.GetPosition().Get()[0] - self.dragged_last_pos
            self.dragged_last_pos = event.GetPosition().Get()[0]
            p = x * (self.value.range() / width)
            r, g, b, p_old = self.value.schema[self.dragged_index]
            self.value.schema[self.dragged_index] = (r, g, b, p_old + p)
            self.ruler.draw()
            self.gradient.Refresh()
        else:
            if self.pick_index(event.GetPosition().Get()[0]) != -1:
                self.gradient.SetCursor(wx.Cursor(wx.CURSOR_HAND))
            else:
                self.gradient.SetCursor(wx.Cursor(wx.CURSOR_CROSS))

    def on_size(self, event):
        width = self.GetSize().GetWidth()
        self.ruler.set_scale(width / self.value.range(), draw=False)
        self.ruler.set_offset(-self.value.min_pos())
        self.ruler.draw()
        self.gradient.Refresh()

    def get_color(self, pos):
        return get_interpol_color_by_pos(self.value, pos, self.mode)

    def on_paint(self, event):
        dc = wx.PaintDC(self.gradient)
        width, height = (
            self.gradient.GetSize().GetWidth(),
            self.gradient.GetSize().GetHeight(),
        )
        if width == 0 or height == 0:
            return
        draw_gradient(dc, wx.Rect(0, 0, width, height), self.value)

        for r, g, b, p in self.value.schema:
            x = int((p - self.value.min_pos()) / self.value.range() * width)
            dc.SetPen(
                wx.Pen(wx.Colour(255 - r, 255 - g, 255 - b), 1, wx.PENSTYLE_SOLID)
            )
            dc.DrawRectangle(int(x - 5), int(height / 2 - 5), 10, 10)

        self.ruler.set_scale(width / self.value.range(), draw=False)
        self.ruler.set_offset(-self.value.min_pos())
        self.ruler.draw()

    def set_mode(self, mode):
        self.mode = mode
        self.Refresh()


class ColorSchemeDialog(wx.Dialog):
    def __init__(self, parent, value: ColorScheme, mode=INTERPOL_MODE_LINEAR):
        super().__init__(
            parent,
            title="Настройка цветовой схемы",
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
            size=wx.Size(400, 130),
        )
        self.mode = mode
        sz = wx.BoxSizer(wx.VERTICAL)
        self.picker = ColorSchemePicker(self, value, mode=mode, size=wx.Size(350, 50))
        sz.Add(self.picker, 0, wx.EXPAND | wx.BOTTOM, 10)
        btn_sz = wx.BoxSizer(wx.HORIZONTAL)
        self.btn_load = wx.Button(self, wx.ID_OPEN, "Загрузить")
        self.btn_save = wx.Button(self, wx.ID_SAVE, "Сохранить")
        self.btn_load.Bind(wx.EVT_BUTTON, self.on_load)
        self.btn_save.Bind(wx.EVT_BUTTON, self.on_save)
        btn_sz.Add(self.btn_load)
        btn_sz.Add(self.btn_save, 1, wx.RIGHT, border=20)
        sz.Add(btn_sz, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)
        btn_sz.AddStretchSpacer()
        self.btn_cancel = wx.Button(self, label="Отменить")
        self.btn_cancel.Bind(wx.EVT_BUTTON, self.on_cancel)
        btn_sz.Add(self.btn_cancel, 0, wx.EXPAND)
        self.btn_apply = wx.Button(self, label="Применить")
        self.btn_apply.Bind(wx.EVT_BUTTON, self.on_apply)
        self.btn_apply.SetDefault()
        btn_sz.Add(self.btn_apply, 0, wx.EXPAND)
        self.SetSizer(sz)
        self.Layout()

    def on_apply(self, event):
        self.EndModal(wx.ID_OK)

    def on_cancel(self, event):
        self.EndModal(wx.ID_CANCEL)

    def get_value(self):
        return self.picker.value

    def on_save(self, event):
        wildcard = (
            "Color Scheme Files (*.colorscheme)|*.colorscheme|All files (*.*)|*.*"
        )

        with wx.FileDialog(
            self,
            message="Сохранить цветовую схему",
            wildcard=wildcard,
            style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
        ) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                with open(dlg.GetPath(), "w") as f:
                    self.picker.value.save(f)

    def on_load(self, event):
        wildcard = (
            "Color Scheme Files (*.colorscheme)|*.colorscheme|All files (*.*)|*.*"
        )

        with wx.FileDialog(
            self,
            message="Открыть цветовую схему",
            wildcard=wildcard,
            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST,
        ) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                with open(dlg.GetPath(), "r") as f:
                    self.picker.value = ColorScheme.load(f)
                    self.picker.Refresh()
                    self.picker.Update()


class GradientPanel(wx.Panel):
    def __init__(self, parent, style, pos, size):
        super().__init__(parent, style=style, pos=pos, size=size)
        self.value = None
        self.mode = INTERPOL_MODE_LINEAR
        sz = wx.BoxSizer(wx.HORIZONTAL)
        self.gradient = wx.Panel(self)
        sz.Add(self.gradient, 1, wx.EXPAND)
        self.button = wx.Button(self, label="...", style=wx.BU_EXACTFIT)
        sz.Add(self.button, 0, wx.EXPAND)
        self.SetSizer(sz)
        self.Layout()
        self.gradient.Bind(wx.EVT_PAINT, self.on_paint)

    def on_paint(self, event):
        if self.value is None:
            return

        panel = event.GetEventObject()
        dc = wx.PaintDC(panel)
        rect: wx.Rect = panel.GetClientRect()
        rect.Deflate(0, 2)

        width = rect.width
        height = rect.height

        if width == 0 or height == 0:
            return
        draw_gradient(dc, rect, self.value, self.mode)

    def set_color_scheme(self, color_scheme):
        self.value = color_scheme
        self.Refresh()
        self.Update()

    def set_mode(self, mode):
        self.mode = mode
        self.Refresh()
        self.Update()


class GradientEditor(wx.propgrid.PGEditor):
    def __init__(self, mode=INTERPOL_MODE_LINEAR):
        super().__init__()
        self.mode = mode

    def CreateControls(self, propgrid, property, pos, size):
        panel = GradientPanel(propgrid, style=wx.NO_BORDER, pos=pos, size=size)
        panel.Layout()
        panel.set_color_scheme(property.GetValue())
        panel.set_mode(self.mode)

        return wx.propgrid.PGWindowList(panel)

    def UpdateControl(self, property: wx.propgrid.PGProperty, ctrl: wx.Window) -> None:
        ctrl.set_color_scheme(property.GetValue())

    def SetControlStringValue(
        self, property: wx.propgrid.PGProperty, ctrl: wx.Window, txt: str
    ) -> None:
        ctrl.set_color_scheme(property.GetValue())

    def get_color(self, scheme, value, mode):
        return get_interpol_color_by_pos(scheme, value, mode)

    def DrawValue(self, dc, rect, property, text):
        propvalue = ColorScheme.from_string(text)
        stops = getattr(propvalue, "schema")
        self.value = propvalue

        if not stops or len(stops) < 2:
            dc.SetBrush(wx.Brush(wx.WHITE))
            dc.DrawRectangle(rect)
            return

        width = rect.width
        height = rect.height

        # Рисуем градиент слева направо
        if width == 0 or height == 0:
            return
        draw_gradient(dc, rect, self.value, self.mode)

    def OnPaint(self, event):
        if self.value is None:
            return

        panel = event.GetEventObject()
        dc = wx.PaintDC(panel)
        rect: wx.Rect = panel.GetClientRect()
        rect.Deflate(0, 2)

        self.DrawValue(dc, rect, None, self.value.to_string())

    def OnEvent(
        self,
        propgrid: wx.propgrid.PropertyGrid,
        property: wx.propgrid.PGProperty,
        wnd_primary: wx.Window,
        event: wx.Event,
    ) -> bool:
        """
        OnEvent(propgrid, property, wnd_primary, event) -> bool

        Handles events.
        """
        return True

    def OnClick(self, event): ...


class ColorSchemeProperty(wx.propgrid.PGProperty):
    def __init__(self, label, name, value=None):
        super().__init__(label, name)
        self.SetValue(value)

    def GetValueAsString(self, argFlags=0):
        return self.GetValue().to_string()

    def OnEvent(
        self,
        propgrid: wx.propgrid.PropertyGrid,
        wnd_primary: wx.Window,
        event: wx.Event,
    ) -> bool:
        if event.GetEventType() == wx.wxEVT_BUTTON:
            dlg = ColorSchemeDialog(propgrid, self.GetValue().clone())
            if dlg.ShowModal() == wx.ID_OK:
                self.SetValueInEvent(dlg.get_value())
        return True
