<template>
  <div>
    <div v-if="error">
      {{ error }}
    </div>
    <div class="flex mx-2 my-2 p-2 py-0">
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
          <div>
            <div class="flex items-center mb-3">
              <Button
                outlined
                label="詳細"
                icon="pi pi-bars"
                @click="visible = true"
                class="mr-2"
              />
              <Button
                outlined
                @click="copySelectedQuestion"
                :disabled="!selectedQuestion"
                class="mr-2"
              >
                <span v-if="!copied">複製題目</span>
                <span v-else>Copied!</span>
              </Button>
              <InputText v-model="username" placeholder="名字" class="p-inputtext-sm w-56" />
            </div>

            <Select
              v-model="selectedQuestion"
              :options="questions"
              optionLabel="prompt"
              placeholder="選擇回答的問題"
              class="w-full mb-3"
            >
              <template #value="slotProps">
                <div class="question-option">
                  {{ slotProps.value ? cropText(slotProps.value.prompt) : '選擇回答的問題' }}
                </div>
              </template>
              <template #option="slotProps">
                <div class="question-option">
                  {{ cropText(slotProps.option.prompt) }}
                </div>
              </template>
            </Select>
          </div>

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
    <div class="card mt-3 mx-1 my-2 p-2 py-0">
      <h1 class="text-3xl font-bold">Leaderboard</h1>
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
                <span>{{ cropText(slotProps.option.prompt) }}</span>
              </template>
            </MultiSelect>
          </template>
          <template #body="slotProps">
            {{ cropText(getQuestionPrompt(slotProps.data.question_id)) }}
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
import { ref, computed, onMounted, onUnmounted } from 'vue'
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
import { useClipboard } from '@vueuse/core'
import { config } from '@/config'

const { copy, copied } = useClipboard()
const copySelectedQuestion = () => {
  if (selectedQuestion.value) {
    copy(selectedQuestion.value.prompt)
  }
}
const visible = ref(false)
// const darkOrNot = ref(true)

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
  gpt_score: number
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

let eventSource: EventSource | null = null

const setupEventSource = () => {
  eventSource = new EventSource(`${config.apiUrl}/stream`)
  eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data)
    if (data.type === 'update') {
      fetchLeaderboard()
    }
  }
  eventSource.onerror = (err) => {
    console.error('EventSource failed:', err)
    error.value = 'Lost connection to the server. Please refresh the page.'
  }
}

const cropText = (text: string, charLimit: number = 20): string => {
  if (text.length <= charLimit) {
    return text
  }
  return text.slice(0, charLimit) + '...'
}

const fetchQuestions = async () => {
  error.value = null
  loading.value = true
  try {
    const response = await fetch(`${config.apiUrl}/questions`)
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
    const response = await fetch(`${config.apiUrl}/evaluate`, {
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
  const userQuestionEntries = leaderboard.value.filter(
    (entry) => entry.username === username.value && entry.question_id === selectedQuestion.value!.id
  )

  if (userQuestionEntries.length === 0) {
    // New entry for this user and question
    leaderboard.value.push({
      username: username.value,
      score: newEntry.score,
      question_id: selectedQuestion.value!.id,
      timestamp: new Date().toISOString(),
      isHighest: true,
      isNewest: true
    })
  } else if (userQuestionEntries.length === 1) {
    // One existing entry
    const existingEntry = userQuestionEntries[0]
    if (newEntry.score > existingEntry.score) {
      // New highest score
      existingEntry.score = newEntry.score
      existingEntry.timestamp = new Date().toISOString()
      existingEntry.isHighest = true
      existingEntry.isNewest = true
    } else {
      // New score is not the highest, add as newest
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
    // Two existing entries
    userQuestionEntries.sort((a, b) => b.score - a.score)
    const [highest, newest] = userQuestionEntries

    if (newEntry.score > highest.score) {
      // New highest score
      newest.isNewest = false
      highest.isNewest = true
      highest.isHighest = false
      leaderboard.value.push({
        username: username.value,
        score: newEntry.score,
        question_id: selectedQuestion.value!.id,
        timestamp: new Date().toISOString(),
        isHighest: true,
        isNewest: true
      })
    } else {
      // Update newest entry
      newest.score = newEntry.score
      newest.timestamp = new Date().toISOString()
      newest.isNewest = true
      highest.isNewest = false
    }
  }

  // Ensure only two entries per user per question
  const updatedUserQuestionEntries = leaderboard.value.filter(
    (entry) => entry.username === username.value && entry.question_id === selectedQuestion.value!.id
  )
  if (updatedUserQuestionEntries.length > 2) {
    const sortedEntries = updatedUserQuestionEntries.sort((a, b) => b.score - a.score)
    const indexToRemove = leaderboard.value.findIndex((entry) => entry === sortedEntries[2])
    leaderboard.value.splice(indexToRemove, 1)
  }
}

const fetchLeaderboard = async () => {
  try {
    const response = await fetch(`${config.apiUrl}/leaderboard`)
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }
    const fetchedLeaderboard = await response.json()
    leaderboard.value = processLeaderboard(fetchedLeaderboard)
  } catch (e) {
    console.error('Error fetching leaderboard:', e)
    error.value = 'Failed to fetch leaderboard. Please try again later.'
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
  return questions.value.map((q) => ({
    id: q.id,
    prompt: cropText(q.prompt) // Apply cropping here
  }))
})

const getQuestionPrompt = (questionId: string): string => {
  const question = questions.value.find((q) => q.id === questionId)
  return question ? question.prompt : questionId
}

const onFilter = (event: any) => {
  filters.value = event.filters
}

onMounted(() => {
  fetchQuestions()
  fetchLeaderboard()
  setupEventSource()
})

onUnmounted(() => {
  if (eventSource) {
    eventSource.close()
  }
})
</script>
