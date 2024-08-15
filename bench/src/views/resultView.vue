<template>
  <div class="leaderboard">
    <h2 class="text-2xl font-bold mb-4">Average Leaderboard</h2>
    <div class="mb-6">
      <Chart type="line" :data="chartData" :options="chartOptions" class="h-64" />
    </div>
    <DataTable
      :value="leaderboardArray"
      :paginator="true"
      :rows="10"
      :loading="loading"
      responsiveLayout="scroll"
      class="p-datatable-sm"
    >
      <Column field="username" header="Username" sortable></Column>
      <Column field="average_score" header="Average Score" sortable>
        <template #body="slotProps">
          {{ slotProps.data.average_score.toFixed(2) }}
        </template>
      </Column>
      <Column field="questions_attempted" header="Questions Attempted" sortable>
        <template #body="slotProps">
          {{ slotProps.data.questions_attempted }} / {{ slotProps.data.total_questions }}
        </template>
      </Column>
      <Column field="missed_questions" header="Missed Questions">
        <template #body="slotProps">
          {{
            slotProps.data.missed_questions ? slotProps.data.missed_questions.join(', ') : 'None'
          }}
        </template>
      </Column>
    </DataTable>

    <div v-if="error" class="text-center text-red-500 mt-4">
      <p>{{ error }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { config } from '@/config'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Chart from 'primevue/chart'

interface LeaderboardEntry {
  average_score: number
  questions_attempted: number
  total_questions: number
  missed_questions?: string[]
}

interface LeaderboardData {
  [username: string]: LeaderboardEntry
}

const leaderboard = ref<LeaderboardData>({})
const loading = ref(true)
const error = ref<string | null>(null)

const leaderboardArray = computed(() => {
  return Object.entries(leaderboard.value).map(([username, data]) => ({
    username,
    ...data
  }))
})

const chartData = computed(() => {
  const scores = leaderboardArray.value.map((entry) => entry.average_score)
  const buckets = Array(20).fill(0) // 20 buckets for scores 0-100

  scores.forEach((score) => {
    const bucketIndex = Math.min(Math.floor(score / 5), 19)
    buckets[bucketIndex]++
  })

  return {
    labels: buckets.map((_, index) => `${index * 5}-${(index + 1) * 5}`),
    datasets: [
      {
        label: 'Number of Users',
        data: buckets,
        fill: true,
        borderColor: '#4bc0c0',
        backgroundColor: 'rgba(75, 192, 192, 0.2)',
        tension: 0.4
      }
    ]
  }
})

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      display: false
    },
    title: {
      display: true,
      text: 'Distribution of Average Scores'
    }
  },
  scales: {
    y: {
      beginAtZero: true,
      title: {
        display: true,
        text: 'Number of Users'
      }
    },
    x: {
      title: {
        display: true,
        text: 'Score Range'
      }
    }
  }
}

const fetchData = async () => {
  try {
    loading.value = true
    const response = await fetch(`${config.apiUrl}/average-scores`)

    if (!response.ok) {
      throw new Error('Failed to fetch data')
    }

    const averageScoresData = await response.json()
    leaderboard.value = averageScoresData
    loading.value = false
  } catch (err) {
    error.value = 'Failed to fetch data. Please try again later.'
    loading.value = false
    console.error('Error fetching data:', err)
  }
}

let eventSource: EventSource | null = null

const setupEventSource = () => {
  eventSource = new EventSource(`${config.apiUrl}/stream`)
  eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data)
    if (data.type === 'update') {
      fetchData()
    }
  }
  eventSource.onerror = (err) => {
    console.error('EventSource failed:', err)
    error.value = 'Lost connection to the server. Please refresh the page.'
  }
}

onMounted(() => {
  fetchData()
  setupEventSource()
})

onUnmounted(() => {
  if (eventSource) {
    eventSource.close()
  }
})
</script>

<style scoped>
.leaderboard {
  max-width: 1000px;
  margin: 0 auto;
  padding: 20px;
}
</style>
