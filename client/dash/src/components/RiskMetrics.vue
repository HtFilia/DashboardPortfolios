<template>
  <div class="risk-metrics">
    <h2>Risk Metrics</h2>
    <div class="metrics-grid">
      <div v-for="strategy in strategies" :key="strategy.id" class="metric-card">
        <h3>{{ strategy.name }}</h3>
        <div class="metric-values">
          <div class="metric">
            <span class="label">VaR 95%</span>
            <span class="value">{{ strategy.riskMetrics.var95.toFixed(2) }}</span>
          </div>
          <div class="metric">
            <span class="label">VaR 99%</span>
            <span class="value">{{ strategy.riskMetrics.var99.toFixed(2) }}</span>
          </div>
          <div class="metric">
            <span class="label">Max Drawdown</span>
            <span class="value">{{ strategy.riskMetrics.maxDrawdown.toFixed(2) }}</span>
          </div>
          <div class="metric">
            <span class="label">Exposure</span>
            <span class="value">{{ strategy.riskMetrics.exposure.toFixed(2) }}</span>
          </div>
          <div class="metric">
            <span class="label">Risk Limit</span>
            <span class="value">{{ strategy.riskMetrics.riskLimit.toFixed(2) }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Strategy } from '../types';

defineProps<{
  strategies: Strategy[];
}>();
</script>

<style scoped>
.risk-metrics {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  padding: 1.5rem;
}

h2 {
  margin-bottom: 1.5rem;
  color: #333;
}

.metrics-grid {
  display: grid;
  gap: 1.5rem;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
}

.metric-card {
  background: #f8f9fa;
  border-radius: 6px;
  padding: 1rem;
}

h3 {
  margin-bottom: 1rem;
  color: #444;
}

.metric-values {
  display: grid;
  gap: 0.5rem;
}

.metric {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.label {
  color: #666;
}

.value {
  font-weight: 600;
  color: #333;
}
</style> 