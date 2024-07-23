from pydantic import BaseModel
from typing import Dict,List 
from datetime import datetime

class QuestionModel(BaseModel):
    id: str
    prompt: str
    chatgpt_answer: str

class AnswerInput(BaseModel):
    question_id: str
    student_answer: str
    username: str

class EvaluationResult(BaseModel):
    score: float
    tfidf_similarity: float
    bleu_score: float
    rouge_l_score: float
    bertscore:float
    prompt_relevance_ratio: float
    chatgpt_score:float
    # bertscore:float
class LeaderboardEntry(BaseModel):
    username: str
    score: float
    question_id: str
    timestamp: datetime
    is_highest: bool
    is_newest: bool

questions: Dict[str, QuestionModel] = {}
leaderboard: List[LeaderboardEntry] = []