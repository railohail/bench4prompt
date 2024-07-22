<template>
  <div>
    <h1 class="italic">Prompt Evaluation</h1>
    <ToggleSwitch v-model="darkOrNot" label="Toggle Color Scheme" @click="toggleColorScheme()" />
    <div v-if="error">
      {{ error }}
    </div>
    <div class="flex">
      <div class="flex-1 mr-4">
        <div class="card mb-3">
          <div class="card flex justify-center">
            <Drawer v-model:visible="visible" header="送出答案的詳細資訊">
              <div v-if="evaluationResult" class="card flex-1">
                <h2>Evaluation</h2>
                <div v-for="(value, key) in evaluationResult" :key="key" class="mb-2">
                  <strong>{{ key }}:</strong>
                  {{ typeof value === 'number' ? value.toFixed(2) : value }}
                </div>
              </div>
            </Drawer>
          </div>
          <Button outlined label="詳細" icon="pi pi-bars" @click="visible = true" />
          <Select
            v-model="selectedQuestion"
            :options="questions"
            optionLabel="prompt"
            placeholder="選擇回答的問題"
            class="w-full mb-3"
          />
          <InputText v-model="username" placeholder="名字" size="large" class="w-full mb-4" />

          <Button
            outlined
            icon="pi pi-check"
            label="送出答案"
            @click="submitAnswer"
            :disabled="!selectedQuestion || !studentAnswer || !username"
            :loading="loading"
          />
        </div>
        <div class="card w-full">
          <Textarea
            autoresize
            v-model="studentAnswer"
            cols="77"
            rows="10"
            class="w-full"
            placeholder="答案"
          />
        </div>
      </div>
    </div>
    <div class="card mt-3">
      <h2 class="text-red-600">Leaderboard</h2>
      <DataTable
        :value="sortedLeaderboard"
        :paginator="true"
        :rows="5"
        :filters="filters"
        @filter="onFilter"
      >
        <Column field="username" header="Username" :sortable="true"></Column>
        <Column field="score" header="Score" :sortable="true">
          <template #body="slotProps">
            <span>
              {{ slotProps.data.score.toFixed(2) }}
              <Tag v-if="slotProps.data.isHighest" value="Highest" severity="success"></Tag>
              <Tag v-if="slotProps.data.isNewest" value="Newest" severity="info"></Tag>
            </span>
          </template>
        </Column>
        <Column
          field="question_id"
          header="Question"
          :sortable="true"
          :filter="true"
          filterMatchMode="in"
        >
          <template #filter="{ filterModel }">
            <MultiSelect
              v-model="filterModel.value"
              :options="questionOptions"
              optionLabel="prompt"
              optionValue="id"
              placeholder="Select Questions"
              class="p-column-filter"
              :maxSelectedLabels="3"
            >
              <template #option="slotProps">
                <span>{{ slotProps.option.prompt }}</span>
              </template>
            </MultiSelect>
          </template>
          <template #body="slotProps">
            {{ getQuestionPrompt(slotProps.data.question_id) }}
          </template>
        </Column>
        <Column field="timestamp" header="Timestamp" :sortable="true">
          <template #body="slotProps">
            {{ new Date(slotProps.data.timestamp).toLocaleString() }}
          </template>
        </Column>
      </DataTable>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import 'primeicons/primeicons.css'
import Select from 'primevue/select'
import InputText from 'primevue/inputtext'
import Button from 'primevue/button'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Tag from 'primevue/tag'
import MultiSelect from 'primevue/multiselect'
import Textarea from 'primevue/textarea'
import Drawer from 'primevue/drawer'
import ToggleSwitch from 'primevue/toggleswitch'

const visible = ref(false)
const darkOrNot = ref(true)

interface Question {
  id: string
  prompt: string
}

interface EvaluationResult {
  score: number
  tfidf_similarity: number
  bleu_score: number
  rouge_l_score: number
  prompt_relevance_ratio: number
}

interface LeaderboardEntry {
  username: string
  score: number
  question_id: string
  timestamp: string
  isHighest: boolean
  isNewest: boolean
}

const questions = ref<Question[]>([])
const selectedQuestion = ref<Question | null>(null)
const username = ref('')
const studentAnswer = ref('')
const evaluationResult = ref<EvaluationResult | null>(null)
const error = ref<string | null>(null)
const loading = ref(false)
const leaderboard = ref<LeaderboardEntry[]>([])
const filters = ref({})

const isDarkMode = ref(true)
const toggleColorScheme = () => {
  isDarkMode.value = !isDarkMode.value
  const element = document.querySelector('html')
  if (element) {
    element.classList.toggle('my-app-dark', isDarkMode.value)
  }
}

const fetchQuestions = async () => {
  error.value = null
  loading.value = true
  try {
    const response = await fetch('http://localhost:8000/questions')
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }
    questions.value = await response.json()
  } catch (e) {
    console.error('Error fetching questions:', e)
    error.value = 'Failed to fetch questions. Please try again later.'
  } finally {
    loading.value = false
  }
}

const submitAnswer = async () => {
  if (!selectedQuestion.value || !studentAnswer.value || !username.value) return

  error.value = null
  loading.value = true
  try {
    const response = await fetch('http://localhost:8000/evaluate', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        question_id: selectedQuestion.value.id,
        student_answer: studentAnswer.value,
        username: username.value
      })
    })
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    const result = await response.json()
    evaluationResult.value = result
    if (result) {
      updateLeaderboard(result)
    }
  } catch (e) {
    console.error('Error submitting answer:', e)
    error.value = 'Failed to submit answer. Please try again later.'
  } finally {
    loading.value = false
  }
}

const updateLeaderboard = (newEntry: EvaluationResult) => {
  const existingEntryIndex = leaderboard.value.findIndex(
    (entry) => entry.username === username.value && entry.question_id === selectedQuestion.value!.id
  )

  if (existingEntryIndex !== -1) {
    // Update existing entry
    const existingEntry = leaderboard.value[existingEntryIndex]
    if (newEntry.score > existingEntry.score) {
      // New highest score
      existingEntry.score = newEntry.score
      existingEntry.timestamp = new Date().toISOString()
      existingEntry.isHighest = true
      existingEntry.isNewest = true
    } else {
      // New score is not the highest
      leaderboard.value.push({
        username: username.value,
        score: newEntry.score,
        question_id: selectedQuestion.value!.id,
        timestamp: new Date().toISOString(),
        isHighest: false,
        isNewest: true
      })
      existingEntry.isNewest = false
    }
  } else {
    // New entry
    leaderboard.value.push({
      username: username.value,
      score: newEntry.score,
      question_id: selectedQuestion.value!.id,
      timestamp: new Date().toISOString(),
      isHighest: true,
      isNewest: true
    })
  }

  // Ensure only two entries per user per question
  const userQuestionEntries = leaderboard.value.filter(
    (entry) => entry.username === username.value && entry.question_id === selectedQuestion.value!.id
  )
  if (userQuestionEntries.length > 2) {
    const sortedEntries = userQuestionEntries.sort((a, b) => b.score - a.score)
    const indexToRemove = leaderboard.value.findIndex((entry) => entry === sortedEntries[2])
    leaderboard.value.splice(indexToRemove, 1)
  }
}

const fetchLeaderboard = async () => {
  try {
    const response = await fetch('http://localhost:8000/leaderboard')
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }
    const fetchedLeaderboard = await response.json()
    leaderboard.value = processLeaderboard(fetchedLeaderboard)
  } catch (e) {
    console.error('Error fetching leaderboard:', e)
  }
}

const processLeaderboard = (fetchedLeaderboard: LeaderboardEntry[]) => {
  const processedLeaderboard: LeaderboardEntry[] = []
  const userQuestionMap = new Map<string, LeaderboardEntry[]>()

  for (const entry of fetchedLeaderboard) {
    const key = `${entry.username}-${entry.question_id}`
    if (!userQuestionMap.has(key)) {
      userQuestionMap.set(key, [])
    }
    userQuestionMap.get(key)!.push(entry)
  }

  for (const entries of userQuestionMap.values()) {
    entries.sort((a, b) => b.score - a.score)
    const highest = entries[0]
    highest.isHighest = true
    highest.isNewest = entries.length === 1
    processedLeaderboard.push(highest)

    if (entries.length > 1) {
      const newest = entries[1]
      newest.isHighest = false
      newest.isNewest = true
      processedLeaderboard.push(newest)
    }
  }

  return processedLeaderboard
}

const sortedLeaderboard = computed(() => {
  return [...leaderboard.value].sort((a, b) => b.score - a.score)
})

const questionOptions = computed(() => {
  return questions.value.map((q) => ({ id: q.id, prompt: q.prompt }))
})

const getQuestionPrompt = (questionId: string) => {
  const question = questions.value.find((q) => q.id === questionId)
  return question ? question.prompt : questionId
}

const onFilter = (event: any) => {
  filters.value = event.filters
}

onMounted(() => {
  fetchQuestions()
  fetchLeaderboard()
})
</script>
