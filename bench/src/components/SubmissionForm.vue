<template>
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
    <div class="flex items-center gap-2 mb-3">
      <Button outlined label="詳細" icon="pi pi-bars" @click="visible = true" />

      <Select
        v-model="selectedQuestionModel"
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
      <Button outlined @click="copySelectedQuestion" :disabled="!selectedQuestionModel">
        <span v-if="!copied">複製題目</span>
        <span v-else>Copied!</span>
      </Button>
    </div>
    <InputText
      v-model="usernameModel"
      placeholder="名字"
      size="large"
      class="w-full mb-4"
      @input="$emit('update:username', usernameModel)"
    />

    <Button
      outlined
      icon="pi pi-check"
      label="送出答案"
      @click="$emit('submit-answer')"
      :disabled="!isFormValid"
      :loading="loading"
    />
    <div class="card w-full">
      <Textarea
        autoresize
        v-model="studentAnswerModel"
        cols="77"
        rows="10"
        class="w-full"
        placeholder="答案"
        @input="$emit('update:studentAnswer', studentAnswerModel)"
      />
    </div>
  </div>
</template>
<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useClipboard } from '@vueuse/core'
import Select from 'primevue/select'
import InputText from 'primevue/inputtext'
import Button from 'primevue/button'
import Textarea from 'primevue/textarea'
import Drawer from 'primevue/drawer'
import type { Question, EvaluationResult } from '@/utils/types'

const props = defineProps<{
  questions: Question[]
  selectedQuestion: Question | null
  username: string
  studentAnswer: string
  loading: boolean
  evaluationResult: EvaluationResult | null
}>()

const emit = defineEmits<{
  (e: 'update:selectedQuestion', value: Question | null): void
  (e: 'update:username', value: string): void
  (e: 'update:studentAnswer', value: string): void
  (e: 'submit-answer'): void
}>()

const visible = ref(false)
const { copy, copied } = useClipboard()

const selectedQuestionModel = ref<Question | null>(props.selectedQuestion)
const usernameModel = ref(props.username)
const studentAnswerModel = ref(props.studentAnswer)

watch(selectedQuestionModel, (newValue) => {
  emit('update:selectedQuestion', newValue)
})
const loadingModel = ref(props.loading)

watch(
  () => props.loading,
  (newValue) => {
    console.log('SubmissionForm: Loading state changed to:', newValue)
    loadingModel.value = newValue
  }
)
watch(
  () => props.selectedQuestion,
  (newValue) => {
    selectedQuestionModel.value = newValue
  }
)

watch(usernameModel, (newValue) => {
  emit('update:username', newValue)
})

watch(
  () => props.username,
  (newValue) => {
    usernameModel.value = newValue
  }
)

watch(studentAnswerModel, (newValue) => {
  emit('update:studentAnswer', newValue)
})

watch(
  () => props.studentAnswer,
  (newValue) => {
    studentAnswerModel.value = newValue
  }
)

const isFormValid = computed(() => {
  return (
    selectedQuestionModel.value !== null &&
    usernameModel.value.trim() !== '' &&
    studentAnswerModel.value.trim() !== ''
  )
})

const cropText = (text: string, charLimit: number = 20): string => {
  if (text.length <= charLimit) {
    return text
  }
  return text.slice(0, charLimit) + '...'
}

const copySelectedQuestion = () => {
  if (selectedQuestionModel.value) {
    copy(selectedQuestionModel.value.prompt)
  }
}
</script>
