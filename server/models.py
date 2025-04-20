from typing import List, TypedDict, Dict
from enum import Enum
from dataclasses import dataclass

class FinancialInstrument(TypedDict):
    internalCode: str
    bloombergTicker: str
    reutersTicker: str
    instrumentType: str
    currency: str
    assetClass: str  # Added asset class

class Position(TypedDict):
    instrument: FinancialInstrument
    quantity: float
    dailyPnL: float
    totalPnL: float
    lastPrice: float  # Added to track last price for P&L calculation
    openingPrice: float  # Price at the start of the trading day
    entryPrice: float    # Average price paid to enter the position

class RiskMetrics(TypedDict):
    var95: float
    var99: float
    maxDrawdown: float
    exposure: float
    riskLimit: float
    volatility: float  # Added volatility metric

class Strategy(TypedDict):
    id: int
    name: str
    selected: bool
    positions: List[Position]
    riskMetrics: RiskMetrics

class AssetClass(Enum):
    TECH = "Technology"
    FINANCIAL = "Financial"
    COMMODITY = "Commodity"
    UTILITY = "Utility"
    CONSUMER = "Consumer"
    INDUSTRIAL = "Industrial"

@dataclass
class AssetParams:
    base_volatility: float  # Base daily volatility
    mean_reversion: float   # Speed of mean reversion
    long_term_mean: float   # Long-term average return
    jump_probability: float # Probability of price jumps
    jump_scale: float      # Scale of price jumps
    beta: float           # Market beta
    asset_class: AssetClass  # Asset class for specialized modeling 