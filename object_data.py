from dataclasses import dataclass, field
from typing import List

@dataclass
class DxfPlotLayer:
    name: str
    group: object # SeismicPlotGroup
    visible: bool = True

@dataclass
class DxfPlot:
    filename: str
    affine_transform_filename: str
    data: any # ezdxf modelspace
    layers: List[DxfPlotLayer] = field(default_factory=lambda: [])
    visible: bool = True

@dataclass
class SeismicEvents:
    filename: str = None

