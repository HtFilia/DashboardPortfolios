<script setup lang="ts">
import { onMounted, onUnmounted } from 'vue';
import { RouterLink, RouterView } from 'vue-router';
import { websocketService } from './services/websocket';

onMounted(() => {
  websocketService.connect();
});

onUnmounted(() => {
  websocketService.disconnect();
});
</script>

<template>
  <div class="app">
    <aside class="sidebar">
      <div class="sidebar-header">
        <h1>Portfolio Dashboard</h1>
      </div>
      <nav class="sidebar-nav">
        <RouterLink to="/" class="nav-item">
          <span class="nav-icon">📊</span>
          <span>Dashboard</span>
        </RouterLink>
      </nav>
    </aside>

    <main class="main">
      <RouterView />
    </main>
  </div>
</template>

<style>
:root {
  --primary-color: #2c3e50;
  --secondary-color: #6c757d;
  --background-color: #f5f7fa;
  --sidebar-width: 180px;
  --sidebar-bg: #ffffff;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: Arial, sans-serif;
  background-color: var(--background-color);
}

.app {
  min-height: 100vh;
  display: flex;
}

.sidebar {
  width: var(--sidebar-width);
  background-color: var(--sidebar-bg);
  box-shadow: 2px 0 4px rgba(0, 0, 0, 0.1);
  position: fixed;
  top: 0;
  left: 0;
  bottom: 0;
  display: flex;
  flex-direction: column;
}

.sidebar-header {
  padding: 1rem;
  border-bottom: 1px solid #e9ecef;
}

.sidebar-header h1 {
  font-size: 1.2rem;
  color: var(--primary-color);
}

.sidebar-nav {
  padding: 0.5rem 0;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  color: var(--secondary-color);
  text-decoration: none;
  transition: all 0.2s;
  font-size: 0.9rem;
}

.nav-item:hover {
  background-color: #f8f9fa;
  color: var(--primary-color);
}

.nav-item.router-link-active {
  background-color: #f8f9fa;
  color: var(--primary-color);
  border-left: 3px solid var(--primary-color);
}

.nav-icon {
  font-size: 1rem;
}

.main {
  flex: 1;
  margin-left: var(--sidebar-width);
  padding: 1.5rem;
}
</style>
