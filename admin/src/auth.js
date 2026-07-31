import { ref, readonly } from 'vue'
import { supabase } from './supabase'

const currentUser = ref(null)
const loading = ref(true)

// Listen for auth state changes
supabase.auth.onAuthStateChange((event, session) => {
  currentUser.value = session?.user ?? null
  loading.value = false
})

// Initialize - check current session
supabase.auth.getSession()
  .then(({ data: { session } }) => {
    currentUser.value = session?.user ?? null
  })
  .finally(() => {
    loading.value = false
  })

export const useAuth = () => {
  const signInWithEmail = async (email, password) => {
    const { error } = await supabase.auth.signInWithPassword({
      email,
      password
    })
    if (error) throw error
  }

  const signUpWithEmail = async (email, password, username) => {
    const { error } = await supabase.auth.signUp({
      email,
      password,
      options: {
        data: {
          username
        }
      }
    })
    if (error) throw error
  }

  const sendPasswordResetEmail = async (email, redirectTo) => {
    const { error } = await supabase.auth.resetPasswordForEmail(email, {
      redirectTo
    })
    if (error) throw error
  }

  const updatePassword = async (password) => {
    const { error } = await supabase.auth.updateUser({
      password
    })
    if (error) throw error
  }

  const signOut = async () => {
    const { error } = await supabase.auth.signOut()
    if (error) throw error
  }

  const getAccessToken = async () => {
    const { data: { session } } = await supabase.auth.getSession()
    return session?.access_token ?? null
  }

  return {
    currentUser: readonly(currentUser),
    loading: readonly(loading),
    signInWithEmail,
    signUpWithEmail,
    sendPasswordResetEmail,
    updatePassword,
    signOut,
    getAccessToken
  }
}
