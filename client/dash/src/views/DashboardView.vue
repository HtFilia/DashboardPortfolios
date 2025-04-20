<script setup lang="ts">
import { computed, ref, onMounted, onUnmounted } from 'vue';
import { websocketService } from '../services/websocket';
import type { Strategy, Position } from '../types';

const strategies = ref<Strategy[]>([]);
const selectedStrategies = ref<Set<number>>(new Set());

// Subscribe to WebSocket updates
onMounted(() => {
  const unsubscribe = websocketService.onUpdate((data) => {
    if (data.type === 'initial') {
      strategies.value = data.data.strategies;
    } else if (data.type === 'update') {
      // Update existing strategies with new data
      data.data.strategies.forEach(updatedStrategy => {
        const index = strategies.value.findIndex(s => s.id === updatedStrategy.id);
        if (index !== -1) {
          strategies.value[index] = {
            ...strategies.value[index],
            ...updatedStrategy,
            selected: strategies.value[index].selected // Preserve selection state
          };
        }
      });
    }
  });

  onUnmounted(() => {
    unsubscribe();
  });
});

const aggregatedPositions = computed(() => {
  const positionMap = new Map<string, Position>();
  
  // Get all positions from selected strategies
  strategies.value.forEach(strategy => {
    if (selectedStrategies.value.has(strategy.id)) {
      strategy.positions.forEach(position => {
        const symbol = position.instrument.internalCode;
        const existingPosition = positionMap.get(symbol);
        
        if (existingPosition) {
          // Aggregate positions with the same symbol
          positionMap.set(symbol, {
            ...existingPosition,
            quantity: existingPosition.quantity + position.quantity,
            dailyPnL: existingPosition.dailyPnL + position.dailyPnL,
            totalPnL: existingPosition.totalPnL + position.totalPnL
          });
        } else {
          // Add new position
          positionMap.set(symbol, { ...position });
        }
      });
    }
  });
  
  return Array.from(positionMap.values());
});

const toggleStrategy = (strategy: Strategy) => {
  if (selectedStrategies.value.has(strategy.id)) {
    selectedStrategies.value.delete(strategy.id);
  } else {
    selectedStrategies.value.add(strategy.id);
  }
  websocketService.toggleStrategy(strategy.id);
};

const isStrategySelected = (strategyId: number) => {
  return selectedStrategies.value.has(strategyId);
};
</script>

<template>
  <div class="dashboard">
    <div class="strategy-cards">
      <div 
        v-for="strategy in strategies" 
        :key="strategy.id"
        class="strategy-card"
        :class="{ selected: isStrategySelected(strategy.id) }"
        @click="toggleStrategy(strategy)"
      >
        <h3>{{ strategy.name }}</h3>
        <div class="metrics">
          <div class="metric">
            <span class="label">Total P&L</span>
            <span class="value" :class="{ positive: strategy.positions.reduce((sum, pos) => sum + pos.totalPnL, 0) >= 0 }">
              {{ strategy.positions.reduce((sum, pos) => sum + pos.totalPnL, 0).toFixed(2) }}
            </span>
          </div>
          <div class="metric">
            <span class="label">Daily P&L</span>
            <span class="value" :class="{ positive: strategy.positions.reduce((sum, pos) => sum + pos.dailyPnL, 0) >= 0 }">
              {{ strategy.positions.reduce((sum, pos) => sum + pos.dailyPnL, 0).toFixed(2) }}
            </span>
          </div>
          <div class="metric">
            <span class="label">Exposure</span>
            <span class="value">{{ strategy.riskMetrics.exposure.toFixed(2) }}</span>
          </div>
        </div>
      </div>
    </div>

    <div v-if="aggregatedPositions.length > 0" class="positions-table">
      <h2>Selected Positions</h2>
      <table>
        <thead>
          <tr>
            <th>Instrument</th>
            <th>Quantity</th>
            <th>Daily P&L</th>
            <th>Total P&L</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="position in aggregatedPositions" :key="position.instrument.internalCode">
            <td>{{ position.instrument.internalCode }}</td>
            <td>{{ position.quantity }}</td>
            <td :class="{ positive: position.dailyPnL >= 0 }">{{ position.dailyPnL.toFixed(2) }}</td>
            <td :class="{ positive: position.totalPnL >= 0 }">{{ position.totalPnL.toFixed(2) }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<style scoped>
.dashboard {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.strategy-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1rem;
}

.strategy-card {
  background: white;
  border-radius: 8px;
  padding: 1rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  cursor: pointer;
  transition: all 0.2s;
}

.strategy-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

.strategy-card.selected {
  border: 2px solid var(--primary-color);
  background-color: #f8f9fa;
}

.strategy-card h3 {
  margin-bottom: 1rem;
  color: var(--primary-color);
}

.metrics {
  display: grid;
  gap: 0.5rem;
}

.metric {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.label {
  color: var(--secondary-color);
  font-size: 0.9rem;
}

.value {
  font-weight: 600;
  color: var(--primary-color);
}

.value.positive {
  color: #28a745;
}

.positions-table {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.positions-table h2 {
  padding: 1rem;
  border-bottom: 1px solid #eee;
  color: var(--primary-color);
}

table {
  width: 100%;
  border-collapse: collapse;
}

th, td {
  padding: 1rem;
  text-align: left;
  border-bottom: 1px solid #eee;
}

th {
  background-color: #f8f9fa;
  font-weight: 600;
  color: var(--primary-color);
}

tbody tr:hover {
  background-color: #f8f9fa;
}

.positive {
  color: #28a745;
}
</style> 