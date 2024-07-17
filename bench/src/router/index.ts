import { createRouter, createWebHistory } from 'vue-router'
import submitView from '@/views/submitView.vue'
const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'submit',
      component: submitView
    }
  ]
})

export default router
