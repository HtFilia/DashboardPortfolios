<template>
  <div class="dashboard">
    <div class="header">
      <h1>Portfolio Dashboard</h1>
      <div class="controls">
        <button @click="toggleAllStrategies" class="toggle-btn">
          {{ allStrategiesSelected ? 'Deselect All' : 'Select All' }}
        </button>
      </div>
    </div>

    <div class="strategies-container">
      <div class="strategy-cards">
        <div v-for="strategy in strategies" :key="strategy.id" 
             class="strategy-card" 
             :class="{ 'selected': strategy.selected }"
             @click="toggleStrategy(strategy.id)">
          <div class="strategy-header">
            <h3>{{ strategy.name }}</h3>
            <div class="strategy-status" :class="{ 'selected': strategy.selected }">
              {{ strategy.selected ? 'Selected' : 'Not Selected' }}
            </div>
          </div>
          
          <div class="strategy-metrics">
            <div class="metric">
              <span class="metric-label">Total Valuation</span>
              <span class="metric-value">{{ formatCurrency(computeStrategyTotalValuation(strategy)) }}</span>
            </div>
            <div class="metric">
              <span class="metric-label">Total P&L</span>
              <span class="metric-value" :class="{ 'positive': computeStrategyTotalPnL(strategy) > 0, 'negative': computeStrategyTotalPnL(strategy) < 0 }">
                {{ formatCurrency(computeStrategyTotalPnL(strategy)) }}
              </span>
            </div>
            <div class="metric">
              <span class="metric-label">Daily P&L</span>
              <span class="metric-value" :class="{ 'positive': computeStrategyDailyPnL(strategy) > 0, 'negative': computeStrategyDailyPnL(strategy) < 0 }">
                {{ formatCurrency(computeStrategyDailyPnL(strategy)) }}
              </span>
            </div>
          </div>

          <div class="risk-metrics">
            <h4>Risk Metrics</h4>
            <div class="metric">
              <span class="metric-label">VaR (95%)</span>
              <span class="metric-value">{{ formatCurrency(strategy.riskMetrics.var95) }}</span>
            </div>
            <div class="metric">
              <span class="metric-label">Max Drawdown</span>
              <span class="metric-value">{{ formatCurrency(strategy.riskMetrics.maxDrawdown) }}</span>
            </div>
            <div class="metric">
              <span class="metric-label">Volatility</span>
              <span class="metric-value">{{ formatCurrency(strategy.riskMetrics.volatility) }}</span>
            </div>
          </div>
        </div>
      </div>

      <div class="summary-card">
        <div class="summary-header">
          <h3>Portfolio Summary</h3>
        </div>
        
        <div class="summary-metrics">
          <div class="metric">
            <span class="metric-label">Total Portfolio Valuation</span>
            <span class="metric-value">{{ formatCurrency(totalPortfolioValuation) }}</span>
          </div>
          <div class="metric">
            <span class="metric-label">Total Portfolio P&L</span>
            <span class="metric-value" :class="{ 'positive': totalPortfolioPnL > 0, 'negative': totalPortfolioPnL < 0 }">
              {{ formatCurrency(totalPortfolioPnL) }}
            </span>
          </div>
          <div class="metric">
            <span class="metric-label">Total Daily P&L</span>
            <span class="metric-value" :class="{ 'positive': totalDailyPnL > 0, 'negative': totalDailyPnL < 0 }">
              {{ formatCurrency(totalDailyPnL) }}
            </span>
          </div>
        </div>

        <div class="risk-metrics">
          <h4>Portfolio Risk Metrics</h4>
          <div class="metric">
            <span class="metric-label">Total VaR (95%)</span>
            <span class="metric-value">{{ formatCurrency(totalVar95) }}</span>
          </div>
          <div class="metric">
            <span class="metric-label">Total Max Drawdown</span>
            <span class="metric-value">{{ formatCurrency(totalMaxDrawdown) }}</span>
          </div>
          <div class="metric">
            <span class="metric-label">Total Volatility</span>
            <span class="metric-value">{{ formatCurrency(totalVolatility) }}</span>
          </div>
        </div>
      </div>
    </div>

    <div class="positions-container">
      <h2>Positions</h2>
      <table class="positions-table">
        <thead>
          <tr>
            <th @click="handleSort('symbol')" class="sortable">
              Symbol {{ getSortIcon('symbol') }}
            </th>
            <th @click="handleSort('quantity')" class="sortable">
              Quantity {{ getSortIcon('quantity') }}
            </th>
            <th @click="handleSort('lastPrice')" class="sortable">
              Current Price {{ getSortIcon('lastPrice') }}
            </th>
            <th @click="handleSort('openingPrice')" class="sortable">
              Opening Price {{ getSortIcon('openingPrice') }}
            </th>
            <th @click="handleSort('entryPrice')" class="sortable">
              Entry Price {{ getSortIcon('entryPrice') }}
            </th>
            <th @click="handleSort('positionValue')" class="sortable">
              Position Value {{ getSortIcon('positionValue') }}
            </th>
            <th @click="handleSort('dailyPnL')" class="sortable">
              Daily P&L {{ getSortIcon('dailyPnL') }}
            </th>
            <th @click="handleSort('totalPnL')" class="sortable">
              Total P&L {{ getSortIcon('totalPnL') }}
            </th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="position in sortedPositions" :key="position.instrument.internalCode">
            <td>{{ position.instrument.internalCode }}</td>
            <td>{{ position.quantity }}</td>
            <td>{{ formatCurrency(position.lastPrice) }}</td>
            <td>{{ formatCurrency(position.openingPrice) }}</td>
            <td>{{ formatCurrency(position.entryPrice) }}</td>
            <td>{{ formatCurrency(computePositionValue(position)) }}</td>
            <td :class="{ 'positive': position.dailyPnL > 0, 'negative': position.dailyPnL < 0 }">
              {{ formatCurrency(position.dailyPnL) }}
            </td>
            <td :class="{ 'positive': position.totalPnL > 0, 'negative': position.totalPnL < 0 }">
              {{ formatCurrency(position.totalPnL) }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useWebSocket } from '@/composables/useWebSocket'

// WebSocket setup
const { strategies, connect, disconnect } = useWebSocket()

// Lifecycle hooks
onMounted(() => {
  connect()
})

onUnmounted(() => {
  disconnect()
})

// Sorting state
const sortColumn = ref('symbol')
const sortDirection = ref('asc')

// Sortable columns configuration
const sortableColumns = {
  symbol: { type: 'string', key: 'instrument.internalCode' },
  quantity: { type: 'number', key: 'quantity' },
  lastPrice: { type: 'number', key: 'lastPrice' },
  openingPrice: { type: 'number', key: 'openingPrice' },
  entryPrice: { type: 'number', key: 'entryPrice' },
  positionValue: { type: 'number', key: 'positionValue' },
  dailyPnL: { type: 'number', key: 'dailyPnL' },
  totalPnL: { type: 'number', key: 'totalPnL' }
}

// Computed properties
const allStrategiesSelected = computed(() => {
  return strategies.value.every(strategy => strategy.selected)
})

const aggregatedPositions = computed(() => {
  const positions = new Map()
  
  strategies.value.forEach(strategy => {
    strategy.positions.forEach(position => {
      const key = position.instrument.internalCode
      if (!positions.has(key)) {
        positions.set(key, { ...position, quantity: 0, dailyPnL: 0, totalPnL: 0 })
      }
      const existing = positions.get(key)
      existing.quantity += position.quantity
      existing.dailyPnL += position.dailyPnL
      existing.totalPnL += position.totalPnL
    })
  })
  
  return Array.from(positions.values())
})

const sortedPositions = computed(() => {
  const positions = [...aggregatedPositions.value]
  const { key, type } = sortableColumns[sortColumn.value]
  
  positions.sort((a, b) => {
    let valueA = key.split('.').reduce((obj, k) => obj[k], a)
    let valueB = key.split('.').reduce((obj, k) => obj[k], b)
    
    if (type === 'number') {
      valueA = Number(valueA)
      valueB = Number(valueB)
    }
    
    return sortDirection.value === 'asc' 
      ? valueA > valueB ? 1 : -1
      : valueA < valueB ? 1 : -1
  })
  
  return positions
})

// Helper functions
const formatCurrency = (value) => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(value)
}

const computePositionValue = (position) => {
  return position.quantity * position.lastPrice
}

const computeStrategyTotalValuation = (strategy) => {
  return strategy.positions.reduce((total, position) => {
    return total + computePositionValue(position)
  }, 0)
}

const computeStrategyTotalPnL = (strategy) => {
  return strategy.positions.reduce((total, position) => {
    return total + position.totalPnL
  }, 0)
}

const computeStrategyDailyPnL = (strategy) => {
  return strategy.positions.reduce((total, position) => {
    return total + position.dailyPnL
  }, 0)
}

// Portfolio summary computed properties
const totalPortfolioValuation = computed(() => {
  return strategies.value.reduce((total, strategy) => {
    return total + computeStrategyTotalValuation(strategy)
  }, 0)
})

const totalPortfolioPnL = computed(() => {
  return strategies.value.reduce((total, strategy) => {
    return total + computeStrategyTotalPnL(strategy)
  }, 0)
})

const totalDailyPnL = computed(() => {
  return strategies.value.reduce((total, strategy) => {
    return total + computeStrategyDailyPnL(strategy)
  }, 0)
})

const totalVar95 = computed(() => {
  return strategies.value.reduce((total, strategy) => {
    return total + strategy.riskMetrics.var95
  }, 0)
})

const totalMaxDrawdown = computed(() => {
  return strategies.value.reduce((total, strategy) => {
    return total + strategy.riskMetrics.maxDrawdown
  }, 0)
})

const totalVolatility = computed(() => {
  return strategies.value.reduce((total, strategy) => {
    return total + strategy.riskMetrics.volatility
  }, 0)
})

// Event handlers
const toggleStrategy = (strategyId) => {
  const strategy = strategies.value.find(s => s.id === strategyId)
  if (strategy) {
    strategy.selected = !strategy.selected
  }
}

const toggleAllStrategies = () => {
  const newState = !allStrategiesSelected.value
  strategies.value.forEach(strategy => {
    strategy.selected = newState
  })
}

const handleSort = (column) => {
  if (sortColumn.value === column) {
    sortDirection.value = sortDirection.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortColumn.value = column
    sortDirection.value = 'asc'
  }
}

const getSortIcon = (column) => {
  if (sortColumn.value !== column) return '↕️'
  return sortDirection.value === 'asc' ? '↑' : '↓'
}
</script>

<style scoped>
.dashboard {
  padding: 20px;
  color: #fff;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
}

.header h1 {
  margin: 0;
  font-size: 2rem;
}

.controls {
  display: flex;
  gap: 10px;
}

.toggle-btn {
  background-color: #3a3a3a;
  color: #fff;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.toggle-btn:hover {
  background-color: #4a4a4a;
}

.strategies-container {
  display: flex;
  gap: 20px;
  margin-bottom: 30px;
}

.strategy-cards {
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
  flex: 1;
}

.strategy-card {
  background-color: #2a2a2a;
  border-radius: 8px;
  padding: 20px;
  width: 300px;
  cursor: pointer;
  transition: all 0.2s;
  border: 1px solid #3a3a3a;
}

.strategy-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.strategy-card.selected {
  border-color: #4a9eff;
  background-color: #2a3a4a;
}

.strategy-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.strategy-header h3 {
  margin: 0;
  font-size: 1.2rem;
}

.strategy-status {
  font-size: 0.9rem;
  color: #888;
}

.strategy-status.selected {
  color: #4a9eff;
}

.strategy-metrics {
  margin-bottom: 20px;
}

.metric {
  display: flex;
  justify-content: space-between;
  margin-bottom: 10px;
}

.metric-label {
  color: #888;
}

.metric-value {
  font-weight: 600;
}

.metric-value.positive {
  color: #4caf50;
}

.metric-value.negative {
  color: #f44336;
}

.risk-metrics {
  margin-top: 20px;
  padding-top: 15px;
  border-top: 1px solid #3a3a3a;
}

.risk-metrics h4 {
  margin: 0 0 15px 0;
  color: #fff;
  font-size: 1rem;
}

.summary-card {
  background-color: #2a2a2a;
  border-radius: 8px;
  padding: 20px;
  width: 300px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  border: 1px solid #3a3a3a;
}

.summary-header {
  margin-bottom: 20px;
  padding-bottom: 10px;
  border-bottom: 1px solid #3a3a3a;
}

.summary-header h3 {
  margin: 0;
  color: #fff;
  font-size: 1.2rem;
}

.summary-metrics {
  margin-bottom: 20px;
}

.summary-metrics .metric {
  margin-bottom: 15px;
}

.summary-metrics .metric-value {
  font-size: 1.1rem;
  font-weight: 600;
}

.positions-container {
  margin-top: 30px;
}

.positions-container h2 {
  margin-bottom: 20px;
}

.positions-table {
  width: 100%;
  border-collapse: collapse;
  background-color: #2a2a2a;
  border-radius: 8px;
  overflow: hidden;
}

.positions-table th,
.positions-table td {
  padding: 12px 16px;
  text-align: left;
  border-bottom: 1px solid #3a3a3a;
}

.positions-table th {
  background-color: #1a1a1a;
  font-weight: 600;
  cursor: pointer;
  user-select: none;
}

.positions-table th.sortable:hover {
  background-color: #2a2a2a;
}

.positions-table tr:last-child td {
  border-bottom: none;
}

.positions-table tr:hover {
  background-color: #3a3a3a;
}
</style> 