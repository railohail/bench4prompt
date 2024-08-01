import { ref } from 'vue'
import type { Ref } from 'vue'
import type { Question, EvaluationResult } from '@/utils/types'
import { config } from '@/config'

export function useEvaluation(
  selectedQuestion: Ref<Question | null>,
  updateLeaderboard: (newEntry: EvaluationResult, username: string, questionId: string) => void
) {
  const username = ref('')
  const studentAnswer = ref('')
  const evaluationResult = ref<EvaluationResult | null>(null)
  const error = ref<string | null>(null)
  const loading = ref(false)

  const submitAnswer = async () => {
    if (!selectedQuestion.value || !studentAnswer.value || !username.value) return

    error.value = null
    loading.value = true
    console.log('Loading state at submission start:', loading.value)
    try {
      console.log('Loading state before API call:', loading.value)
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
        updateLeaderboard(result, username.value, selectedQuestion.value.id)
      }
    } catch (e) {
      console.error('Error submitting answer:', e)
      error.value = 'Failed to submit answer. Please try again later.'
    } finally {
      loading.value = false
      console.log('Loading state at submission end:', loading.value)
    }
  }

  return { username, studentAnswer, evaluationResult, error, loading, submitAnswer }
}
