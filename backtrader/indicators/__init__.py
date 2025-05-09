#!/usr/bin/env python
###############################################################################
#
# Copyright (C) 2015-2023 Daniel Rodriguez
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################

import sys
from . import ema, wma, hma, sma

# The modules below should/must define __all__ with the Indicator objects
# of prepend an "_" (underscore) to private classes/variables


# base for moving averages

# moving averages (so envelope and oscillators can be auto-generated)

# depends on moving averages

# depend on basicops, moving averages and deviations


__all__ = [
    "AccelerationDecelerationOscillator",
    "AO",
    "AroonOscillator",
    "AroonUpDown",
    "ATR",
    "AwesomeOscillator",
    "BBands",
    "CCI",
    "DEMA",
    "DM",
    "DMA",
    "EMA",
    "HMA",
    "Ichimoku",
    "KAMA",
    "KAMAOsc",
    "KST",
    "Lowest",
    "LRSI",
    "MACD",
    "MACDHisto",
    "Momentum",
    "MomentumOscillator",
    "Oscillator",
    "PctChange",
    "PercentRank",
    "PGO",
    "PPO",
    "PPOShort",
    "PriceOsc",
    "RMI",
    "RSI",
    "SMA",
    "SMAEnvelope",
    "Stochastic",
    "UpMove",
    "DownMove",
    "DPO",
    "DV2",
    "EMAEnvelope",
    "EMAOsc",
    "Envelope",
    "HeikinAshi",
    "Highest",
    "ROC",
    "RSI_Safe",
    "SMAOsc",
    "SMMA",
    "SMMAEnvelope",
    "SMMAOsc",
    "StochasticFull",
    "SumN",
    "TEMA",
    "TEMAEnvelope",
    "TEMAOsc",
    "Trix",
    "TSI",
    "UltimateOscillator",
    "Vortex",
    "WilliamsAD",
    "WilliamsR",
    "WMA",
    "WMAEnvelope",
    "WMAOsc",
    "ZLEMA",
    "ZeroLagIndicator",
    "CrossOver",
]

from .sma import MovingAverageSimple as SMA
# Ensure SMA registration before any other indicators
from .accdecoscillator import AccelerationDecelerationOscillator
from .aroon import AroonOscillator, AroonUpDown
from .atr import AverageTrueRange as ATR
from .awesomeoscillator import AwesomeOscillator
from .bollinger import BollingerBands as BBands
from .cci import CCI
from .dema import DEMA
from .dema import TEMA
from .directionalmove import DirectionalMovement as DM, UpMove, DownMove
from .dma import DMA
from .dpo import DPO
from .dv2 import DV2
from .ema import ExponentialMovingAverage as EMA
from .envelope import Envelope
from .heikinashi import HeikinAshi
from .basicops import Highest, Lowest, SumN
from .hma import HullMovingAverage as HMA
from .ichimoku import Ichimoku
from .kama import KAMA
from .kst import KST
from .lrsi import LRSI
from .macd import MACDHisto, MACD
from .stochastic import Stochastic, StochasticFull
from .momentum import Momentum, MomentumOscillator, RateOfChange as ROC
from .oscillator import Oscillator
from .percentchange import PctChange
from .percentrank import PercentRank
from .prettygoodoscillator import PGO
from .priceoscillator import PPO, PPOShort, PriceOscillator as PriceOsc
from .rsi import RSI
from .rmi import RMI
from .rsi import RSI_Safe
from .smma import SmoothedMovingAverage as SMMA
from .trix import Trix
from .tsi import TrueStrengthIndicator as TSI
from .ultimateoscillator import UltimateOscillator
from .vortex import Vortex
from .basicops import SumN
from .williams import WilliamsAD
from .williams import WilliamsR
from .wma import WeightedMovingAverage as WMA
from .zlema import ZeroLagExponentialMovingAverage as ZLEMA
from .zlind import ZeroLagIndicator
from .crossover import CrossOver

AO = AwesomeOscillator
DEMAEnvelope = getattr(sys.modules[__name__], "DEMAEnvelope", None)
DEMAOsc = getattr(sys.modules[__name__], "DEMAOsc", None)
EMAEnvelope = getattr(sys.modules[__name__], "EMAEnvelope", None)
EMAOsc = getattr(sys.modules[__name__], "EMAOsc", None)
SMAEnvelope = getattr(sys.modules[__name__], "SMAEnvelope", None)
KAMAOsc = getattr(sys.modules[__name__], "KAMAOsc", None)
SMAOsc = getattr(sys.modules[__name__], "SMAOsc", None)
SMMAEnvelope = getattr(sys.modules[__name__], "SMMAEnvelope", None)
SMMAOsc = getattr(sys.modules[__name__], "SMMAOsc", None)
TEMAEnvelope = getattr(sys.modules[__name__], "TEMAEnvelope", None)
TEMAOsc = getattr(sys.modules[__name__], "TEMAOsc", None)
WMAEnvelope = getattr(sys.modules[__name__], "WMAEnvelope", None)
WMAOsc = getattr(sys.modules[__name__], "WMAOsc", None)

