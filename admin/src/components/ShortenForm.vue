<template>
  <div class="shorten-form">
    <div class="form-header">
      <h2>Shorten Your URL</h2>
      <p>Create short links in seconds</p>
    </div>
    
    <form @submit.prevent="shortenUrl" class="form">
      <div class="form-group">
        <label for="url" class="form-label">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"></path>
            <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"></path>
          </svg>
          Long URL
        </label>
        <input
          id="url"
          v-model="formData.url"
          type="url"
          placeholder="https://example.com/very/long/url"
          required
          class="form-input"
        />
      </div>
      
      <div class="form-group">
        <label for="customCode" class="form-label">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"></path>
          </svg>
          Custom Code (Optional)
        </label>
        <input
          id="customCode"
          v-model="formData.customCode"
          type="text"
          placeholder="my-custom-code"
          class="form-input"
        />
      </div>
      
      <button type="submit" :disabled="loading" class="submit-btn">
        <span v-if="loading" class="loading-spinner"></span>
        <span>{{ loading ? 'Shortening...' : 'Shorten URL' }}</span>
        <svg v-if="!loading" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M5 12h14"></path>
          <path d="M12 5l7 7-7 7"></path>
        </svg>
      </button>
    </form>
    
    <div v-if="result" class="result">
      <div class="result-header">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M9 12l2 2 4-4"></path>
          <circle cx="12" cy="12" r="10"></circle>
        </svg>
        <h3>Success! Your short URL is ready</h3>
      </div>
      <div class="short-url">
        <div class="url-display">
          <a :href="result.short_url" target="_blank" class="url-link">{{ result.short_url }}</a>
        </div>
        <button @click="copyToClipboard(result.short_url)" class="copy-btn">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
            <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
          </svg>
          <span>Copy</span>
        </button>
      </div>
    </div>
    
    <div v-if="error" class="error">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="12" cy="12" r="10"></circle>
        <line x1="15" y1="9" x2="9" y2="15"></line>
        <line x1="9" y1="9" x2="15" y2="15"></line>
      </svg>
      <span>{{ error }}</span>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { api } from '../api'

const loading = ref(false)
const error = ref('')
const result = ref(null)

const formData = reactive({
  url: '',
  customCode: ''
})

const shortenUrl = async () => {
  loading.value = true
  error.value = ''
  result.value = null
  
  try {
    console.log('Making API call to:', api.defaults.baseURL + '/shorten')
    console.log('Data being sent:', { url: formData.url, custom_code: formData.customCode || undefined })
    
    // Always make real API call for now
    const response = await api.post('/shorten', {
      url: formData.url,
      custom_code: formData.customCode || undefined
    })
    
    console.log('API response:', response.data)
    result.value = response.data
    
    formData.url = ''
    formData.customCode = ''
  } catch (err) {
    if (err.response?.status === 400 && err.response?.data?.detail?.includes('already exists')) {
      error.value = `Custom code '${formData.customCode}' is already in use. Please choose a different one.`
    } else {
      error.value = err.response?.data?.detail || 'An error occurred'
    }
  } finally {
    loading.value = false
  }
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
.shorten-form {
  max-width: 600px;
  margin: 0 auto;
  background: white;
  border-radius: 20px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.form-header {
  text-align: center;
  padding: 2rem 2rem 1rem;
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
}

.form-header h2 {
  font-size: 1.8rem;
  font-weight: 700;
  color: #1a202c;
  margin-bottom: 0.5rem;
}

.form-header p {
  color: #718096;
  font-size: 1rem;
}

.form {
  padding: 2rem;
}

.form-group {
  margin-bottom: 1.5rem;
}

.form-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
  font-weight: 600;
  color: #2d3748;
  font-size: 0.95rem;
}

.form-label svg {
  width: 18px;
  height: 18px;
  color: #667eea;
}

.form-input {
  width: 100%;
  padding: 1rem 1.25rem;
  border: 2px solid #e2e8f0;
  border-radius: 12px;
  font-size: 16px;
  transition: all 0.3s ease;
  background: #fafbfc;
  color: #2d3748;
}

.form-input:focus {
  outline: none;
  border-color: #667eea;
  background: white;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.form-help {
  display: block;
  margin-top: 0.5rem;
  color: #718096;
  font-size: 0.85rem;
}

.submit-btn {
  width: 100%;
  padding: 1rem 2rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 12px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
}

.submit-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(102, 126, 234, 0.3);
}

.submit-btn:disabled {
  background: #cbd5e0;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.submit-btn svg {
  width: 20px;
  height: 20px;
  transition: transform 0.3s ease;
}

.submit-btn:hover:not(:disabled) svg {
  transform: translateX(4px);
}

.loading-spinner {
  width: 20px;
  height: 20px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top: 2px solid white;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.result {
  margin: 2rem;
  padding: 1.5rem;
  background: linear-gradient(135deg, #f0fff4 0%, #e6fffa 100%);
  border-radius: 16px;
  border: 1px solid #9ae6b4;
  box-shadow: 0 4px 12px rgba(56, 178, 172, 0.1);
}

.result-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 1rem;
}

.result-header svg {
  width: 24px;
  height: 24px;
  color: #38a169;
}

.result-header h3 {
  color: #38a169;
  font-size: 1.1rem;
  font-weight: 600;
  margin: 0;
}

.short-url {
  display: flex;
  gap: 1rem;
  align-items: center;
  flex-wrap: wrap;
}

.url-display {
  flex: 1;
  min-width: 200px;
}

.url-link {
  color: #2b6cb0;
  text-decoration: none;
  word-break: break-all;
  font-weight: 500;
  font-size: 1rem;
  display: block;
  padding: 0.75rem;
  background: white;
  border-radius: 8px;
  border: 1px solid #bee3f8;
}

.url-link:hover {
  text-decoration: underline;
  color: #2c5282;
}

.copy-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.25rem;
  background: #38a169;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  flex-shrink: 0;
}

.copy-btn:hover {
  background: #2f855a;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(56, 161, 105, 0.3);
}

.copy-btn svg {
  width: 16px;
  height: 16px;
}

.error {
  margin: 2rem;
  padding: 1rem 1.25rem;
  background: linear-gradient(135deg, #fed7d7 0%, #feb2b2 100%);
  color: #c53030;
  border-radius: 12px;
  border: 1px solid #fc8181;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-weight: 500;
}

.error svg {
  width: 20px;
  height: 20px;
  flex-shrink: 0;
}

@media (max-width: 768px) {
  .form {
    padding: 1.5rem;
  }
  
  .form-header {
    padding: 1.5rem 1.5rem 1rem;
  }
  
  .form-header h2 {
    font-size: 1.5rem;
  }
  
  .result {
    margin: 1.5rem;
    padding: 1.25rem;
  }
  
  .error {
    margin: 1.5rem;
  }
  
  .short-url {
    flex-direction: column;
    align-items: stretch;
  }
  
  .url-display {
    min-width: auto;
    margin-bottom: 0.75rem;
  }
  
  .copy-btn {
    width: 100%;
    justify-content: center;
  }
}

@media (max-width: 480px) {
  .form {
    padding: 1rem;
  }
  
  .form-header {
    padding: 1rem 1rem 0.75rem;
  }
  
  .form-header h2 {
    font-size: 1.3rem;
  }
  
  .form-header p {
    font-size: 0.9rem;
  }
  
  .result {
    margin: 1rem;
    padding: 1rem;
  }
  
  .error {
    margin: 1rem;
    padding: 0.875rem 1rem;
  }
}
</style>
