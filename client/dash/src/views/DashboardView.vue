<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useWebSocket } from '@/services/websocket'
import type { Strategy, Position } from '@/types'

const { connect, disconnect, onUpdate } = useWebSocket()

const strategies = ref<Strategy[]>([])
const prices = ref<Record<string, number>>({})

// Sorting state
type SortableColumn = keyof typeof sortableColumns
const sortColumn = ref<SortableColumn>('symbol')
const sortDirection = ref('asc')

// Sortable columns configuration
const sortableColumns = {
  symbol: { key: 'instrument.internalCode', type: 'string' },
  quantity: { key: 'quantity', type: 'number' },
  currentPrice: { key: 'lastPrice', type: 'number' },
  openingPrice: { key: 'openingPrice', type: 'number' },
  entryPrice: { key: 'entryPrice', type: 'number' },
  positionValue: { key: 'positionValue', type: 'number' },
  dailyPnL: { key: 'dailyPnL', type: 'number' },
  totalPnL: { key: 'totalPnL', type: 'number' }
}

// Computed property to get all positions from selected strategies
const selectedPositions = computed(() => {
  return strategies.value
    .filter(strategy => strategy.selected)
    .flatMap(strategy => strategy.positions)
})

// Computed property to aggregate positions by symbol
const aggregatedPositions = computed(() => {
  const aggregated: Record<string, Position> = {}
  
  selectedPositions.value.forEach(position => {
    const symbol = position.instrument.internalCode
    if (!aggregated[symbol]) {
      aggregated[symbol] = {
        ...position,
        quantity: 0,
        lastPrice: position.lastPrice,
        positionValue: 0,
        dailyPnL: 0,
        totalPnL: 0
      }
    }
    
    // Aggregate quantities and calculate metrics
    aggregated[symbol].quantity += position.quantity
    aggregated[symbol].positionValue = computePositionValue(aggregated[symbol])
    aggregated[symbol].dailyPnL = computePositionDailyPnL(aggregated[symbol])
    aggregated[symbol].totalPnL = computePositionTotalPnL(aggregated[symbol])
  })
  
  return Object.values(aggregated)
})

// Computed property for sorted positions
const sortedPositions = computed(() => {
  const positions = [...aggregatedPositions.value]
  const column = sortableColumns[sortColumn.value]
  
  return positions.sort((a, b) => {
    let valueA, valueB
    
    if (column.key === 'positionValue') {
      valueA = computePositionValue(a)
      valueB = computePositionValue(b)
    } else if (column.key === 'dailyPnL') {
      valueA = computePositionDailyPnL(a)
      valueB = computePositionDailyPnL(b)
    } else if (column.key === 'totalPnL') {
      valueA = computePositionTotalPnL(a)
      valueB = computePositionTotalPnL(b)
    } else {
      valueA = column.key.split('.').reduce((obj: any, key) => obj[key], a)
      valueB = column.key.split('.').reduce((obj: any, key) => obj[key], b)
    }
    
    if (column.type === 'string') {
      return sortDirection.value === 'asc' 
        ? valueA.localeCompare(valueB)
        : valueB.localeCompare(valueA)
    } else {
      return sortDirection.value === 'asc'
        ? valueA - valueB
        : valueB - valueA
    }
  })
})

// Function to handle header click
const handleSort = (column: string) => {
  if (sortColumn.value === column) {
    sortDirection.value = sortDirection.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortColumn.value = column as SortableColumn
    sortDirection.value = 'asc'
  }
}

// Function to get sort icon
const getSortIcon = (column: string) => {
  if (sortColumn.value !== column) return '↕️'
  return sortDirection.value === 'asc' ? '↑' : '↓'
}

// Helper functions for position calculations
const computePositionValue = (position: Position) => {
  return position.quantity * position.lastPrice
}

const computePositionDailyPnL = (position: Position) => {
  if (!position.openingPrice || !position.lastPrice) {
    console.warn('Missing price data for position:', position)
    return 0
  }
  return position.quantity * (position.lastPrice - position.openingPrice)
}

const computePositionTotalPnL = (position: Position) => {
  if (!position.entryPrice || !position.lastPrice) {
    console.warn('Missing price data for position:', position)
    return 0
  }
  return position.quantity * (position.lastPrice - position.entryPrice)
}

// Helper functions for strategy calculations
const computeStrategyTotalValuation = (strategy: Strategy) => {
  return strategy.positions.reduce((total, position) => {
    return total + Math.abs(computePositionValue(position))
  }, 0)
}

const computeStrategyDailyPnL = (strategy: Strategy) => {
  return strategy.positions.reduce((total, position) => {
    const pnl = computePositionDailyPnL(position)
    if (isNaN(pnl)) {
      console.warn('NaN Daily P&L for position:', position)
      return total
    }
    return total + pnl
  }, 0)
}

const computeStrategyTotalPnL = (strategy: Strategy) => {
  return strategy.positions.reduce((total, position) => {
    const pnl = computePositionTotalPnL(position)
    if (isNaN(pnl)) {
      console.warn('NaN Total P&L for position:', position)
      return total
    }
    return total + pnl
  }, 0)
}

// Helper functions for formatting and styling
const formatCurrency = (value: number) => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD'
  }).format(value)
}

const getPnLClass = (value: number) => {
  return {
    'positive': value > 0,
    'negative': value < 0
  }
}

const toggleStrategy = (strategyId: number) => {
  const strategy = strategies.value.find(s => s.id === strategyId)
  if (strategy) {
    strategy.selected = !strategy.selected
  }
}

// WebSocket handling
onMounted(() => {
  connect()
  
  onUpdate((data) => {
    if (data.type === 'initial' || data.type === 'update') {
      // Preserve selection state when updating strategies
      const newStrategies = (data.data.strategies || []).map((newStrategy: Strategy) => {
        const existingStrategy = strategies.value.find(s => s.id === newStrategy.id)
        return {
          ...newStrategy,
          selected: existingStrategy?.selected ?? false
        }
      })
      strategies.value = newStrategies
      prices.value = data.data.prices || {}
    }
  })
})

onUnmounted(() => {
  disconnect()
})
</script>

<template>
  <div class="dashboard">
    <div class="strategies-grid">
      <div
        v-for="strategy in strategies"
        :key="strategy.id"
        class="strategy-card"
        :class="{ selected: strategy.selected }"
        @click="toggleStrategy(strategy.id)"
      >
        <h3>{{ strategy.name }}</h3>
        <div class="metrics">
          <div class="metric">
            <span class="label">Total Valuation:</span>
            <span>{{ formatCurrency(computeStrategyTotalValuation(strategy)) }}</span>
          </div>
          <div class="metric">
            <span class="label">Total P&L:</span>
            <span :class="getPnLClass(computeStrategyTotalPnL(strategy))">
              {{ formatCurrency(computeStrategyTotalPnL(strategy)) }}
            </span>
          </div>
          <div class="metric">
            <span class="label">Daily P&L:</span>
            <span :class="getPnLClass(computeStrategyDailyPnL(strategy))">
              {{ formatCurrency(computeStrategyDailyPnL(strategy)) }}
            </span>
          </div>
          <div class="risk-metrics">
            <div class="metric">
              <span class="label">VaR (95%):</span>
              <span>{{ formatCurrency(strategy.riskMetrics.var95) }}</span>
            </div>
            <div class="metric">
              <span class="label">Max Drawdown:</span>
              <span>{{ formatCurrency(strategy.riskMetrics.maxDrawdown) }}</span>
            </div>
            <div class="metric">
              <span class="label">Volatility:</span>
              <span>{{ (strategy.riskMetrics.volatility * 100).toFixed(2) }}%</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="positions-table">
      <h2>Positions</h2>
      <table>
        <thead>
          <tr>
            <th @click="handleSort('symbol')" class="sortable">
              Symbol {{ getSortIcon('symbol') }}
            </th>
            <th @click="handleSort('quantity')" class="sortable">
              Quantity {{ getSortIcon('quantity') }}
            </th>
            <th @click="handleSort('currentPrice')" class="sortable">
              Current Price {{ getSortIcon('currentPrice') }}
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
            <td :class="getPnLClass(computePositionDailyPnL(position))">
              {{ formatCurrency(computePositionDailyPnL(position)) }}
            </td>
            <td :class="getPnLClass(computePositionTotalPnL(position))">
              {{ formatCurrency(computePositionTotalPnL(position)) }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<style scoped>
.dashboard {
  padding: 20px;
}

.strategies-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

.strategy-card {
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 15px;
  cursor: pointer;
  transition: all 0.3s ease;
  background: white;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.strategy-card.selected {
  border-color: #4CAF50;
  background-color: #f8fff8;
  box-shadow: 0 4px 8px rgba(76, 175, 80, 0.2);
}

.strategy-card h3 {
  margin: 0 0 15px 0;
  color: #333;
  font-size: 1.2rem;
}

.metrics {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.metric {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 4px 0;
}

.label {
  color: #666;
  font-size: 0.9rem;
}

.risk-metrics {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid #eee;
}

.risk-metrics .label {
  color: #555;
  font-size: 0.85rem;
}

.positive {
  color: #4CAF50;
  font-weight: 500;
}

.negative {
  color: #f44336;
  font-weight: 500;
}

.positions-table {
  margin-top: 30px;
}

table {
  width: 100%;
  border-collapse: collapse;
}

th, td {
  padding: 12px;
  text-align: left;
  border-bottom: 1px solid #ddd;
}

th {
  background-color: #f5f5f5;
  font-weight: bold;
}

tr:hover {
  background-color: #f5f5f5;
}

.sortable {
  cursor: pointer;
  user-select: none;
}

.sortable:hover {
  background-color: #e9e9e9;
}

th {
  position: relative;
  padding-right: 24px; /* Space for sort icon */
}

th::after {
  content: '';
  position: absolute;
  right: 8px;
  top: 50%;
  transform: translateY(-50%);
}
</style> 