<template>
  <div class="position-list">
    <table class="position-table">
      <thead>
        <tr>
          <th>Internal Code</th>
          <th>Bloomberg</th>
          <th>Reuters</th>
          <th>Type</th>
          <th>Currency</th>
          <th>Quantity</th>
          <th>Daily P&L</th>
          <th>Total P&L</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="position in positions" :key="position.instrument.internalCode">
          <td>{{ position.instrument.internalCode }}</td>
          <td>{{ position.instrument.bloombergTicker }}</td>
          <td>{{ position.instrument.reutersTicker }}</td>
          <td>{{ position.instrument.instrumentType }}</td>
          <td>{{ position.instrument.currency }}</td>
          <td :class="{ 'positive': position.quantity > 0, 'negative': position.quantity < 0 }">
            {{ position.quantity }}
          </td>
          <td :class="{ 'positive': position.dailyPnL > 0, 'negative': position.dailyPnL < 0 }">
            {{ formatNumber(position.dailyPnL) }}
          </td>
          <td :class="{ 'positive': position.totalPnL > 0, 'negative': position.totalPnL < 0 }">
            {{ formatNumber(position.totalPnL) }}
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup lang="ts">
import { Position } from '@/types/financial'

defineProps<{
  positions: Position[]
}>()

const formatNumber = (num: number): string => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(num)
}
</script>

<style scoped>
.position-list {
  margin-top: 1rem;
  overflow-x: auto;
}

.position-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.9rem;
}

.position-table th,
.position-table td {
  padding: 0.75rem;
  text-align: left;
  border-bottom: 1px solid #e9ecef;
}

.position-table th {
  background-color: #f8f9fa;
  font-weight: 600;
  color: #495057;
}

.position-table tr:hover {
  background-color: #f8f9fa;
}

.positive {
  color: #28a745;
}

.negative {
  color: #dc3545;
}
</style> 