<template>
  <div>
    <h1 class="italic">Prompt Evaluation</h1>
    <ToggleSwitch v-model="darkOrNot" label="Toggle Color Scheme" @click="toggleColorScheme()" />
    <div v-if="error">
      {{ error }}
    </div>
    <div class="flex">
      <div class="flex-1 mr-4">
        <SubmissionForm
          :questions="questions"
          :selectedQuestion="selectedQuestion"
          :username="username"
          :studentAnswer="studentAnswer"
          :loading="loading"
          :evaluationResult="evaluationResult"
          @update:selectedQuestion="selectedQuestion = $event"
          @update:username="username = $event"
          @update:studentAnswer="studentAnswer = $event"
          @submit-answer="submitAnswer"
        />
      </div>
    </div>
    <LeaderboardTable
      :leaderboard="sortedLeaderboard"
      :questions="questions"
      :filters="filters"
      @filter="onFilter"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import ToggleSwitch from 'primevue/toggleswitch'
import SubmissionForm from '@/components/SubmissionForm.vue'
import LeaderboardTable from '@/components/LeaderboardTable.vue'
import { useQuestions } from '../composables/useQuestions'
import { useLeaderboard } from '../composables/useLeaderboard'
import { useEvaluation } from '../composables/useEvaluation'

const darkOrNot = ref(true)
const error = ref<string | null>(null)
const filters = ref({})

const { questions, fetchQuestions, selectedQuestion } = useQuestions()
const { leaderboard, fetchLeaderboard, sortedLeaderboard, updateLeaderboard } =
  useLeaderboard(questions)
const { username, studentAnswer, evaluationResult, submitAnswer, loading } = useEvaluation(
  selectedQuestion,
  updateLeaderboard
)

watch(loading, (newValue) => {
  console.log('testView: Loading state changed to:', newValue)
})

const toggleColorScheme = () => {
  darkOrNot.value = !darkOrNot.value
  const element = document.querySelector('html')
  if (element) {
    element.classList.toggle('my-app-dark', darkOrNot.value)
  }
}

const onFilter = (event: any) => {
  filters.value = event.filters
}

onMounted(() => {
  console.log('testView: Initial loading state:', loading.value)
  fetchQuestions()
  fetchLeaderboard()
})
</script>
