from ..utils.py3 import range as range, zip as zip
from .utils import shade_color as shade_color
from _typeshed import Incomplete

class CandlestickPlotHandler:
    legend_opens: Incomplete
    legend_highs: Incomplete
    legend_lows: Incomplete
    legend_closes: Incomplete
    colorup: Incomplete
    colordown: Incomplete
    edgeup: Incomplete
    edgedown: Incomplete
    tickup: Incomplete
    tickdown: Incomplete
    def __init__(self, ax, x, opens, highs, lows, closes, colorup: str = 'k', colordown: str = 'r', edgeup: Incomplete | None = None, edgedown: Incomplete | None = None, tickup: Incomplete | None = None, tickdown: Incomplete | None = None, width: int = 1, tickwidth: int = 1, edgeadjust: float = 0.05, edgeshading: int = -10, alpha: float = 1.0, label: str = '_nolegend', fillup: bool = True, filldown: bool = True, **kwargs) -> None: ...
    def legend_artist(self, legend, orig_handle, fontsize, handlebox): ...
    def barcollection(self, xs, opens, highs, lows, closes, width, tickwidth: int = 1, edgeadjust: int = 0, label: str = '_nolegend', scaling: float = 1.0, bot: int = 0, fillup: bool = True, filldown: bool = True, **kwargs): ...

def plot_candlestick(ax, x, opens, highs, lows, closes, colorup: str = 'k', colordown: str = 'r', edgeup: Incomplete | None = None, edgedown: Incomplete | None = None, tickup: Incomplete | None = None, tickdown: Incomplete | None = None, width: int = 1, tickwidth: float = 1.25, edgeadjust: float = 0.05, edgeshading: int = -10, alpha: float = 1.0, label: str = '_nolegend', fillup: bool = True, filldown: bool = True, **kwargs): ...

class VolumePlotHandler:
    legend_vols: Incomplete
    legend_opens: Incomplete
    legend_closes: Incomplete
    colorup: Incomplete
    colordown: Incomplete
    edgeup: Incomplete
    edgedown: Incomplete
    barcol: Incomplete
    def __init__(self, ax, x, opens, closes, volumes, colorup: str = 'k', colordown: str = 'r', edgeup: Incomplete | None = None, edgedown: Incomplete | None = None, edgeshading: int = -5, edgeadjust: float = 0.05, width: int = 1, alpha: float = 1.0, **kwargs) -> None: ...
    def legend_artist(self, legend, orig_handle, fontsize, handlebox): ...
    def barcollection(self, x, opens, closes, vols, width, edgeadjust: int = 0, vscaling: float = 1.0, vbot: int = 0, **kwargs): ...

def plot_volume(ax, x, opens, closes, volumes, colorup: str = 'k', colordown: str = 'r', edgeup: Incomplete | None = None, edgedown: Incomplete | None = None, edgeshading: int = -5, edgeadjust: float = 0.05, width: int = 1, alpha: float = 1.0, **kwargs): ...

class OHLCPlotHandler:
    legend_opens: Incomplete
    legend_highs: Incomplete
    legend_lows: Incomplete
    legend_closes: Incomplete
    colorup: Incomplete
    colordown: Incomplete
    barcol: Incomplete
    opencol: Incomplete
    closecol: Incomplete
    def __init__(self, ax, x, opens, highs, lows, closes, colorup: str = 'k', colordown: str = 'r', width: int = 1, tickwidth: float = 0.5, alpha: float = 1.0, label: str = '_nolegend', **kwargs) -> None: ...
    def legend_artist(self, legend, orig_handle, fontsize, handlebox): ...
    def barcollection(self, xs, opens, highs, lows, closes, width, tickwidth, label: str = '_nolegend', scaling: float = 1.0, bot: int = 0, **kwargs): ...

def plot_ohlc(ax, x, opens, highs, lows, closes, colorup: str = 'k', colordown: str = 'r', width: float = 1.5, tickwidth: float = 0.5, alpha: float = 1.0, label: str = '_nolegend', **kwargs): ...

class LineOnClosePlotHandler:
    legend_closes: Incomplete
    color: Incomplete
    alpha: Incomplete
    def __init__(self, ax, x, closes, color: str = 'k', width: int = 1, alpha: float = 1.0, label: str = '_nolegend', **kwargs) -> None: ...
    def legend_artist(self, legend, orig_handle, fontsize, handlebox): ...
    def barcollection(self, xs, closes, width, label: str = '_nolegend', scaling: float = 1.0, bot: int = 0, **kwargs): ...

def plot_lineonclose(ax, x, closes, color: str = 'k', width: float = 1.5, alpha: float = 1.0, label: str = '_nolegend', **kwargs): ...
