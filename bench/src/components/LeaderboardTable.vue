<template>
  <div class="card mt-3">
    <h2 class="text-red-600">Leaderboard</h2>
    <DataTable
      :value="leaderboard"
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
</template>

<script setup lang="ts">
import { computed } from 'vue'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Tag from 'primevue/tag'
import MultiSelect from 'primevue/multiselect'
import type { LeaderboardEntry, Question } from '@/utils/types'

const props = defineProps<{
  leaderboard: LeaderboardEntry[]
  questions: Question[]
  filters: Record<string, any>
}>()

const emit = defineEmits<{
  (e: 'filter', value: any): void
}>()

const questionOptions = computed(() => {
  return props.questions.map((q) => ({
    id: q.id,
    prompt: cropText(q.prompt)
  }))
})

const cropText = (text: string, charLimit: number = 20): string => {
  if (text.length <= charLimit) {
    return text
  }
  return text.slice(0, charLimit) + '...'
}

const getQuestionPrompt = (questionId: string): string => {
  const question = props.questions.find((q) => q.id === questionId)
  return question ? question.prompt : questionId
}

const onFilter = (event: any) => {
  emit('filter', event)
}
</script>
