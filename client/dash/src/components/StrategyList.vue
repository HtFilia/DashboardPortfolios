<template>
  <div class="strategy-list">
    <h2>Portfolio Strategies</h2>
    <div class="strategy-items">
      <div 
        v-for="strategy in strategies" 
        :key="strategy.id" 
        class="strategy-card"
        :class="{ 'selected': strategy.selected }"
        @click="toggleStrategy(strategy)"
      >
        <div class="strategy-header">
          <input
            type="checkbox"
            :id="'strategy-' + strategy.id"
            :checked="strategy.selected"
            @change="handleStrategyChange(strategy)"
          />
          <label :for="'strategy-' + strategy.id">{{ strategy.name }}</label>
        </div>
        <div class="strategy-metrics">
          <div class="metric">
            <span class="metric-label">Daily P&L</span>
            <span :class="['metric-value', { 'positive': strategyDailyPnL(strategy) > 0, 'negative': strategyDailyPnL(strategy) < 0 }]">
              {{ formatNumber(strategyDailyPnL(strategy)) }}
            </span>
          </div>
          <div class="metric">
            <span class="metric-label">Total P&L</span>
            <span :class="['metric-value', { 'positive': strategyTotalPnL(strategy) > 0, 'negative': strategyTotalPnL(strategy) < 0 }]">
              {{ formatNumber(strategyTotalPnL(strategy)) }}
            </span>
          </div>
          <div class="risk-section">
            <div class="risk-metric">
              <span class="metric-label">Exposure</span>
              <span class="metric-value">{{ formatNumber(strategy.riskMetrics.exposure) }}</span>
            </div>
            <div class="risk-metric">
              <span class="metric-label">VaR (95%)</span>
              <span class="metric-value">{{ formatNumber(strategy.riskMetrics.var95) }}</span>
            </div>
            <div class="risk-indicator" :style="{ backgroundColor: getRiskColor(getRiskLevel(strategy)) }">
              {{ getRiskLevel(strategy).toUpperCase() }} RISK
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <div v-if="selectedStrategies.length > 0" class="positions-container">
      <h3>Selected Strategies Positions</h3>
      <PositionList :positions="allPositions" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import PositionList from './PositionList.vue'
import { Strategy, Position, FinancialInstrument } from '@/types/financial'

// Create some sample financial instruments
const instruments: Record<string, FinancialInstrument> = {
  AAPL: {
    internalCode: 'AAPL',
    bloombergTicker: 'AAPL US',
    reutersTicker: 'AAPL.O',
    instrumentType: 'Equity',
    currency: 'USD'
  },
  MSFT: {
    internalCode: 'MSFT',
    bloombergTicker: 'MSFT US',
    reutersTicker: 'MSFT.O',
    instrumentType: 'Equity',
    currency: 'USD'
  },
  GOOGL: {
    internalCode: 'GOOGL',
    bloombergTicker: 'GOOGL US',
    reutersTicker: 'GOOGL.O',
    instrumentType: 'Equity',
    currency: 'USD'
  },
  TSLA: {
    internalCode: 'TSLA',
    bloombergTicker: 'TSLA US',
    reutersTicker: 'TSLA.O',
    instrumentType: 'Equity',
    currency: 'USD'
  },
  AMZN: {
    internalCode: 'AMZN',
    bloombergTicker: 'AMZN US',
    reutersTicker: 'AMZN.O',
    instrumentType: 'Equity',
    currency: 'USD'
  }
}

// Create sample positions
const createPosition = (instrument: FinancialInstrument, quantity: number, dailyPnL: number, totalPnL: number): Position => ({
  instrument,
  quantity,
  dailyPnL,
  totalPnL
})

const strategies = ref<Strategy[]>([
  {
    id: 1,
    name: 'Long-Term Growth',
    selected: false,
    positions: [
      createPosition(instruments.AAPL, 100, 250.50, 1250.75),
      createPosition(instruments.MSFT, 50, 150.25, 750.50),
      createPosition(instruments.GOOGL, 25, 200.75, 1000.25)
    ],
    riskMetrics: {
      var95: 50000,
      var99: 75000,
      maxDrawdown: 25000,
      exposure: 150000,
      riskLimit: 200000
    }
  },
  {
    id: 2,
    name: 'Value Investing',
    selected: false,
    positions: [
      createPosition(instruments.MSFT, 75, 225.75, 1125.25),
      createPosition(instruments.TSLA, 30, -150.50, -750.25),
      createPosition(instruments.AMZN, 40, 300.25, 1500.50)
    ],
    riskMetrics: {
      var95: 45000,
      var99: 65000,
      maxDrawdown: 20000,
      exposure: 120000,
      riskLimit: 180000
    }
  },
  {
    id: 3,
    name: 'Dividend Focus',
    selected: false,
    positions: [
      createPosition(instruments.AAPL, 50, 125.25, 625.50),
      createPosition(instruments.MSFT, 100, 300.50, 1500.75),
      createPosition(instruments.AMZN, 20, 150.25, 750.50)
    ],
    riskMetrics: {
      var95: 35000,
      var99: 50000,
      maxDrawdown: 15000,
      exposure: 100000,
      riskLimit: 150000
    }
  },
  {
    id: 4,
    name: 'Sector Rotation',
    selected: false,
    positions: [
      createPosition(instruments.TSLA, 50, -250.75, -1250.25),
      createPosition(instruments.GOOGL, 40, 320.50, 1600.75),
      createPosition(instruments.AMZN, 30, 225.25, 1125.50)
    ],
    riskMetrics: {
      var95: 60000,
      var99: 85000,
      maxDrawdown: 30000,
      exposure: 180000,
      riskLimit: 250000
    }
  },
  {
    id: 5,
    name: 'Market Neutral',
    selected: false,
    positions: [
      createPosition(instruments.AAPL, 100, 250.50, 1250.75),
      createPosition(instruments.TSLA, -100, 250.50, 1250.75),
      createPosition(instruments.GOOGL, 50, 200.75, 1000.25),
      createPosition(instruments.AMZN, -50, -200.75, -1000.25)
    ],
    riskMetrics: {
      var95: 40000,
      var99: 60000,
      maxDrawdown: 20000,
      exposure: 160000,
      riskLimit: 200000
    }
  }
])

const selectedStrategies = computed(() => strategies.value.filter(s => s.selected))

const allPositions = computed(() => {
  const positionMap = new Map<string, Position>()
  
  selectedStrategies.value.forEach(strategy => {
    strategy.positions.forEach(position => {
      const key = position.instrument.internalCode
      if (positionMap.has(key)) {
        const existingPosition = positionMap.get(key)!
        positionMap.set(key, {
          instrument: existingPosition.instrument,
          quantity: existingPosition.quantity + position.quantity,
          dailyPnL: existingPosition.dailyPnL + position.dailyPnL,
          totalPnL: existingPosition.totalPnL + position.totalPnL
        })
      } else {
        positionMap.set(key, { ...position })
      }
    })
  })
  
  return Array.from(positionMap.values())
    .sort((a, b) => b.dailyPnL - a.dailyPnL)
})

const strategyDailyPnL = (strategy: Strategy): number => {
  return strategy.positions.reduce((sum, position) => sum + position.dailyPnL, 0)
}

const strategyTotalPnL = (strategy: Strategy): number => {
  return strategy.positions.reduce((sum, position) => sum + position.totalPnL, 0)
}

const formatNumber = (num: number): string => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(num)
}

const toggleStrategy = (strategy: Strategy) => {
  strategy.selected = !strategy.selected
  handleStrategyChange(strategy)
}

const handleStrategyChange = (strategy: Strategy) => {
  console.log(`Strategy ${strategy.name} ${strategy.selected ? 'selected' : 'deselected'}`)
}

const getRiskLevel = (strategy: Strategy): 'low' | 'medium' | 'high' => {
  const exposureRatio = strategy.riskMetrics.exposure / strategy.riskMetrics.riskLimit
  if (exposureRatio > 0.9) return 'high'
  if (exposureRatio > 0.7) return 'medium'
  return 'low'
}

const getRiskColor = (level: 'low' | 'medium' | 'high'): string => {
  switch (level) {
    case 'low': return '#28a745'
    case 'medium': return '#ffc107'
    case 'high': return '#dc3545'
  }
}
</script>

<style scoped>
.strategy-list {
  max-width: 100%;
  margin: 0 auto;
  padding: 1rem;
}

h2 {
  color: #2c3e50;
  margin-bottom: 1rem;
  font-size: 1.2rem;
}

h3 {
  color: #2c3e50;
  margin: 1.5rem 0 1rem;
  font-size: 1.1rem;
}

.strategy-items {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 1rem;
}

.strategy-card {
  background-color: #f8f9fa;
  border-radius: 8px;
  padding: 1rem;
  cursor: pointer;
  transition: all 0.2s;
  border: 1px solid #e9ecef;
  min-height: 180px;
}

.strategy-card:hover {
  background-color: #e9ecef;
  transform: translateY(-2px);
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.strategy-card.selected {
  background-color: #e3f2fd;
  border-color: #2196f3;
}

.strategy-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
}

.strategy-header input[type="checkbox"] {
  width: 1rem;
  height: 1rem;
  cursor: pointer;
  pointer-events: none;
}

.strategy-header label {
  font-weight: 600;
  color: #2c3e50;
  cursor: pointer;
  pointer-events: none;
  flex: 1;
}

.strategy-metrics {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.metric {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.metric-label {
  font-size: 0.85rem;
  color: #6c757d;
}

.metric-value {
  font-size: 0.9rem;
  font-weight: 500;
}

.positive {
  color: #28a745;
}

.negative {
  color: #dc3545;
}

.positions-container {
  margin-top: 1.5rem;
}

.risk-section {
  margin-top: 0.75rem;
  padding-top: 0.75rem;
  border-top: 1px solid #e9ecef;
}

.risk-metric {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.25rem;
}

.risk-indicator {
  margin-top: 0.5rem;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 600;
  color: white;
  text-align: center;
  text-transform: uppercase;
}
</style> 