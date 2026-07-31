<script setup>
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuth } from '../auth'

const route = useRoute()
const router = useRouter()
const { signInWithEmail, signUpWithEmail, sendPasswordResetEmail, updatePassword } = useAuth()

const isLoading = ref(false)
const error = ref('')
const success = ref('')
const mode = ref(route.query.mode === 'reset' ? 'reset' : 'sign-in')

const username = ref('')
const email = ref('')
const password = ref('')
const confirmPassword = ref('')
const resetPassword = ref('')
const confirmResetPassword = ref('')

const isSignUp = computed(() => mode.value === 'sign-up')
const isForgotPassword = computed(() => mode.value === 'forgot')
const isResetPassword = computed(() => mode.value === 'reset')

const subtitle = computed(() => {
  if (isSignUp.value) return 'Create an account'
  if (isForgotPassword.value) return 'Send a password reset link'
  if (isResetPassword.value) return 'Choose a new password'
  return 'Sign in to manage your links'
})

const submitLabel = computed(() => {
  if (isSignUp.value) return 'Create Account'
  if (isForgotPassword.value) return 'Send Reset Link'
  if (isResetPassword.value) return 'Reset Password'
  return 'Sign In'
})

const setMode = (nextMode) => {
  mode.value = nextMode
  error.value = ''
  success.value = ''
  password.value = ''
  confirmPassword.value = ''
  resetPassword.value = ''
  confirmResetPassword.value = ''
}

const validateMatchingPasswords = (firstPassword, secondPassword) => {
  if (firstPassword !== secondPassword) {
    error.value = 'Passwords do not match'
    return false
  }
  return true
}

const handleEmailAuth = async () => {
  isLoading.value = true
  error.value = ''
  success.value = ''
  try {
    if (isSignUp.value) {
      if (!username.value.trim()) {
        error.value = 'Username is required'
        return
      }
      if (!validateMatchingPasswords(password.value, confirmPassword.value)) return

      await signUpWithEmail(email.value, password.value, username.value.trim())
      success.value = 'Account created. Check your email for a confirmation link.'
      setMode('sign-in')
      success.value = 'Account created. Check your email for a confirmation link.'
    } else if (isForgotPassword.value) {
      await sendPasswordResetEmail(email.value, `${window.location.origin}/login?mode=reset`)
      success.value = 'Password reset link sent. Check your email.'
    } else if (isResetPassword.value) {
      if (!validateMatchingPasswords(resetPassword.value, confirmResetPassword.value)) return

      await updatePassword(resetPassword.value)
      success.value = 'Password updated. You can sign in with your new password.'
      setMode('sign-in')
      success.value = 'Password updated. You can sign in with your new password.'
    } else {
      await signInWithEmail(email.value, password.value)
      router.push(route.query.redirect || '/')
    }
  } catch (err) {
    error.value = err.message || 'Authentication failed'
  } finally {
    isLoading.value = false
  }
}

watch(
  () => route.query.mode,
  (nextMode) => {
    if (nextMode === 'reset') {
      setMode('reset')
    }
  }
)
</script>

<template>
  <div class="login-page">
    <div class="login-background">
      <div class="login-pattern"></div>
    </div>
    <div class="login-container">
        <div class="login-card">
          <div class="login-header">
            <h1 class="brand">ChopURL</h1>
          <p class="subtitle">{{ subtitle }}</p>
        </div>

        <div class="auth-content">
          <form @submit.prevent="handleEmailAuth" class="auth-form">
            <div v-if="isSignUp" class="form-group">
              <label>Username</label>
              <input v-model="username" type="text" placeholder="Your username" required class="auth-input" />
            </div>
            <div v-if="!isResetPassword" class="form-group">
              <label>Email</label>
              <input v-model="email" type="email" placeholder="you@example.com" required class="auth-input" />
            </div>
            <template v-if="isResetPassword">
              <div class="form-group">
                <label>New Password</label>
                <input v-model="resetPassword" type="password" placeholder="••••••••" required minlength="6" class="auth-input" />
              </div>
              <div class="form-group">
                <label>Confirm New Password</label>
                <input v-model="confirmResetPassword" type="password" placeholder="••••••••" required minlength="6" class="auth-input" />
              </div>
            </template>
            <div v-else-if="!isForgotPassword" class="form-group">
              <label>Password</label>
              <input v-model="password" type="password" placeholder="••••••••" required minlength="6" class="auth-input" />
            </div>
            <div v-if="isSignUp" class="form-group">
              <label>Confirm Password</label>
              <input v-model="confirmPassword" type="password" placeholder="••••••••" required minlength="6" class="auth-input" />
            </div>
            <button type="submit" :disabled="isLoading" class="submit-btn">
              <span v-if="isLoading" class="loading-spinner"></span>
              {{ isLoading ? 'Please wait...' : submitLabel }}
            </button>
          </form>
          <button v-if="!isSignUp && !isForgotPassword && !isResetPassword" @click="setMode('forgot')" class="forgot-btn">
            Forgot password?
          </button>
          <p class="toggle-text">
            {{ isSignUp ? 'Already have an account?' : "Don't have an account?" }}
            <button @click="setMode(isSignUp ? 'sign-in' : 'sign-up')" class="toggle-btn">
              {{ isSignUp ? 'Sign In' : 'Sign Up' }}
            </button>
          </p>
          <p v-if="isForgotPassword || isResetPassword" class="toggle-text">
            Remembered your password?
            <button @click="setMode('sign-in')" class="toggle-btn">Sign In</button>
          </p>
        </div>

        <div v-if="success" class="success-msg">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18">
            <path d="M9 12l2 2 4-4"></path>
            <circle cx="12" cy="12" r="10"></circle>
          </svg>
          <span>{{ success }}</span>
        </div>

        <div v-if="error" class="error-msg">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18">
            <circle cx="12" cy="12" r="10"></circle>
            <line x1="15" y1="9" x2="9" y2="15"></line>
            <line x1="9" y1="9" x2="15" y2="15"></line>
          </svg>
          <span>{{ error }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
}

.login-background {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  z-index: 1;
}

.login-pattern {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-image: radial-gradient(rgba(255, 255, 255, 0.1) 1px, transparent 1px);
  background-size: 30px 30px;
}

.login-container {
  position: relative;
  z-index: 2;
  width: 100%;
  max-width: 440px;
  padding: 2rem;
}

.login-card {
  background: white;
  border-radius: 20px;
  padding: 2.5rem 2rem;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.2);
}

.login-header {
  text-align: center;
  margin-bottom: 2rem;
}

.brand {
  font-size: 2rem;
  font-weight: 800;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-bottom: 0.5rem;
}

.subtitle {
  color: #64748b;
  font-size: 0.95rem;
}

.form-group {
  margin-bottom: 1.25rem;
}

.form-group label {
  display: block;
  font-size: 0.875rem;
  font-weight: 600;
  color: #475569;
  margin-bottom: 0.5rem;
}

.auth-input {
  width: 100%;
  padding: 0.875rem 1rem;
  border: 2px solid #e2e8f0;
  border-radius: 10px;
  font-size: 1rem;
  transition: all 0.2s ease;
  outline: none;
  box-sizing: border-box;
}

.auth-input:focus {
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.submit-btn {
  width: 100%;
  padding: 0.875rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 10px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  margin-top: 0.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
}

.submit-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.submit-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.loading-spinner {
  width: 18px;
  height: 18px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.toggle-text {
  text-align: center;
  margin-top: 1.5rem;
  font-size: 0.9rem;
  color: #64748b;
}

.forgot-btn {
  display: block;
  margin: 1rem auto 0;
  background: none;
  border: none;
  color: #667eea;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  padding: 0.25rem;
}

.forgot-btn:hover {
  text-decoration: underline;
}

.toggle-btn {
  background: none;
  border: none;
  color: #667eea;
  font-weight: 600;
  cursor: pointer;
  padding: 0;
  margin-left: 0.25rem;
}

.toggle-btn:hover {
  text-decoration: underline;
}

.error-msg {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-top: 1.5rem;
  padding: 0.75rem;
  background: #fef2f2;
  border: 1px solid #fca5a5;
  color: #ef4444;
  border-radius: 8px;
  font-size: 0.9rem;
}

.success-msg {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-top: 1.5rem;
  padding: 0.75rem;
  background: #f0fdf4;
  border: 1px solid #86efac;
  color: #16a34a;
  border-radius: 8px;
  font-size: 0.9rem;
}

@media (max-width: 480px) {
  .login-container {
    padding: 1rem;
  }
  
  .login-card {
    padding: 2rem 1.5rem;
  }
}
</style>
