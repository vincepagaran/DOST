import { createRouter, createWebHistory } from 'vue-router'
import { supabase } from '@/utils/supabase'

import LoginView from '../views/LoginView.vue'
import DashboardView from '@/views/DashboardView.vue'
import UploadView from '@/views/UploadView.vue'
import RegistrationView from '@/views/RegistrationView.vue'

const routes = [
  {
    path: '/',
    name: 'login',
    component: LoginView,
    meta: { requiresGuest: true }, // 🚪 only for guests
  },
  {
    path: '/dashboard',
    name: 'dashboard',
    component: DashboardView,
    meta: { requiresAuth: true }, // 🔒 only for logged-in users
  },
  {
    path: '/upload',
    name: 'upload',
    component: UploadView,
    meta: { requiresAuth: true }, // 🔒 only for logged-in users
  },
  {
    path: '/register',
    name: 'register',
    component: RegistrationView,
    meta: { requiresGuest: true }, // 🚪 only for guests
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// ✅ Navigation Guard
router.beforeEach(async (to, from, next) => {
  const { data } = await supabase.auth.getUser()
  const isLoggedIn = !!data.user

  if (to.meta.requiresAuth && !isLoggedIn) {
    // ⛔ Not logged in → send to login
    next({ name: 'login' })
  } else if (to.meta.requiresGuest && isLoggedIn) {
    // 🔁 Already logged in → send to dashboard
    next({ name: 'dashboard' })
  } else {
    next()
  }
})

export default router
