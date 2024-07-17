from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import json
from .models import QuestionModel, AnswerInput, EvaluationResult, LeaderboardEntry
from .evaluation import evaluate_answer
from typing import List, Dict
from datetime import datetime

questions: Dict[str, QuestionModel] = {}
leaderboard: Dict[str, Dict[str, LeaderboardEntry]] = {}  # Changed to nested dict

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load questions from JSON file
    with open("questions.json", "r") as f:
        questions_data = json.load(f)
    # Store questions in memory
    global questions
    questions = {
        key: QuestionModel(id=key, prompt=value["prompt"], chatgpt_answer=value["chatgpt_answer"])
        for key, value in questions_data.items()
    }
    yield

app = FastAPI(lifespan=lifespan)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Add your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/questions", response_model=List[Dict[str, str]])
async def get_questions():
    return [{"id": q.id, "prompt": q.prompt} for q in questions.values()]

@app.post("/evaluate", response_model=EvaluationResult)
async def evaluate_student_answer(answer_input: AnswerInput):
    if answer_input.question_id not in questions:
        raise HTTPException(status_code=404, detail="Question not found")
    
    question = questions[answer_input.question_id]
    try:
        result = evaluate_answer(question.prompt, question.chatgpt_answer, answer_input.student_answer)
        evaluation_result = EvaluationResult(**result)
        
        # Update leaderboard
        if answer_input.question_id not in leaderboard:
            leaderboard[answer_input.question_id] = {}
        
        current_entry = leaderboard[answer_input.question_id].get(answer_input.username)
        
        if current_entry is None or evaluation_result.score > current_entry.score:
            leaderboard_entry = LeaderboardEntry(
                username=answer_input.username,
                score=evaluation_result.score,
                question_id=answer_input.question_id,
                timestamp=datetime.now()
            )
            leaderboard[answer_input.question_id][answer_input.username] = leaderboard_entry
        
        return evaluation_result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during evaluation: {str(e)}")

@app.get("/leaderboard", response_model=List[LeaderboardEntry])
async def get_leaderboard():
    # Flatten the nested dictionary and sort by score
    all_entries = [entry for question_entries in leaderboard.values() for entry in question_entries.values()]
    sorted_entries = sorted(all_entries, key=lambda x: x.score, reverse=True)
    return sorted_entries