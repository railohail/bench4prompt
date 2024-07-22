from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import json
from .models import QuestionModel, AnswerInput, EvaluationResult, LeaderboardEntry
from .evaluation import evaluate_answer
from typing import List, Dict
from datetime import datetime

questions: Dict[str, QuestionModel] = {}
leaderboard: Dict[str, Dict[str, List[LeaderboardEntry]]] = {}  # Changed to store a list of entries

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
        
        if answer_input.username not in leaderboard[answer_input.question_id]:
            leaderboard[answer_input.question_id][answer_input.username] = []
        
        user_entries = leaderboard[answer_input.question_id][answer_input.username]
        
        new_entry = LeaderboardEntry(
            username=answer_input.username,
            score=evaluation_result.score,
            question_id=answer_input.question_id,
            timestamp=datetime.now(),
            is_highest=False,
            is_newest=True
        )
        
        # Update highest and newest flags
        if not user_entries or evaluation_result.score > max(entry.score for entry in user_entries):
            new_entry.is_highest = True
            for entry in user_entries:
                entry.is_highest = False
                entry.is_newest = False
        else:
            for entry in user_entries:
                entry.is_newest = False
        
        user_entries.append(new_entry)
        
        # Keep only the top 2 entries
        user_entries.sort(key=lambda x: (-x.score, x.timestamp), reverse=True)
        leaderboard[answer_input.question_id][answer_input.username] = user_entries[:2]
        
        return evaluation_result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during evaluation: {str(e)}")

@app.get("/leaderboard", response_model=List[LeaderboardEntry])
async def get_leaderboard():
    all_entries = []
    for question_entries in leaderboard.values():
        for user_entries in question_entries.values():
            all_entries.extend(user_entries)
    
    sorted_entries = sorted(all_entries, key=lambda x: (-x.score, x.timestamp))
    return sorted_entries

