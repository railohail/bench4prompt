import { ref, computed } from 'vue'
import type { Ref } from 'vue'
import type { LeaderboardEntry, Question, EvaluationResult } from '@/utils/types'
import { config } from '@/config'

export function useLeaderboard(questions: Ref<Question[]>) {
  const leaderboard = ref<LeaderboardEntry[]>([])
  const error = ref<string | null>(null)

  const fetchLeaderboard = async () => {
    error.value = null
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

  const updateLeaderboard = (newEntry: EvaluationResult, username: string, questionId: string) => {
    const userQuestionEntries = leaderboard.value.filter(
      (entry) => entry.username === username && entry.question_id === questionId
    )

    if (userQuestionEntries.length === 0) {
      leaderboard.value.push({
        username,
        score: newEntry.score,
        question_id: questionId,
        timestamp: new Date().toISOString(),
        isHighest: true,
        isNewest: true
      })
    } else if (userQuestionEntries.length === 1) {
      const existingEntry = userQuestionEntries[0]
      if (newEntry.score > existingEntry.score) {
        existingEntry.score = newEntry.score
        existingEntry.timestamp = new Date().toISOString()
        existingEntry.isHighest = true
        existingEntry.isNewest = true
      } else {
        leaderboard.value.push({
          username,
          score: newEntry.score,
          question_id: questionId,
          timestamp: new Date().toISOString(),
          isHighest: false,
          isNewest: true
        })
        existingEntry.isNewest = false
      }
    } else {
      userQuestionEntries.sort((a, b) => b.score - a.score)
      const [highest, newest] = userQuestionEntries

      if (newEntry.score > highest.score) {
        newest.isNewest = false
        highest.isNewest = true
        highest.isHighest = false
        leaderboard.value.push({
          username,
          score: newEntry.score,
          question_id: questionId,
          timestamp: new Date().toISOString(),
          isHighest: true,
          isNewest: true
        })
      } else {
        newest.score = newEntry.score
        newest.timestamp = new Date().toISOString()
        newest.isNewest = true
        highest.isNewest = false
      }
    }

    const updatedUserQuestionEntries = leaderboard.value.filter(
      (entry) => entry.username === username && entry.question_id === questionId
    )
    if (updatedUserQuestionEntries.length > 2) {
      const sortedEntries = updatedUserQuestionEntries.sort((a, b) => b.score - a.score)
      const indexToRemove = leaderboard.value.findIndex((entry) => entry === sortedEntries[2])
      leaderboard.value.splice(indexToRemove, 1)
    }
  }

  const sortedLeaderboard = computed(() => {
    return [...leaderboard.value].sort((a, b) => b.score - a.score)
  })

  return { leaderboard, error, fetchLeaderboard, sortedLeaderboard, updateLeaderboard }
}
