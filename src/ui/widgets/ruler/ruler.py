import wx
import math
from dataclasses import dataclass


@dataclass
class RulerConfig:
    factor: float
    offset: float
    cursor: float
    pixels_per_unit: float
    font: wx.Font
    sup_font: wx.Font
    threshold: float = 50
    orientation: int = wx.HORIZONTAL
    inverted: bool = False
    exponent_threshold: float = 10000
    parts: int = 5


def next_factor(current):
    base = [1, 2, 5]
    exp = int(math.floor(math.log10(current)))
    mant = current / (10**exp)
    for b in base:
        if mant < b:
            return b * (10**exp)
    return 10 ** (exp + 1)


def calc_factor(pixels_per_unit: float, threshold: float) -> float:
    factor = 1
    if pixels_per_unit > threshold * 2:
        while factor * pixels_per_unit > threshold * 2:
            factor /= 2
    else:
        while factor * pixels_per_unit < threshold:
            factor = next_factor(factor)
    return factor


def rm(v, s):
    return round(v / s) * s


def draw_label(
    gc: wx.GraphicsContext, config: RulerConfig, x: float, y: float, n: float
):
    if abs(n) >= config.exponent_threshold:
        e = 0
        while abs(n) >= 10:
            n /= 10
            e += 1
        n_text = "%.5f" % n
        n_text = n_text.rstrip('0.')
        n_text = "%s\u22c510" % n_text
        gc.DrawText(n_text, x, y)
        w, h, _, _ = gc.GetFullTextExtent(n_text)
        gc.SetFont(config.sup_font, wx.Colour(0, 0, 0))
        gc.DrawText("%d" % e, x + w, y)
        gc.SetFont(config.font, wx.Colour(0, 0, 0))
    else:
        gc.DrawText(str(n), x, y)


def draw_horizontal(gc: wx.GraphicsContext, rect: wx.Rect, config: RulerConfig):
    w, h = rect.GetWidth(), rect.GetHeight()
    brush = gc.CreateLinearGradientBrush(
        0, 0, 0, h, wx.Colour(255, 255, 255), wx.Colour(220, 220, 220)
    )
    gc.SetBrush(brush)
    gc.DrawRectangle(0, 0, w, h)
    gc.SetPen(wx.Pen(wx.Colour(0, 0, 0), width=1))

    pixoffset = config.offset * config.pixels_per_unit
    mod = config.factor * config.pixels_per_unit
    i = pixoffset % mod
    if config.offset < 0:
        i -= mod

    r = round
    index = rm((i - pixoffset) / config.pixels_per_unit, config.factor)

    while i < w:
        draw_label(gc, config, i + 2, 0, index)
        gc.StrokeLine(r(i), r(h), r(i), 0)
        i += mod
        index += config.factor

    mod /= config.parts
    i = pixoffset % mod
    if config.offset < 0:
        i -= mod

    while i < w:
        gc.StrokeLine(r(i), r(h / 2), r(i), r(h))
        i += mod

    gc.StrokeLine(config.cursor, 0, config.cursor, h)


def draw_horizontal_inverted(
    gc: wx.GraphicsContext, rect: wx.Rect, config: RulerConfig
):
    w, h = rect.GetWidth(), rect.GetHeight()
    brush = gc.CreateLinearGradientBrush(
        0, 0, 0, h, wx.Colour(255, 255, 255), wx.Colour(220, 220, 220)
    )
    gc.SetBrush(brush)
    gc.DrawRectangle(0, 0, w, h)
    gc.SetPen(wx.Pen(wx.Colour(0, 0, 0), width=1))

    pixoffset = config.offset * config.pixels_per_unit
    mod = config.factor * config.pixels_per_unit
    i = pixoffset % mod
    if config.offset < 0:
        i -= mod

    r = round

    index = rm((i - pixoffset) / config.pixels_per_unit, config.factor)

    while i < w:
        draw_label(gc, config, (w - i) + 2, 0, index)
        gc.StrokeLine(r(w - i), r(h), r(w - i), 0)
        i += mod
        index += config.factor

    mod /= config.parts
    i = pixoffset % mod
    if config.offset < 0:
        i -= mod

    while i < w:
        gc.StrokeLine(r(w - i), r(h / 2), r(w - i), h)
        i += mod

    gc.StrokeLine(config.cursor, 0, config.cursor, h)


def draw_vertical(gc: wx.GraphicsContext, rect: wx.Rect, config: RulerConfig):
    w, h = rect.GetWidth(), rect.GetHeight()
    brush = gc.CreateLinearGradientBrush(
        0, 0, w, 0, wx.Colour(255, 255, 255), wx.Colour(220, 220, 220)
    )
    gc.SetBrush(brush)
    gc.DrawRectangle(0, 0, w, h)
    gc.SetPen(wx.Pen(wx.Colour(0, 0, 0), width=1))

    pixoffset = config.offset * config.pixels_per_unit
    mod = config.factor * config.pixels_per_unit
    i = pixoffset % mod
    if config.offset < 0:
        i -= mod

    def r(value):
        return round(value)

    index = rm((i - pixoffset) / config.pixels_per_unit, config.factor)
    while i < h:
        gc.PushState()
        gc.Translate(0, r(i))
        gc.Rotate(-math.pi / 2)
        draw_label(gc, config, 0, 2, index)
        gc.PopState()
        gc.StrokeLine(0, r(i), r(w), r(i))
        index += config.factor
        i += mod

    mod /= config.parts
    i = pixoffset % mod
    if config.offset < 0:
        i -= mod

    while i < h:
        gc.StrokeLine(w / 2, i, w, i)
        i += mod

    gc.StrokeLine(0, config.cursor, w, config.cursor)


def draw_vertical_inverted(gc: wx.GraphicsContext, rect: wx.Rect, config: RulerConfig):
    w, h = rect.GetWidth(), rect.GetHeight()
    brush = gc.CreateLinearGradientBrush(
        0, 0, w, 0, wx.Colour(255, 255, 255), wx.Colour(220, 220, 220)
    )
    gc.SetBrush(brush)
    gc.DrawRectangle(0, 0, w, h)
    gc.SetPen(wx.Pen(wx.Colour(0, 0, 0), width=1))

    pixoffset = config.offset * config.pixels_per_unit
    mod = config.factor * config.pixels_per_unit
    i = pixoffset % mod
    if config.offset < 0:
        i -= mod

    def r(value):
        return round(value)

    index = rm((i - pixoffset) / config.pixels_per_unit, config.factor)
    while i < h:
        gc.PushState()
        gc.Translate(0, r(h - i))
        gc.Rotate(-math.pi / 2)
        draw_label(gc, config, 0, 2, index)
        gc.PopState()
        gc.StrokeLine(0, r(h - i), r(w), r(h - i))
        index += config.factor
        i += mod

    mod /= config.parts
    i = pixoffset % mod
    if config.offset < 0:
        i -= mod

    while i < h:
        gc.StrokeLine(r(w / 2), r(h - i), r(w), r(h - i))
        i += mod

    gc.StrokeLine(0, config.cursor, w, config.cursor)


def draw(dc: wx.DC, rect: wx.Rect, config: RulerConfig):
    gc = wx.GraphicsContext.Create(dc)
    gc.SetFont(config.font, wx.Colour(0, 0, 0))
    w, h = rect.GetSize()
    if w <= 0 or h <= 0:
        return
    if config.orientation == wx.HORIZONTAL and not config.inverted:
        draw_horizontal(gc, rect, config)
    elif config.orientation == wx.HORIZONTAL and config.inverted:
        draw_horizontal_inverted(gc, rect, config)
    elif config.orientation == wx.VERTICAL and not config.inverted:
        draw_vertical(gc, rect, config)
    elif config.orientation == wx.VERTICAL and config.inverted:
        draw_vertical_inverted(gc, rect, config)
    else:
        raise Exception("Undefined draw ruler mode")
    gc.SetPen(wx.Pen(wx.Colour(120, 120, 120), width=1))
    gc.StrokeLine(0, 0, w, 0)
    gc.StrokeLine(0, 0, 0, h)
    gc.StrokeLine(w - 1, 0, w - 1, h)
    gc.StrokeLine(0, h - 1, w, h - 1)


class RulerWidget(wx.Panel):
    def __init__(
        self,
        parent,
        threshold=50,
        orientation=wx.HORIZONTAL,
        invert=False,
        exponent_threshold=10000,
        parts=5,
    ):
        super().__init__(parent)
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)
        font = wx.Font(
            8, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL
        )
        sup_font = wx.Font(
            int(font.GetPointSize() * 0.7),
            font.GetFamily(),
            font.GetStyle(),
            font.GetWeight(),
        )
        self.config = RulerConfig(
            factor=1,
            offset=0,
            cursor=0,
            pixels_per_unit=1,
            font=font,
            sup_font=sup_font,
            threshold=threshold,
            orientation=orientation,
            inverted=invert,
            exponent_threshold=exponent_threshold,
            parts=5,
        )
        self.SetMinSize(
            wx.Size(20, 20) if orientation == wx.HORIZONTAL else wx.Size(20, 20)
        )
        self.SetSize(
            wx.Size(-1, 20) if orientation == wx.HORIZONTAL else wx.Size(20, -1)
        )

        self.Layout()
        self.Bind(wx.EVT_PAINT, self.on_paint)
        self.Bind(wx.EVT_SIZE, self.on_size)

    def on_size(self, event):
        self.Refresh()

    def on_paint(self, event):
        # Хотя согласно документации в windows wx.AutoBufferedPaintDC
        # должен быть просто алиасом wx.PaintDC, но на деле он работает заметно быстрее.
        dc = wx.AutoBufferedPaintDC(self)

        w, h = self.GetSize()
        if w <= 0 or h <= 0:
            return

        draw(dc, wx.Rect(0, 0, w, h), self.config)

    def set_scale(self, pixels_per_unit: float, draw=True):
        if abs(self.config.pixels_per_unit - pixels_per_unit) > 0.00001:
            self.config.pixels_per_unit = pixels_per_unit
            self.config.factor = calc_factor(pixels_per_unit, self.config.threshold)
        if draw:
            self.draw()

    def set_offset(self, axis_value: float, draw=True):
        """Sets the offset of the ruler in coords."""
        self.config.offset = axis_value
        if draw:
            self.draw()

    def set_cursor(self, axis_value: float | None, draw=True):
        """Sets the cursor position on the ruler. in pixels."""
        self.config.cursor = axis_value
        if draw:
            self.draw()

    def draw(self):
        # Не используем self.Update() оставляя нахождение лучшего момента отрисовки планировщику
        # Позволяет отрисовке не захлебываться при большом количестве событий (например MOUSE MOVE события)
        self.Refresh()
