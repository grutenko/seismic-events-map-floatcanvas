import wx
import math
from dataclasses import dataclass


@dataclass
class RulerConfig:
    factor: float
    offset: float
    cursor: float
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


def draw_label(gc: wx.GraphicsContext, x: float, y: float, n: float): ...


def draw_horizontal(gc: wx.GraphicsContext, rect: wx.Rect, config: RulerConfig): ...


def draw_horizontal_inverted(
    gc: wx.GraphicsContext, rect: wx.Rect, config: RulerConfig
): ...


def draw_vertical(gc: wx.GraphicsContext, rect: wx.Rect, config: RulerConfig): ...


def draw_vertical_inverted(
    gc: wx.GraphicsContext, rect: wx.Rect, config: RulerConfig
): ...


def draw(dc: wx.DC, rect: wx.Rect, config: RulerConfig):
    gc = wx.GraphicsContext.Create(dc)
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
        self.base_font = wx.Font(
            8, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL
        )
        self.SetDoubleBuffered(True)
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)
        self.orientation = orientation
        self.threshold = threshold
        self.pixels_per_unit = 20
        self.factor = 1
        self.parts = parts
        self.exponent_threshold = exponent_threshold
        self.update_factor()
        self.invert = invert
        self.offset = 0.0
        self.cursor = 0.0
        self.SetMinSize(
            wx.Size(20, 20) if orientation == wx.HORIZONTAL else wx.Size(20, 20)
        )
        self.SetSize(
            wx.Size(-1, 20) if orientation == wx.HORIZONTAL else wx.Size(20, -1)
        )
        if orientation == wx.HORIZONTAL and not invert:
            self.draw_fn = self.paint_horizontal
        elif orientation == wx.HORIZONTAL and invert:
            self.draw_fn = self.paint_horizontal_inverted
        elif orientation == wx.VERTICAL and not invert:
            self.draw_fn = self.paint_vertical
        else:
            self.draw_fn = self.paint_vertical_inverted
        self.Layout()
        self.Bind(wx.EVT_PAINT, self.on_paint)
        self.Bind(wx.EVT_SIZE, self.on_size)

    def on_size(self, event):
        self.Refresh()

    def on_paint(self, event):
        # Хотя согласно документации в windows wx.AutoBufferedPaintDC
        # должен быть просто алиасом wx.PaintDC, но на деле он работает заметно быстрее.
        dc = wx.AutoBufferedPaintDC(self)
        gc = wx.GraphicsContext.Create(dc)

        w, h = self.GetSize()
        if w <= 0 or h <= 0:
            return

        gc.SetFont(self.base_font, wx.Colour(0, 0, 0))
        self.draw_fn(gc, w, h)
        gc.SetPen(wx.Pen(wx.Colour(120, 120, 120), width=1))
        gc.StrokeLine(0, 0, w, 0)
        gc.StrokeLine(0, 0, 0, h)
        gc.StrokeLine(w - 1, 0, w - 1, h)
        gc.StrokeLine(0, h - 1, w, h - 1)

    def paint_number(self, gc: wx.GraphicsContext, x: float, y: float, n: float):
        n_text = ""
        if abs(n) < self.exponent_threshold:
            gc.DrawText(str(n), x, y)
        else:
            e = 0
            while abs(n) >= 10:
                n /= 10
                e += 1
            n_text = f"{n:.2f}".rstrip("0").rstrip(".") + "\u22c510"
            gc.DrawText(n_text, x, y)
            w, h, _, _ = gc.GetFullTextExtent(n_text)
            sup_font = wx.Font(
                int(self.base_font.GetPointSize() * 0.7),
                self.base_font.GetFamily(),
                self.base_font.GetStyle(),
                self.base_font.GetWeight(),
            )
            gc.SetFont(sup_font, wx.Colour(0, 0, 0))
            gc.DrawText("%d" % e, x + w, y)
            gc.SetFont(self.base_font, wx.Colour(0, 0, 0))

    def round_to_multiple(self, value, step):
        return round(value / step) * step

    def paint_horizontal(self, gc, w, h):
        brush = gc.CreateLinearGradientBrush(
            0, 0, 0, h, wx.Colour(255, 255, 255), wx.Colour(220, 220, 220)
        )
        gc.SetBrush(brush)
        gc.DrawRectangle(0, 0, w, h)
        gc.SetPen(wx.Pen(wx.Colour(0, 0, 0), width=1))

        pixoffset = self.offset * self.pixels_per_unit
        mod = self.factor * self.pixels_per_unit
        i = pixoffset % mod
        if self.offset < 0:
            i -= mod

        r = round

        index = self.round_to_multiple(
            (i - pixoffset) / self.pixels_per_unit, self.factor
        )

        while i < w:
            self.paint_number(gc, i + 2, 0, index)
            gc.StrokeLine(r(i), r(h), r(i), 0)
            i += mod
            index += self.factor

        mod /= self.parts
        i = pixoffset % mod
        if self.offset < 0:
            i -= mod

        while i < w:
            gc.StrokeLine(r(i), r(h / 2), r(i), r(h))
            i += mod

        gc.StrokeLine(self.cursor, 0, self.cursor, h)

    def paint_horizontal_inverted(self, gc, w, h):
        brush = gc.CreateLinearGradientBrush(
            0, 0, 0, h, wx.Colour(255, 255, 255), wx.Colour(220, 220, 220)
        )
        gc.SetBrush(brush)
        gc.DrawRectangle(0, 0, w, h)
        gc.SetPen(wx.Pen(wx.Colour(0, 0, 0), width=1))

        pixoffset = self.offset * self.pixels_per_unit
        mod = self.factor * self.pixels_per_unit
        i = pixoffset % mod
        if self.offset < 0:
            i -= mod

        r = round

        index = self.round_to_multiple(
            (i - pixoffset) / self.pixels_per_unit, self.factor
        )

        while i < w:
            self.paint_number(gc, (w - i) + 2, 0, index)
            gc.StrokeLine(r(w - i), r(h), r(w - i), 0)
            i += mod
            index += self.factor

        mod /= self.parts
        i = pixoffset % mod
        if self.offset < 0:
            i -= mod

        while i < w:
            gc.StrokeLine(r(w - i), r(h / 2), r(w - i), h)
            i += mod

        gc.StrokeLine(self.cursor, 0, self.cursor, h)

    def paint_vertical(self, gc, w, h):
        brush = gc.CreateLinearGradientBrush(
            0, 0, w, 0, wx.Colour(255, 255, 255), wx.Colour(220, 220, 220)
        )
        gc.SetBrush(brush)
        gc.DrawRectangle(0, 0, w, h)
        gc.SetPen(wx.Pen(wx.Colour(0, 0, 0), width=1))

        pixoffset = self.offset * self.pixels_per_unit
        mod = self.factor * self.pixels_per_unit
        i = pixoffset % mod
        if self.offset < 0:
            i -= mod

        r = round

        index = self.round_to_multiple(
            (i - pixoffset) / self.pixels_per_unit, self.factor
        )

        i0 = i
        index0 = index
        gc.PushState()
        gc.Rotate(-math.pi / 2)
        while i0 < h:
            self.paint_number(gc, i0, 2, index0)
            index0 += self.factor
            i0 += mod
        gc.PopState()

        i0 = i
        index0 = index
        while i0 < h:
            gc.StrokeLine(0, r(h - i0), r(w), r(h - i0))
            index0 += self.factor
            i0 += mod

        mod /= self.parts
        i0 = i
        index0 = index
        while i0 < h:
            gc.StrokeLine(w / 2, i0, w, i0)
            i0 += mod

        gc.StrokeLine(0, self.cursor, w, self.cursor)

    def paint_vertical_inverted(self, gc, w, h):
        brush = gc.CreateLinearGradientBrush(
            0, 0, w, 0, wx.Colour(255, 255, 255), wx.Colour(220, 220, 220)
        )
        gc.SetBrush(brush)
        gc.DrawRectangle(0, 0, w, h)
        gc.SetPen(wx.Pen(wx.Colour(0, 0, 0), width=1))

        pixoffset = self.offset * self.pixels_per_unit
        mod = self.factor * self.pixels_per_unit
        i = pixoffset % mod
        if self.offset < 0:
            i -= mod

        r = round

        index = self.round_to_multiple(
            (i - pixoffset) / self.pixels_per_unit, self.factor
        )
        i0 = i
        index0 = index
        gc.PushState()
        gc.Rotate(-math.pi / 2)
        while i0 < h:
            self.paint_number(gc, i0, 2, index0)
            index0 += self.factor
            i0 += mod

        gc.PopState()
        i0 = i
        index0 = index
        while i0 < h:
            gc.StrokeLine(0, r(h - i0), r(w), r(h - i0))
            index += self.factor
            i0 += mod

        mod /= self.parts
        i0 = i
        while i0 < h:
            gc.StrokeLine(r(w / 2), r(h - i0), r(w), r(h - i0))
            i0 += mod

        gc.StrokeLine(0, self.cursor, w, self.cursor)

    def update_factor(self):
        def next_factor(current):
            """Вернуть следующий фактор после current из шкалы 1,2,5*10^n."""
            base = [1, 2, 5]
            # раскладываем текущее число на mantissa * 10^exp
            import math

            exp = int(math.floor(math.log10(current)))
            mant = current / (10**exp)

            # ищем ближайший больший base
            for b in base:
                if mant < b:
                    return b * (10**exp)
            # если больше всех, то идем в следующий порядок
            return 10 ** (exp + 1)

        factor = 1
        if self.pixels_per_unit > self.threshold * 2:
            while factor * self.pixels_per_unit > self.threshold * 2:
                factor /= 2
        else:
            while factor * self.pixels_per_unit < self.threshold:
                factor = next_factor(factor)
        self.factor = factor

    def set_scale(self, pixels_per_unit: float, draw=True):
        if self.pixels_per_unit != pixels_per_unit:
            self.pixels_per_unit = pixels_per_unit
            self.update_factor()
        if draw:
            self.draw()

    def set_offset(self, axis_value: float, draw=True):
        """Sets the offset of the ruler in coords."""
        self.offset = axis_value
        if draw:
            self.draw()

    def set_cursor(self, axis_value: float | None, draw=True):
        """Sets the cursor position on the ruler. in pixels."""
        self.cursor = axis_value
        if draw:
            self.draw()

    def draw(self):
        # Не используем self.Update() оставляя нахождение лучшего момента отрисовки планировщику
        # Позволяет отрисовке не захлебываться при большом количестве событий (например MOUSE MOVE события)
        self.Refresh()
