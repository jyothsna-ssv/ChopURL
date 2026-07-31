<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { useAuth } from './auth'
import { useRouter } from 'vue-router'

const router = useRouter()
const { currentUser, signOut } = useAuth()
const statusMessage = ref('')
const errorMessage = ref('')

const handleSignOut = async () => {
  statusMessage.value = ''
  errorMessage.value = ''
  try {
    await signOut()
    statusMessage.value = 'You have been signed out.'
    await router.push('/')
  } catch {
    errorMessage.value = 'Unable to sign out. Please try again.'
  }
}

const handleExpiredSession = async () => {
  statusMessage.value = ''
  errorMessage.value = ''
  await router.push({
    name: 'Login',
    query: { expired: '1', redirect: router.currentRoute.value.fullPath },
  })
}

onMounted(() => window.addEventListener('chopurl:session-expired', handleExpiredSession))
onBeforeUnmount(() => window.removeEventListener('chopurl:session-expired', handleExpiredSession))
</script>

<template>
  <div class="app">
    <nav class="navbar">
      <div class="nav-container">
        <router-link to="/" class="nav-brand">
          <span class="brand-text">ChopURL</span>
        </router-link>
        
        <div class="nav-actions">
          <template v-if="currentUser">
            <div class="user-info">
              <div class="user-avatar">
                {{ (currentUser.user_metadata?.username || currentUser.email)?.[0]?.toUpperCase() || '?' }}
              </div>
              <span class="user-email">{{ currentUser.user_metadata?.username || currentUser.email || currentUser.phone || 'User' }}</span>
            </div>
            <button @click="handleSignOut" class="nav-btn sign-out-btn">Sign Out</button>
          </template>
          <template v-else>
            <router-link to="/login" class="nav-btn sign-in-btn">Sign In</router-link>
          </template>
        </div>
      </div>
    </nav>

    <p v-if="statusMessage" class="app-message app-message-success" role="status">
      {{ statusMessage }}
    </p>
    <p v-if="errorMessage" class="app-message app-message-error" role="alert">
      {{ errorMessage }}
    </p>
    
    <router-view />
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

.app-message {
  position: fixed;
  top: 68px;
  left: 50%;
  z-index: 1001;
  max-width: calc(100% - 2rem);
  margin: 0;
  padding: 0.65rem 1rem;
  border-radius: 6px;
  transform: translateX(-50%);
  box-shadow: 0 3px 10px rgba(0, 0, 0, 0.12);
}

.app-message-success {
  background: #e6fffa;
  color: #0f5132;
}

.app-message-error {
  background: #fff5f5;
  color: #9b2c2c;
}

/* Navbar */
.navbar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 1000;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-bottom: 1px solid rgba(0, 0, 0, 0.08);
  padding: 0;
}

.nav-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0.75rem 2rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.nav-brand {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  text-decoration: none;
  font-size: 1.25rem;
  font-weight: 700;
  color: #1a202c;
  transition: opacity 0.2s;
}

.nav-brand:hover {
  opacity: 0.8;
}

.brand-text {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.nav-actions {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.user-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.85rem;
  font-weight: 600;
}

.user-email {
  font-size: 0.9rem;
  color: #4a5568;
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.nav-btn {
  padding: 0.5rem 1.25rem;
  border-radius: 8px;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  text-decoration: none;
  border: none;
}

.sign-in-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.sign-in-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.sign-out-btn {
  background: #f7fafc;
  color: #4a5568;
  border: 1px solid #e2e8f0;
}

.sign-out-btn:hover {
  background: #edf2f7;
  border-color: #cbd5e0;
}

@media (max-width: 640px) {
  .user-email {
    display: none;
  }
  
  .nav-container {
    padding: 0.75rem 1rem;
  }
}
</style>
