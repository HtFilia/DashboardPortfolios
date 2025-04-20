<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useWebSocket } from '@/services/websocket'
import type { Strategy, Position } from '@/types'

const { connect, disconnect, onUpdate } = useWebSocket()

const strategies = ref<Strategy[]>([])
const prices = ref<Record<string, number>>({})

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
        lastPrice: position.lastPrice
      }
    }
    
    // Aggregate quantities
    aggregated[symbol].quantity += position.quantity
  })
  
  return Object.values(aggregated)
})

// Helper functions for position calculations
const computePositionValue = (position: Position) => {
  return position.quantity * position.lastPrice
}

const computePositionDailyPnL = (position: Position) => {
  return position.quantity * (position.lastPrice - position.openingPrice)
}

const computePositionTotalPnL = (position: Position) => {
  return position.quantity * (position.lastPrice - position.entryPrice)
}

// Helper functions for strategy calculations
const computeStrategyExposure = (strategy: Strategy) => {
  return strategy.positions.reduce((total, position) => {
    return total + Math.abs(position.quantity * position.lastPrice)
  }, 0)
}

const computeStrategyDailyPnL = (strategy: Strategy) => {
  return strategy.positions.reduce((total, position) => {
    return total + computePositionDailyPnL(position)
  }, 0)
}

const computeStrategyTotalPnL = (strategy: Strategy) => {
  return strategy.positions.reduce((total, position) => {
    return total + computePositionTotalPnL(position)
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
      const newStrategies = data.data.strategies.map((newStrategy: Strategy) => {
        const existingStrategy = strategies.value.find(s => s.id === newStrategy.id)
        return {
          ...newStrategy,
          selected: existingStrategy?.selected ?? false
        }
      })
      strategies.value = newStrategies
      prices.value = data.data.prices
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
          <div class="metric">
            <span class="label">Exposure:</span>
            <span>{{ formatCurrency(computeStrategyExposure(strategy)) }}</span>
          </div>
        </div>
      </div>
    </div>

    <div class="positions-table">
      <h2>Positions</h2>
      <table>
        <thead>
          <tr>
            <th>Symbol</th>
            <th>Quantity</th>
            <th>Current Price</th>
            <th>Position Value</th>
            <th>Daily P&L</th>
            <th>Total P&L</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="position in aggregatedPositions" :key="position.instrument.internalCode">
            <td>{{ position.instrument.internalCode }}</td>
            <td>{{ position.quantity }}</td>
            <td>{{ formatCurrency(position.lastPrice) }}</td>
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
}

.strategy-card.selected {
  border-color: #4CAF50;
  background-color: #f8fff8;
}

.strategy-card h3 {
  margin: 0 0 10px 0;
}

.metrics {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.metric {
  display: flex;
  justify-content: space-between;
}

.label {
  color: #666;
}

.positive {
  color: #4CAF50;
}

.negative {
  color: #f44336;
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
</style> 