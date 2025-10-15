<template>
  <div class="links-page">
    <!-- Header Section -->
    <header class="page-header">
      <div class="header-background">
        <div class="header-pattern"></div>
      </div>
      <div class="header-content">
        <div class="header-nav">
          <router-link to="/" class="back-btn">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M19 12H5"></path>
              <path d="M12 19l-7-7 7-7"></path>
            </svg>
            <span>Back to Home</span>
          </router-link>
        </div>
        
        <div class="header-text">
          <h1 class="page-title">
            Shortened Links
          </h1>
          <p class="page-subtitle">Manage and track all your shortened URLs</p>
        </div>
      </div>
    </header>

    <!-- Main Content -->
    <main class="main-content">
      <div class="content-container">
        <!-- Stats Overview -->
        <div class="stats-overview">
          <div class="stat-card">
            <div class="stat-icon">📊</div>
            <div class="stat-content">
              <span class="stat-number">{{ totalLinks }}</span>
              <span class="stat-label">Total Links</span>
            </div>
          </div>
          <div class="stat-card">
            <div class="stat-icon">👁️</div>
            <div class="stat-content">
              <span class="stat-number">{{ totalClicks }}</span>
              <span class="stat-label">Total Clicks</span>
            </div>
          </div>
          <div class="stat-card">
            <div class="stat-icon">📈</div>
            <div class="stat-content">
              <span class="stat-number">{{ averageClicks }}</span>
              <span class="stat-label">Avg Clicks</span>
            </div>
          </div>
        </div>

            <!-- Links Table -->
            <div class="table-section">
              <LinksTable 
                :links="links" 
                :loading="loading"
                :error="error"
                @viewStats="handleViewStats"
                @deleteLink="handleDeleteLink"
                @refresh="loadLinks"
              />
            </div>

        <!-- Pagination -->
        <div v-if="totalPages > 1" class="simple-pagination">
          <button 
            @click="goToPage(currentPage - 1)" 
            :disabled="currentPage === 1"
            class="pagination-btn prev-btn"
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M15 18l-6-6 6-6"></path>
            </svg>
            <span>Previous</span>
          </button>
          
          <span class="page-text">{{ currentPage }} of {{ totalPages }}</span>
          
          <button 
            @click="goToPage(currentPage + 1)" 
            :disabled="currentPage === totalPages"
            class="pagination-btn next-btn"
          >
            <span>Next</span>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M9 18l6-6-6-6"></path>
            </svg>
          </button>
        </div>

        <!-- Clear All Button - Moved to bottom -->
        <div class="clear-all-section">
          <button @click="clearAllLinks" class="clear-all-btn" :disabled="loading">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M3 6h18"></path>
              <path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"></path>
              <path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"></path>
            </svg>
            <span>Clear All Links</span>
          </button>
        </div>
      </div>
    </main>
    
    <!-- Stats Modal -->
    <StatsModal 
      :isOpen="showStatsModal"
      :link="selectedLink"
      @close="closeStatsModal"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { api } from '../api'
import LinksTable from '../components/LinksTable.vue'
import StatsModal from '../components/StatsModal.vue'

const links = ref([])
const loading = ref(false)
const error = ref('')
const currentPage = ref(1)
const totalPages = ref(1)
const showStatsModal = ref(false)
const selectedLink = ref(null)

const ITEMS_PER_PAGE = 8

const loadLinks = async () => {
  loading.value = true
  error.value = ''
  try {
    // Always make real API calls
    const skip = (currentPage.value - 1) * ITEMS_PER_PAGE
    const response = await api.get(`/admin/links?skip=${skip}&limit=${ITEMS_PER_PAGE}`)
    links.value = response.data
    
    // Get total count for proper pagination
    const totalResponse = await api.get('/admin/links')
    const totalLinks = totalResponse.data.length
    totalPages.value = Math.max(1, Math.ceil(totalLinks / ITEMS_PER_PAGE))
  } catch (err) {
    console.error('Error loading links:', err)
    error.value = 'Failed to load links. Please try again.'
  } finally {
    loading.value = false
  }
}

const goToPage = (page) => {
  if (page >= 1 && page <= totalPages.value) {
    currentPage.value = page
    loadLinks()
  }
}

const handleViewStats = (link) => {
  selectedLink.value = link
  showStatsModal.value = true
}

const closeStatsModal = () => {
  showStatsModal.value = false
  selectedLink.value = null
}

const totalLinks = computed(() => links.value.length)

const totalClicks = computed(() => {
  return links.value.reduce((sum, link) => sum + link.clicks, 0)
})

const averageClicks = computed(() => {
  if (links.value.length === 0) return 0
  return Math.round(totalClicks.value / links.value.length)
})

const handleDeleteLink = async (shortCode) => {
  if (confirm('Are you sure you want to delete this link?')) {
    try {
      // Always make real API call
      await api.delete(`/admin/links/${shortCode}`)
      await loadLinks() // Refresh the list
    } catch (error) {
      console.error('Error deleting link:', error)
      alert('Failed to delete link')
    }
  }
}

const clearAllLinks = async () => {
  if (confirm('Are you sure you want to delete ALL links? This action cannot be undone!')) {
    try {
      // Always make real API call
      await api.delete('/admin/links/clear/all')
      currentPage.value = 1
      await loadLinks() // Refresh the list
      alert('All links have been cleared')
    } catch (error) {
      console.error('Error clearing links:', error)
      alert('Failed to clear links')
    }
  }
}

onMounted(() => {
  loadLinks()
})
</script>

<style scoped>
.links-page {
  min-height: 100vh;
  background: #fafbfc;
}

/* Header Section */
.page-header {
  position: relative;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 3rem 0;
  overflow: hidden;
}

.header-background {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 1;
}

.header-pattern {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><pattern id="grain" width="100" height="100" patternUnits="userSpaceOnUse"><circle cx="50" cy="50" r="1" fill="white" opacity="0.1"/></pattern></defs><rect width="100" height="100" fill="url(%23grain)"/></svg>');
  opacity: 0.3;
}

.header-content {
  position: relative;
  z-index: 2;
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 2rem;
  display: flex;
  align-items: center;
  gap: 2rem;
}

.header-nav {
  flex-shrink: 0;
}

.back-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 12px;
  color: white;
  text-decoration: none;
  font-weight: 500;
  transition: all 0.3s ease;
}

.back-btn:hover {
  background: rgba(255, 255, 255, 0.2);
  transform: translateY(-2px);
}

.back-btn svg {
  width: 20px;
  height: 20px;
}

.header-text {
  flex: 1;
  text-align: center;
}

.page-title {
  font-size: 2.5rem;
  font-weight: 700;
  margin-bottom: 0.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1rem;
}

.title-icon {
  font-size: 2rem;
}

.page-subtitle {
  font-size: 1.1rem;
  opacity: 0.9;
  font-weight: 300;
}

.header-actions {
  flex: 1;
  display: flex;
  justify-content: flex-end;
}

.clear-all-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem;
  background: rgba(220, 53, 69, 0.9);
  border: 1px solid rgba(220, 53, 69, 0.3);
  border-radius: 12px;
  color: white;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
}

.clear-all-btn:hover:not(:disabled) {
  background: rgba(220, 53, 69, 1);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(220, 53, 69, 0.3);
}

.clear-all-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.clear-all-btn svg {
  width: 20px;
  height: 20px;
}

/* Main Content */
.main-content {
  padding: 2rem 0;
}

.content-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 2rem;
}

/* Stats Overview */
.stats-overview {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1.5rem;
  margin-bottom: 3rem;
}

.stat-card {
  background: white;
  padding: 2rem;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  border: 1px solid #e2e8f0;
  display: flex;
  align-items: center;
  gap: 1rem;
  transition: all 0.3s ease;
}

.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 32px rgba(102, 126, 234, 0.15);
}

.stat-icon {
  font-size: 2rem;
  width: 60px;
  height: 60px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.stat-content {
  display: flex;
  flex-direction: column;
}

.stat-number {
  font-size: 2rem;
  font-weight: 700;
  color: #1a202c;
  margin-bottom: 0.25rem;
}

.stat-label {
  font-size: 0.9rem;
  color: #718096;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  font-weight: 500;
}

/* Table Section */
.table-section {
  background: white;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  border: 1px solid #e2e8f0;
  overflow: hidden;
  margin-bottom: 2rem;
}

/* Simple Pagination */
.simple-pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  margin: 1rem 0;
}

.page-text {
  font-size: 0.75rem;
  color: #718096;
  font-weight: 500;
}

/* Clear All Section - Moved to bottom */
.clear-all-section {
  display: flex;
  justify-content: center;
  margin-top: 2rem;
  padding-top: 2rem;
  border-top: 1px solid #e2e8f0;
}

.clear-all-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem;
  background: linear-gradient(135deg, #e53e3e 0%, #c53030 100%);
  color: white;
  border: none;
  border-radius: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 16px rgba(229, 62, 62, 0.3);
}

.clear-all-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(229, 62, 62, 0.4);
  background: linear-gradient(135deg, #c53030 0%, #9c2626 100%);
}

.clear-all-btn:disabled {
  background: #cbd5e0;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.clear-all-btn svg {
  width: 18px;
  height: 18px;
}

/* Pagination Buttons */
.pagination-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.5rem 0.875rem;
  background: #f7fafc;
  color: #4a5568;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  font-weight: 500;
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.2s ease;
}

.pagination-btn:hover:not(:disabled) {
  background: #edf2f7;
  border-color: #cbd5e0;
  transform: none;
}

.pagination-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.next-btn {
  background: #667eea;
  color: white;
  border-color: #667eea;
}

.next-btn:hover:not(:disabled) {
  background: #5a67d8;
  border-color: #5a67d8;
}

.pagination-btn svg {
  width: 14px;
  height: 14px;
}

/* Responsive Design */
@media (max-width: 768px) {
  .header-content {
    flex-direction: column;
    text-align: center;
    gap: 1.5rem;
  }
  
  .page-title {
    font-size: 2rem;
  }
  
  .stats-overview {
    grid-template-columns: 1fr;
    gap: 1rem;
  }
  
  .stat-card {
    padding: 1.5rem;
  }
  
  .pagination {
    flex-direction: column;
    gap: 1rem;
  }
  
  .pagination-info {
    order: -1;
  }
}

@media (max-width: 480px) {
  .page-title {
    font-size: 1.8rem;
    flex-direction: column;
    gap: 0.5rem;
  }
  
  .title-icon {
    font-size: 1.5rem;
  }
  
  .page-subtitle {
    font-size: 1rem;
  }
  
  .stat-card {
    padding: 1rem;
  }
  
  .stat-number {
    font-size: 1.5rem;
  }
  
  .pagination-btn {
    width: 100%;
    justify-content: center;
  }
}
</style>
