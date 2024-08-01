import { ref } from 'vue'
import type { Question } from '@/utils/types'
import { config } from '@/config'

export function useQuestions() {
  const questions = ref<Question[]>([])
  const selectedQuestion = ref<Question | null>(null)
  const error = ref<string | null>(null)

  const fetchQuestions = async () => {
    error.value = null
    try {
      const response = await fetch(`${config.apiUrl}/questions`)
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      questions.value = await response.json()
    } catch (e) {
      console.error('Error fetching questions:', e)
      error.value = 'Failed to fetch questions. Please try again later.'
    }
  }

  return { questions, selectedQuestion, error, fetchQuestions }
}
