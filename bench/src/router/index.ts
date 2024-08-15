import { createRouter, createWebHistory } from 'vue-router'
import submitView from '@/views/submitView.vue'
import resultView from '@/views/resultView.vue'
const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'submit',
      component: submitView
    },
    {
      path: '/result',
      name: 'result',
      component: resultView
    }
  ]
})

export default router
