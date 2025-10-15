<script setup>
import { ref } from 'vue'
import StatsModal from './components/StatsModal.vue'

const showStatsModal = ref(false)
const selectedLink = ref(null)

const handleViewStats = (link) => {
  selectedLink.value = link
  showStatsModal.value = true
}

const closeStatsModal = () => {
  showStatsModal.value = false
  selectedLink.value = null
}
</script>

<template>
  <div class="app">
    <router-view @viewStats="handleViewStats" />
    
    <StatsModal 
      :isOpen="showStatsModal"
      :link="selectedLink"
      @close="closeStatsModal"
    />
  </div>
</template>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
  background-color: #f5f5f5;
}

.app {
  min-height: 100vh;
}

.header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  text-align: center;
  padding: 2rem 1rem;
}

.header h1 {
  font-size: 2.5rem;
  margin-bottom: 0.5rem;
}

.header p {
  font-size: 1.1rem;
  opacity: 0.9;
}

.main {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem 1rem;
}
</style>
