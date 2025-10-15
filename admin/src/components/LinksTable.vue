<template>
  <div class="links-table">
    <h2>Shortened Links</h2>
    
    <div v-if="loading" class="loading">
      Loading links...
    </div>
    
    <div v-else-if="links.length === 0" class="no-links">
      No links found. Create your first shortened URL!
    </div>
    
    <div v-else class="table-container">
      <table>
        <thead>
          <tr>
            <th>Short Code</th>
            <th>Original URL</th>
            <th>Short URL</th>
            <th>Clicks</th>
            <th>Created</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="link in links" :key="link.short_code">
            <td>
              <span class="short-code">{{ link.short_code }}</span>
            </td>
            <td class="original-url">
              <a :href="link.original_url" target="_blank" :title="link.original_url">
                {{ link.original_url }}
              </a>
            </td>
            <td class="short-url">
              <a :href="link.short_url" target="_blank">{{ link.short_url }}</a>
            </td>
            <td class="clicks">{{ link.clicks }}</td>
            <td class="created">{{ formatDate(link.created_at) }}</td>
            <td class="actions">
              <button @click="viewStats(link)" class="stats-btn">Stats</button>
              <button @click="copyToClipboard(link.short_url)" class="copy-btn">Copy</button>
              <button @click="deleteLink(link.short_code)" class="delete-btn">Delete</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    
    <div v-if="error" class="error">
      {{ error }}
    </div>
  </div>
</template>

<script setup>
import { defineProps, defineEmits } from 'vue'

const props = defineProps({
  links: {
    type: Array,
    default: () => []
  },
  loading: {
    type: Boolean,
    default: false
  },
  error: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['viewStats', 'deleteLink', 'refresh'])

const truncateUrl = (url) => {
  if (url.length > 50) {
    return url.substring(0, 47) + '...'
  }
  return url
}

const formatDate = (dateString) => {
  return new Date(dateString).toLocaleDateString()
}

const viewStats = (link) => {
  emit('viewStats', link)
}

const deleteLink = (shortCode) => {
  emit('deleteLink', shortCode)
}

const copyToClipboard = async (text) => {
  try {
    await navigator.clipboard.writeText(text)
    alert('Copied to clipboard!')
  } catch (err) {
    console.error('Failed to copy: ', err)
  }
}
</script>

<style scoped>
.links-table {
  max-width: 1400px;
  margin: 0 auto;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.links-table h2 {
  padding: 1.5rem 2rem;
  margin: 0;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  font-size: 1.5rem;
  font-weight: 600;
}

.loading, .no-links {
  text-align: center;
  padding: 3rem 2rem;
  color: #666;
  font-size: 1.1rem;
  background: #f8f9fa;
}

.loading {
  color: #667eea;
  font-weight: 500;
}

.table-container {
  overflow-x: auto;
  background: white;
}

table {
  width: 100%;
  border-collapse: collapse;
  margin: 0;
  font-size: 14px;
}

th, td {
  padding: 1rem;
  text-align: left;
  border-bottom: 1px solid #e9ecef;
  vertical-align: top;
}

th {
  background-color: #f8f9fa;
  font-weight: 600;
  color: #495057;
  font-size: 13px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  position: sticky;
  top: 0;
  z-index: 10;
}

tr:hover {
  background-color: #f8f9fa;
}

.original-url {
  max-width: 300px;
  word-wrap: break-word;
  word-break: break-all;
}

.original-url a {
  color: #007bff;
  text-decoration: none;
  display: block;
  line-height: 1.4;
}

.original-url a:hover {
  text-decoration: underline;
  color: #0056b3;
}

.short-url {
  max-width: 200px;
  word-wrap: break-word;
  word-break: break-all;
}

.short-url a {
  color: #28a745;
  text-decoration: none;
  font-weight: 500;
}

.short-url a:hover {
  text-decoration: underline;
  color: #1e7e34;
}

.short-code {
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  background: #e9ecef;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
  color: #495057;
}

.clicks {
  text-align: center;
  font-weight: 600;
  color: #28a745;
}

.created {
  color: #6c757d;
  font-size: 13px;
}

.actions {
  white-space: nowrap;
}

button {
  padding: 6px 12px;
  margin: 0 2px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 12px;
  font-weight: 500;
  transition: all 0.2s ease;
  display: inline-block;
}

.stats-btn {
  background-color: #28a745;
  color: white;
}

.stats-btn:hover {
  background-color: #218838;
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(40, 167, 69, 0.3);
}

.copy-btn {
  background-color: #007bff;
  color: white;
}

.copy-btn:hover {
  background-color: #0056b3;
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(0, 123, 255, 0.3);
}

.delete-btn {
  background-color: #dc3545;
  color: white;
}

.delete-btn:hover {
  background-color: #c82333;
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(220, 53, 69, 0.3);
}

.error {
  margin: 1rem 2rem;
  padding: 1rem;
  background-color: #f8d7da;
  color: #721c24;
  border-radius: 8px;
  border-left: 4px solid #dc3545;
}

/* Responsive Design */
@media (max-width: 1200px) {
  .original-url {
    max-width: 250px;
  }
  
  .short-url {
    max-width: 150px;
  }
}

@media (max-width: 992px) {
  .links-table h2 {
    padding: 1rem 1.5rem;
    font-size: 1.3rem;
  }
  
  th, td {
    padding: 0.75rem;
  }
  
  .original-url {
    max-width: 200px;
  }
  
  .short-url {
    max-width: 120px;
  }
}

@media (max-width: 768px) {
  .links-table {
    margin: 0 0.5rem;
  }
  
  .links-table h2 {
    padding: 1rem;
    font-size: 1.2rem;
  }
  
  th, td {
    padding: 0.5rem;
    font-size: 13px;
  }
  
  .original-url, .short-url {
    max-width: 150px;
  }
  
  .actions {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }
  
  button {
    margin: 0;
    width: 100%;
    font-size: 11px;
    padding: 4px 8px;
  }
}

@media (max-width: 576px) {
  .table-container {
    font-size: 12px;
  }
  
  th, td {
    padding: 0.4rem;
  }
  
  .original-url, .short-url {
    max-width: 120px;
  }
  
  .short-code {
    font-size: 10px;
    padding: 0.2rem 0.4rem;
  }
}
</style>
