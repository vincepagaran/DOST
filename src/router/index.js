import { createRouter, createWebHistory } from 'vue-router'
import LoginView from '../views/LoginView.vue'
import DashboardView from '@/views/DashboardView.vue' // Scholar Dashboard
import UploadView from '@/views/UploadView.vue'
import RegistrationView from '@/views/RegistrationView.vue'
import AdminDashboardView from '@/views/AdminDashboardView.vue'
// import StaffDashboardView from '@/views/StaffDashboardView.vue'
import { supabase } from '@/utils/supabase'

const routes = [
  {
    path: '/',
    name: 'Login',
    component: LoginView,
    meta: { guestOnly: true }, // 🚫 Block if logged in
  },
  {
    path: '/register',
    name: 'register',
    component: RegistrationView,
    meta: { guestOnly: true }, // 🚫 Block if logged in
  },
  {
    path: '/dashboard',
    name: 'dashboard',
    component: DashboardView,
    meta: { requiresAuth: true, role: 'Scholar' },
  },
  {
    path: '/upload',
    name: 'upload',
    component: UploadView,
    meta: { requiresAuth: true, role: 'Scholar' },
  },
  {
    path: '/admin',
    name: 'admin',
    component: AdminDashboardView,
    meta: { requiresAuth: true, role: 'Admin' },
  },
  // {
  //   path: '/staff',
  //   name: 'staff',
  //   component: StaffDashboardView,
  //   meta: { requiresAuth: true, role: 'Staff' },
  // },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// 🔒 Route Guard
router.beforeEach(async (to, from, next) => {
  const { data } = await supabase.auth.getUser()
  const user = data?.user

  // 🚫 If route requires auth but no user → go to login
  if (to.meta.requiresAuth && !user) {
    return next({ name: 'Login' })
  }

  // 🚫 If guestOnly (login/register) but user is already logged in
  if (to.meta.guestOnly && user) {
    // ✅ Fetch role to redirect properly
    const { data: userData } = await supabase
      .from('users')
      .select('role')
      .eq('id', user.id)
      .single()

    const userRole = userData?.role
    if (userRole === 'Admin') return next({ name: 'admin' })
    if (userRole === 'Scholar') return next({ name: 'dashboard' })
    if (userRole === 'Staff') return next({ name: 'staff' })
  }

  if (user) {
    // ✅ Fetch role from users table
    const { data: userData, error } = await supabase
      .from('users')
      .select('role')
      .eq('id', user.id)
      .single()

    if (error) {
      console.error('Error fetching role:', error.message)
      return next({ name: 'Login' })
    }

    const userRole = userData?.role

    // 🚫 If route requires a specific role and doesn’t match → redirect
    if (to.meta.role && to.meta.role !== userRole) {
      if (userRole === 'Admin') return next({ name: 'admin' })
      if (userRole === 'Scholar') return next({ name: 'dashboard' })
      if (userRole === 'Staff') return next({ name: 'staff' })
    }
  }

  next()
})

export default router
