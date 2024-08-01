export interface Question {
  id: string
  prompt: string
}

export interface EvaluationResult {
  score: number
  tfidf_similarity: number
  bleu_score: number
  rouge_l_score: number
  prompt_relevance_ratio: number
  gpt_score: number
}

export interface LeaderboardEntry {
  username: string
  score: number
  question_id: string
  timestamp: string
  isHighest: boolean
  isNewest: boolean
}
