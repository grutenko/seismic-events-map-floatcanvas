import wx
from wx.lib.floatcanvas import FloatCanvas

from ruler import RulerWidget

class SeismicEventsMapPlot(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent)
        sz = wx.FlexGridSizer(2)
        sz.AddGrowableCol(1)
        sz.AddGrowableRow(1)
        deputy = wx.Panel(self)
        sz.Add(deputy, 1, wx.EXPAND)
        self.h_ruler = RulerWidget(self)
        self.v_ruler = RulerWidget(self, orientation=wx.VERTICAL, invert=True)
        sz.Add(self.h_ruler, 1, wx.EXPAND)
        sz.Add(self.v_ruler, 1, wx.EXPAND)
        self.canvas = FloatCanvas.FloatCanvas(self)
        sz.Add(self.canvas, 1, wx.EXPAND)
        self.SetSizer(sz)
        self.Layout()
        self.bind_all()
        wx.CallAfter(self.update_rulers)
        self.left_down = False
        self.last_position = None

    def bind_all(self):
        self.canvas.Bind(wx.EVT_MOUSEWHEEL, self.on_mouse_wheel)
        self.canvas.Bind(wx.EVT_LEFT_DOWN, self.on_mouse_down)
        self.canvas.Bind(wx.EVT_LEFT_UP, self.on_mouse_up)
        self.canvas.Bind(wx.EVT_MOTION, self.on_motion)
        self.canvas.Bind(wx.EVT_SIZE, self.on_size)

    def on_size(self, event):
        self.update_rulers()
        event.Skip()

    def on_mouse_wheel(self, event: wx.MouseEvent):
        self.canvas.Zoom(1 + (event.GetWheelRotation() / event.GetWheelDelta() * 0.05))
        self.update_rulers()

    def on_mouse_down(self, event):
        self.left_down = True
        self.last_position = event.GetPosition().Get()

    def on_mouse_up(self, event):
        self.left_down = False

    def on_motion(self, event):
        x, y = event.GetPosition().Get()
        if self.left_down:
            dx, dy = self.last_position[0] - x, self.last_position[1] - y
            self.last_position = (x, y,)
            self.canvas.MoveImage((dx, dy), "Pixel")
            self.update_rulers()
        self.h_ruler.set_cursor(x)
        self.v_ruler.set_cursor(y)

    def update_rulers(self):
        size = self.canvas.GetSize()
        coords_min = self.canvas.PixelToWorld((0, 0))
        coords_max = self.canvas.PixelToWorld((size.GetWidth(), size.GetHeight()))
        self.h_ruler.set_offset(-coords_min[0], draw=False)
        self.h_ruler.set_scale(size.GetWidth() / abs(coords_max[0] - coords_min[0]), draw=False)
        self.v_ruler.set_offset(-coords_max[1], draw=False)
        self.v_ruler.set_scale(size.GetHeight() / abs(coords_min[1] - coords_max[1]), draw=False)
        self.h_ruler.draw()
        self.v_ruler.draw()

    def dxf_get_entity_color(self, doc, entity):
        from ezdxf.colors import int2rgb
        color = entity.dxf.get('true_color', None)
        if color:
            return ((color >> 16) & 0xff, (color >> 8) & 0xff, color & 0xff)
        elif entity.dxf.color == 0:
            return (0, 0, 0)
        elif entity.dxf.color == 256:
            layer = doc.layers.get(entity.dxf.layer)
            return int2rgb(layer.color)
        else:
            return int2rgb(entity.dxf.color)

    def dxf_add_lwpolyline(self, doc, entity):
        if entity.is_closed:
            self.canvas.AddPolygon(list(entity.get_points("xy")), LineColor=self.dxf_get_entity_color(doc, entity), FillColor=None, LineWidth=1)
        else:
            self.canvas.AddLine(list(entity.get_points("xy")), LineColor=self.dxf_get_entity_color(doc, entity), LineWidth=1)

    def dxf_add_polyline(self, doc, entity):
        xy = [(v.dxf.location[0], v.dxf.location[0], ) for v in entity.vertices]
        if entity.is_closed:
            self.canvas.AddPolygon(xy, LineColor=self.dxf_get_entity_color(doc, entity), FillColor=None, LineWidth=1)
        else:
            self.canvas.AddLine(xy, LineColor=self.dxf_get_entity_color(doc, entity), LineWidth=1)


    def dxf_add_line(self, doc, entity):
        self.canvas.AddLine([(entity.dxf.start[0], entity.dxf.start[1]), (entity.dxf.end[0], entity.dxf.end[1])], LineColor=self.dxf_get_entity_color(doc, entity), LineWidth=1)

    def dxf_add_text(self, doc, entity):
        xy = (entity.dxf.insert[0], entity.dxf.insert[1])
        if hasattr(entity.dxf, "height"):
            height = entity.dxf.height
        else:
            height = entity.dxf.char_height
        if entity.dxftype() == "MTEXT":
            text = entity.plain_text()
        else:
            text = entity.dxf.text
        text = FloatCanvas.ScaledText(text, XY=xy, Size=height, Color=self.dxf_get_entity_color(doc, entity), BackgroundColor="WHITE")
        matrix = wx.AffineMatrix2D()
        matrix.Rotate(entity.dxf.rotation)
        text.Transform = matrix
        self.canvas.AddObject(text)

    def dxf_add_spline(self, doc, entity):
        points = [(o[0], o[1]) for o in entity.control_points]
        self.canvas.AddSpline(Points=points, LineColor=self.dxf_get_entity_color(doc, entity), LineWidth=1)

    def dxf_add_circle(self, doc, entity):
        self.canvas.AddCircle(XY=(entity.dxf.center[0], entity.dxf.center[1], ), Diameter=entity.dxf.radius * 2, LineColor=self.dxf_get_entity_color(doc, entity))

    def dxf_add_point(self, doc, entity):
        self.canvas.AddPoint((entity.dxf.location[0], entity.dxf.location[1], ), Diameter=1, Color=self.dxf_get_entity_color(doc, entity))

    def dxf_load(self, path):
        import ezdxf
        
        entcount = 0
        unsupported_types = []

        doc = ezdxf.readfile(path)
        msp = doc.modelspace()

        for entity in msp:
            if entcount > 100:
                wx.Yield()
                self.canvas.Draw()
                entcount = 0

            if "POLYLINE" == entity.dxftype():
                self.dxf_add_polyline(doc, entity)
            elif "LWPOLYLINE" == entity.dxftype():
                self.dxf_add_lwpolyline(doc, entity)
            elif entity.dxftype() == "LINE":
                self.dxf_add_line(doc, entity)
            elif "TEXT" in entity.dxftype():
                self.dxf_add_text(doc, entity)
            elif "SPLINE" in entity.dxftype():
                self.dxf_add_spline(doc, entity)
            elif "CIRCLE" in entity.dxftype():
                self.dxf_add_circle(doc, entity)
            elif "POINT" in entity.dxftype():
                self.dxf_add_point(doc, entity)
            else:
                if entity.dxftype() not in unsupported_types:
                    unsupported_types.append(entity.dxftype())

            entcount += 1

        print(unsupported_types)
