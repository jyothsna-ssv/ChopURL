import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import Links from '../views/Links.vue'
import Login from '../views/Login.vue'
import { supabase } from '../supabase'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home
  },
  {
    path: '/links',
    name: 'Links',
    component: Links,
    meta: { requiresAuth: true }
  },
  {
    path: '/login',
    name: 'Login',
    component: Login,
    meta: { guestOnly: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach(async (to, from, next) => {
  const { data: { session }, error } = await supabase.auth.getSession()
  const activeSession = error ? null : session
  
  if (to.meta.requiresAuth && !activeSession) {
    next({ name: 'Login', query: { redirect: to.fullPath } })
  } else if (to.meta.guestOnly && activeSession && to.query.mode !== 'reset') {
    next({ name: 'Home' })
  } else {
    next()
  }
})

export default router
