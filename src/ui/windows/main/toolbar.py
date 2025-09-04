import wx

from src.ui.icon import get_icon

class MainToolbar(wx.ToolBar):
    def __init__(self, parent):
        super().__init__(parent, style=wx.TB_DEFAULT_STYLE | wx.TB_FLAT)
        self.parent = parent
        self.SetToolBitmapSize(wx.Size(16, 16))
        
        # Add file operations
        self.AddTool(wx.ID_OPEN, "Открыть", get_icon("folder-open"), shortHelp="Открыть файл\tCTRL+O") # type: ignore
        self.AddTool(wx.ID_SAVE, "Сохранить", get_icon("save"), shortHelp="Сохранить файл\tCTRL+S") # type: ignore
        self.AddTool(wx.ID_SAVEAS, "Сохранить как...", get_icon("save-as"), shortHelp="Сохранить файл под другим именем\tCTRL+SHIFT+S") # type: ignore
        self.AddTool(wx.ID_PRINT, "Печать", get_icon("print"), shortHelp="Печать документа\tCTRL+P") # type: ignore
        self.AddTool(wx.ID_COPY, "Копировать\tCTRL+C", get_icon("copy"), shortHelp="Копировать выделенное\tCTRL+C") # type: ignore
        self.AddTool(wx.ID_CUT, "Вырезать\tCTRL+X", get_icon("cut"), shortHelp="Вырезать выделенное\tCTRL+X") # type: ignore
        self.AddTool(wx.ID_PASTE, "Вставить\tCTRL+V", get_icon("paste"), shortHelp="Вставить из буфера обмена\tCTRL+V") # type: ignore

        self.EnableTool(wx.ID_PASTE, False)
        self.EnableTool(wx.ID_COPY, False)
        self.EnableTool(wx.ID_CUT, False)
        self.EnableTool(wx.ID_PRINT, False)
        self.EnableTool(wx.ID_SAVE, False)
        self.EnableTool(wx.ID_SAVEAS, False)
        
        # Add edit operations
        self.AddTool(wx.ID_UNDO, "Отменить\tCTRL+Z", get_icon("undo"), shortHelp="Отменить последнее действие\tCTRL+Z") # type: ignore
        self.EnableTool(wx.ID_UNDO, False)
        self.AddTool(wx.ID_REDO, "Вернуть\tCTRL+Y", get_icon("redo"),   shortHelp="Вернуть отмененное действие\tCTRL+Y") # type: ignore
        self.EnableTool(wx.ID_REDO, False)
        self.AddStretchableSpace()
        self.AddTool(wx.ID_ZOOM_IN, "Приблизить", get_icon("zoom-in"), shortHelp="Приблизить") # type: ignore
        self.AddTool(wx.ID_ZOOM_OUT, "Отдалить", get_icon("zoom-out"), shortHelp="Отдалить") # type: ignore
        self.AddTool(wx.ID_ZOOM_FIT, "Показать все", get_icon("zoom-to-fit"), shortHelp="Показать все") # type: ignore
        
        # Finalize toolbar
        self.Realize()