from typing import List, Dict, TypedDict

class FinancialInstrument(TypedDict):
    internalCode: str
    bloombergTicker: str
    reutersTicker: str
    instrumentType: str
    currency: str

class Position(TypedDict):
    instrument: FinancialInstrument
    quantity: float
    dailyPnL: float
    totalPnL: float

class RiskMetrics(TypedDict):
    var95: float
    var99: float
    maxDrawdown: float
    exposure: float
    riskLimit: float

class Strategy(TypedDict):
    id: int
    name: str
    selected: bool
    positions: List[Position]
    riskMetrics: RiskMetrics 