<template>
  <div class="strategy-table">
    <table>
      <thead>
        <tr>
          <th>Strategy</th>
          <th>Instrument</th>
          <th>Quantity</th>
          <th>Daily P&L</th>
          <th>Total P&L</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="strategy in strategies" :key="strategy.id">
          <td>{{ strategy.name }}</td>
          <td>
            <div v-for="position in strategy.positions" :key="position.instrument.internalCode">
              {{ position.instrument.internalCode }}
            </div>
          </td>
          <td>
            <div v-for="position in strategy.positions" :key="position.instrument.internalCode">
              {{ position.quantity }}
            </div>
          </td>
          <td>
            <div v-for="position in strategy.positions" :key="position.instrument.internalCode">
              {{ position.dailyPnL.toFixed(2) }}
            </div>
          </td>
          <td>
            <div v-for="position in strategy.positions" :key="position.instrument.internalCode">
              {{ position.totalPnL.toFixed(2) }}
            </div>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup lang="ts">
import type { Strategy } from '../types';

defineProps<{
  strategies: Strategy[];
}>();
</script>

<style scoped>
.strategy-table {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  overflow: hidden;
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
}

tbody tr:hover {
  background-color: #f8f9fa;
}
</style> 