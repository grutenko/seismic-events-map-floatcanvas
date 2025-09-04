import wx
import wx.grid


class SeismicImport(wx.Dialog):
    def __init__(self, parent):
        super().__init__(
            parent,
            size=wx.Size(350, 550),
            title="Импорт сейсмических данных",
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
        )
        sz = wx.BoxSizer(wx.VERTICAL)
        sz_in = wx.BoxSizer(wx.VERTICAL)
        self.file = wx.FilePickerCtrl(
            self, wildcard="CSV файлы (*.csv)|*.csv|All files (*.*)|*.*"
        )
        self.file.GetPickerCtrl().SetLabel("Выбрать CSV файл")
        sz_in.Add(self.file, 0, wx.EXPAND | wx.BOTTOM, border=5)

        label = wx.StaticText(self, label="Разделитель")
        sz_in.Add(label)
        self.delimiter = wx.Choice(self, choices=[";", ",", "Табуляция"])
        self.delimiter.SetSelection(2)
        sz_in.Add(self.delimiter, 0, wx.BOTTOM, border=5)

        line = wx.StaticLine(self)
        sz_in.Add(line, 0, wx.EXPAND | wx.BOTTOM, border=5)

        self.coord_types_radio = wx.RadioBox(self, choices=["АСКСМ", "Геодезические"])
        sz_in.Add(self.coord_types_radio, 0, wx.EXPAND | wx.BOTTOM, border=5)

        label = wx.StaticText(self, label="X")
        sz_in.Add(label)
        self.x_choice = wx.Choice(self)
        self.x_choice.Disable()
        sz_in.Add(self.x_choice, 0, wx.EXPAND | wx.BOTTOM, border=5)

        label = wx.StaticText(self, label="Y")
        sz_in.Add(label)
        self.y_choice = wx.Choice(self)
        self.y_choice.Disable()
        sz_in.Add(self.y_choice, 0, wx.EXPAND | wx.BOTTOM, border=5)

        label = wx.StaticText(self, label="Z")
        sz_in.Add(label)
        self.z_choice = wx.Choice(self)
        self.z_choice.Disable()
        sz_in.Add(self.z_choice, 0, wx.EXPAND | wx.BOTTOM, border=5)

        label = wx.StaticText(self, label="Значение")
        sz_in.Add(label)
        self.value_choice = wx.Choice(self)
        self.value_choice.Disable()
        sz_in.Add(self.value_choice, 0, wx.EXPAND)

        sz.Add(sz_in, 0, wx.EXPAND | wx.ALL, border=10)

        self.grid = wx.grid.Grid(self)
        self.grid.CreateGrid(0, 4)
        self.grid.SetColMinimalAcceptableWidth(2)
        self.grid.SetRowMinimalAcceptableHeight(20)
        self.grid.GridLineColour = wx.SystemSettings.GetColour(
            wx.SYS_COLOUR_ACTIVEBORDER
        )
        font: wx.Font = self.grid.GetLabelFont()
        info: wx.NativeFontInfo = font.GetNativeFontInfo()
        info.SetNumericWeight(600)
        info.SetPointSize(9)
        font.SetNativeFontInfo(info)
        self.grid.SetColLabelSize(20)
        self.grid.SetLabelFont(font)
        self.grid.SetColLabelValue(0, "X")
        self.grid.SetColLabelValue(1, "Y")
        self.grid.SetColLabelValue(2, "Z")
        self.grid.SetColLabelValue(3, "Значение")
        self.grid.SetRowLabelSize(30)
        attr = wx.grid.GridCellAttr()
        attr.SetEditor(wx.grid.GridCellTextEditor())  # редактор текста
        attr.SetRenderer(wx.grid.GridCellStringRenderer())  # отображение текста
        self.grid.SetColAttr(0, attr)
        self.grid.SetColAttr(1, attr)
        self.grid.SetColAttr(2, attr)
        self.grid.SetColAttr(3, attr)
        sz.Add(self.grid, 1, wx.EXPAND | wx.ALL, border=10)

        sz_btn = wx.StdDialogButtonSizer()
        self.btn_load = wx.Button(self, label="Загрузить")
        sz_btn.Add(self.btn_load)
        self.btn_load.Disable()
        sz.Add(sz_btn, 0, wx.ALIGN_RIGHT | wx.ALL, border=10)
        self.SetSizer(sz)
        self.btn_load.Bind(wx.EVT_BUTTON, self.on_load)
        self.Layout()

        self.table = None
        self.x_field = -1
        self.y_field = -1
        self.z_field = -1
        self.value_field = -1
        self.file.Bind(wx.EVT_FILEPICKER_CHANGED, self.on_open_file)
        self.x_choice.Bind(wx.EVT_CHOICE, self.on_choice_changed)
        self.y_choice.Bind(wx.EVT_CHOICE, self.on_choice_changed)
        self.z_choice.Bind(wx.EVT_CHOICE, self.on_choice_changed)
        self.value_choice.Bind(wx.EVT_CHOICE, self.on_choice_changed)

    def update_controls_state(self):
        import os.path

        exists = os.path.exists(self.file.GetPath())
        self.x_choice.Enable(exists)
        self.y_choice.Enable(exists)
        self.z_choice.Enable(exists)
        self.value_choice.Enable(exists)
        self.coord_types_radio.Enable(exists)
        self.btn_load.Enable(exists)

    def on_choice_changed(self, event=None):
        self.x_field = self.x_choice.GetSelection()
        self.y_field = self.y_choice.GetSelection()
        self.z_field = self.z_choice.GetSelection()
        self.value_field = self.value_choice.GetSelection()
        self.update_grid()
        self.update_controls_state()

    def update_grid(self):
        if self.grid.GetNumberRows() > 0:
            self.grid.DeleteRows(0, self.grid.GetNumberRows())
        data = self.table[1:]
        for index, row in enumerate(data):
            self.grid.AppendRows(1)
            self.grid.SetCellValue(index, 0, data[index][self.x_field])
            self.grid.SetCellValue(index, 1, data[index][self.y_field])
            self.grid.SetCellValue(index, 2, data[index][self.z_field])
            self.grid.SetCellValue(index, 3, data[index][self.value_field])

    def on_open_file(self, event):
        import csv
        import re

        data = []
        with open(self.file.GetPath(), newline="", encoding="utf-8") as f:
            rows = []
            for row in f:
                rows.append(re.sub(r"(\t)\1+", r"\1", row))
            rowslen = []
            delimiter = [";", ",", "\t"].__getitem__(self.delimiter.GetSelection())
            for row in csv.reader(rows, delimiter=delimiter):
                if len(row) == 0:
                    continue
                rowslen.append(len(list(row)))
                data.append(list(row))
            max_rows_len = max(rowslen)
            for index in range(1, len(data)):
                data[index].extend(["0,0"] * (max_rows_len - len(data[index])))
            data[0].extend(["Без названия"] * (max_rows_len - len(data[0])))
        self.table = data
        header = data[0]
        self.x_choice.Clear()
        self.y_choice.Clear()
        self.z_choice.Clear()
        self.value_choice.Clear()
        self.x_choice.AppendItems(header)
        self.y_choice.AppendItems(header)
        self.z_choice.AppendItems(header)
        self.value_choice.AppendItems(header)
        self.x_choice.SetSelection(0)
        self.y_choice.SetSelection(1 if len(header) > 1 else 0)
        self.z_choice.SetSelection(2 if len(header) > 1 else 0)
        self.value_choice.SetSelection(3 if len(header) > 1 else 0)
        self.on_choice_changed()
        self.update_grid()
        self.update_controls_state()

    def on_load(self, event):
        self.EndModal(wx.ID_OK)

    def get_table(self):
        data = []
        for row in self.table[1:]:
            data.append(
                [
                    row[self.x_field].replace(",", "."),
                    row[self.y_field].replace(",", "."),
                    row[self.z_field].replace(",", "."),
                    row[self.value_field].replace(",", "."),
                ]
            )
        return data

    def get_coord_system(self):
        if self.coord_types_radio.GetSelection() == 0:
            return "ASKSM"
        else:
            return "GEO"