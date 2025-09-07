import { createRouter, createWebHistory } from 'vue-router'
import LoginView from '../views/LoginView.vue'
import DashboardView from '@/views/DashboardView.vue'
import UploadView from '@/views/UploadView.vue'

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
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
