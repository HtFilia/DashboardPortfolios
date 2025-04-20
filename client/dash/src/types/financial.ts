export interface FinancialInstrument {
  internalCode: string
  bloombergTicker: string
  reutersTicker: string
  instrumentType: string
  currency: string
  [key: string]: string // For future additional attributes
}

export interface Position {
  instrument: FinancialInstrument
  quantity: number
  dailyPnL: number
  totalPnL: number
  [key: string]: any // For future additional attributes
}

export interface RiskMetrics {
  var95: number // Value at Risk at 95% confidence
  var99: number // Value at Risk at 99% confidence
  maxDrawdown: number // Maximum drawdown
  exposure: number // Total exposure
  riskLimit: number // Risk limit for the strategy
  [key: string]: number // For future additional risk metrics
}

export interface Strategy {
  id: number
  name: string
  selected: boolean
  positions: Position[]
  riskMetrics: RiskMetrics
} 