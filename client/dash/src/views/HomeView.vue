<script setup lang="ts">
import StrategyList from '@/components/StrategyList.vue'
</script>

<template>
  <div class="home">
    <main class="main-content">
      <StrategyList />
    </main>
  </div>
</template>

<style scoped>
.home {
  min-height: 100vh;
  background-color: #f5f7fa;
}

.main-content {
  padding: 2rem;
  max-width: 1200px;
  margin: 0 auto;
}
</style>
