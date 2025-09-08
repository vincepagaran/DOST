import { createRouter, createWebHistory } from 'vue-router'
import LoginView from '../views/LoginView.vue'
import DashboardView from '@/views/DashboardView.vue'
import UploadView from '@/views/UploadView.vue'
import RegistrationView from '@/views/RegistrationView.vue'

const routes = [
  {
    path: '/',
    name: 'Login',
    component: LoginView,
  },
  {
    path: '/dashboard',
    name: 'dashboard',
    component: DashboardView,
  },
  {
    path: '/upload',
    name: 'upload',
    component: UploadView,
  },
  {
    path: '/register',
    name: 'register',
    component: RegistrationView,
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
