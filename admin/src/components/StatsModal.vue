<template>
  <div v-if="isOpen" class="modal-overlay" @click="closeModal">
    <div class="modal-content" @click.stop>
      <div class="modal-header">
        <h3>Link Statistics</h3>
        <button @click="closeModal" class="close-btn">&times;</button>
      </div>
      
      <div class="modal-body">
        <div v-if="loading" class="loading">
          Loading statistics...
        </div>
        
        <div v-else-if="stats">
          <div class="stats-grid">
            <div class="stat-item">
              <label>Short Code:</label>
              <span>{{ stats.short_code }}</span>
            </div>
            
            <div class="stat-item">
              <label>Original URL:</label>
              <a :href="stats.original_url" target="_blank" class="url-link">
                {{ stats.original_url }}
              </a>
            </div>
            
            <div class="stat-item">
              <label>Short URL:</label>
              <a :href="stats.short_url" target="_blank" class="url-link">
                {{ stats.short_url }}
              </a>
            </div>
            
            <div class="stat-item">
              <label>Total Clicks:</label>
              <span class="clicks-count">{{ stats.clicks }}</span>
            </div>
            
            <div class="stat-item">
              <label>Created:</label>
              <span>{{ formatDate(stats.created_at) }}</span>
            </div>
            
            <div class="stat-item">
              <label>Last Clicked:</label>
              <span>{{ stats.last_clicked ? formatDate(stats.last_clicked) : 'Never' }}</span>
            </div>
          </div>
          
          <div v-if="stats.clicks > 0" class="click-history">
            <h4>Recent Clicks</h4>
            <div class="click-list">
              <div v-for="click in stats.click_history" :key="click.timestamp" class="click-item">
                <span class="click-time">{{ formatDateTime(click.timestamp) }}</span>
                <span class="click-ip">{{ click.ip_address }}</span>
                <span class="click-user-agent">{{ click.user_agent }}</span>
              </div>
            </div>
          </div>
        </div>
        
        <div v-else-if="error" class="error">
          {{ error }}
        </div>
      </div>
      
      <div class="modal-footer">
        <button @click="closeModal" class="btn-secondary">Close</button>
        <button @click="refreshStats" class="btn-primary">Refresh</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { api } from '../api'

const props = defineProps({
  isOpen: {
    type: Boolean,
    default: false
  },
  link: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['close'])

const loading = ref(false)
const error = ref('')
const stats = ref(null)

const loadStats = async () => {
  if (!props.link) return
  
  loading.value = true
  error.value = ''
  
  try {
    const response = await api.get(`/stats/${props.link.short_code}`)
    stats.value = response.data
  } catch (err) {
    error.value = err.response?.data?.detail || 'Failed to load statistics'
  } finally {
    loading.value = false
  }
}

const refreshStats = () => {
  loadStats()
}

const closeModal = () => {
  emit('close')
}

const formatDate = (dateString) => {
  return new Date(dateString).toLocaleDateString()
}

const formatDateTime = (dateString) => {
  return new Date(dateString).toLocaleString()
}

watch(() => props.isOpen, (newValue) => {
  if (newValue && props.link) {
    loadStats()
  }
})
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 8px;
  max-width: 600px;
  width: 90%;
  max-height: 80vh;
  overflow-y: auto;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #eee;
}

.close-btn {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #666;
}

.modal-body {
  padding: 20px;
}

.stats-grid {
  display: grid;
  gap: 15px;
  margin-bottom: 20px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.stat-item label {
  font-weight: bold;
  color: #333;
}

.url-link {
  color: #007bff;
  text-decoration: none;
  word-break: break-all;
}

.url-link:hover {
  text-decoration: underline;
}

.clicks-count {
  font-size: 18px;
  font-weight: bold;
  color: #28a745;
}

.click-history {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #eee;
}

.click-list {
  max-height: 200px;
  overflow-y: auto;
}

.click-item {
  display: flex;
  gap: 15px;
  padding: 8px 0;
  border-bottom: 1px solid #f0f0f0;
  font-size: 14px;
}

.click-time {
  color: #666;
  min-width: 150px;
}

.click-ip {
  color: #007bff;
  min-width: 100px;
}

.click-user-agent {
  color: #333;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 20px;
  border-top: 1px solid #eee;
}

.btn-primary, .btn-secondary {
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.btn-primary {
  background-color: #007bff;
  color: white;
}

.btn-secondary {
  background-color: #6c757d;
  color: white;
}

.loading {
  text-align: center;
  padding: 40px;
  color: #666;
}

.error {
  padding: 10px;
  background-color: #f8d7da;
  color: #721c24;
  border-radius: 4px;
}
</style>
