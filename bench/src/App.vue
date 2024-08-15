<script setup lang="ts">
import { RouterView, useRouter } from 'vue-router'
import { ref } from 'vue'
import Toolbar from 'primevue/toolbar'
import Button from 'primevue/button'
import ToggleSwitch from 'primevue/toggleswitch'

const router = useRouter()
const darkOrNot = ref(true)
const isDarkMode = ref(true)
const toggleColorScheme = () => {
  isDarkMode.value = !isDarkMode.value
  const element = document.querySelector('html')
  if (element) {
    element.classList.toggle('my-app-dark', isDarkMode.value)
  }
}
const goToSubmit = () => {
  router.push('/')
}
const goToResult = () => {
  router.push('/result')
}
</script>

<template>
  <Toolbar class="bg-gray-100 dark:bg-gray-800 rounded-full shadow-md mx-2 my-2 p-2 py-0">
    <template #start>
      <Button text plain label="Submit" icon="pi pi-file" class="mr-2" @click="goToSubmit" />
      <Button text plain label="Result" icon="pi pi-chart-bar" @click="goToResult" />
      <ToggleSwitch v-model="darkOrNot" label="Toggle Color Scheme" @click="toggleColorScheme()" />
    </template>
  </Toolbar>
  <RouterView />
</template>
