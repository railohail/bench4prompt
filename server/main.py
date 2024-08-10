from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import json
import logging
from .models import QuestionModel, AnswerInput, EvaluationResult, LeaderboardEntry
from .evaluation import evaluate_answer
from typing import List, Dict
from datetime import datetime
import os
import traceback
import json
from datetime import datetime
from pydantic import BaseModel
# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

questions: Dict[str, QuestionModel] = {}
leaderboard: Dict[str, Dict[str, List[LeaderboardEntry]]] = {}

LEADERBOARD_FILE = "leaderboard.json"
class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, BaseModel):
            return obj.model_dump()
        return super().default(obj)
def save_leaderboard():
    try:
        with open(LEADERBOARD_FILE, "w") as f:
            json.dump(leaderboard, f, cls=DateTimeEncoder,indent=2)
        logger.info("Leaderboard saved successfully")
    except Exception as e:
        logger.error(f"Error saving leaderboard: {str(e)}")
        logger.error(traceback.format_exc())

def load_leaderboard():
    global leaderboard
    if os.path.exists(LEADERBOARD_FILE):
        try:
            with open(LEADERBOARD_FILE, "r") as f:
                data = json.load(f)
                leaderboard = {
                    question_id: {
                        username: [LeaderboardEntry(**{**entry, 'timestamp': datetime.fromisoformat(entry['timestamp'])}) for entry in entries]
                        for username, entries in user_entries.items()
                    }
                    for question_id, user_entries in data.items()
                }
            logger.info("Leaderboard loaded successfully")
        except Exception as e:
            logger.error(f"Error loading leaderboard: {str(e)}")
            logger.error(traceback.format_exc())

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load questions from JSON file
    try:
        with open("questions.json", "r") as f:
            questions_data = json.load(f)
        # Store questions in memory
        global questions
        questions = {
            key: QuestionModel(id=key, prompt=value["prompt"], chatgpt_answer=value["chatgpt_answer"])
            for key, value in questions_data.items()
        }
        logger.info("Questions loaded successfully")
    except Exception as e:
        logger.error(f"Error loading questions: {str(e)}")
    
    # Load leaderboard data
    load_leaderboard()
    yield
    # Save leaderboard data when shutting down
    save_leaderboard()

app = FastAPI(lifespan=lifespan)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Add your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/questions", response_model=List[Dict[str, str]])
async def get_questions():
    return [{"id": q.id, "prompt": q.prompt} for q in questions.values()]

@app.post("/evaluate", response_model=EvaluationResult)
async def evaluate_student_answer(answer_input: AnswerInput):
    logger.info(f"Received evaluation request for question {answer_input.question_id}")
    if answer_input.question_id not in questions:
        logger.warning(f"Question not found: {answer_input.question_id}")
        raise HTTPException(status_code=404, detail="Question not found")
    
    question = questions[answer_input.question_id]
    try:
        logger.debug(f"Evaluating answer: {answer_input.student_answer[:50]}...")
        result = evaluate_answer(question.prompt, question.chatgpt_answer, answer_input.student_answer)
        logger.debug(f"Evaluation result: {result}")
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
        user_entries.sort(key=lambda x: (-x.score, x.timestamp))
        leaderboard[answer_input.question_id][answer_input.username] = user_entries[:2]
        
        # Save the updated leaderboard
        save_leaderboard()
        
        logger.info(f"Evaluation completed successfully for user {answer_input.username}")
        return evaluation_result
    except Exception as e:
        logger.error(f"Error during evaluation: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error during evaluation: {str(e)}")

@app.get("/leaderboard", response_model=List[LeaderboardEntry])
async def get_leaderboard():
    all_entries = []
    for question_entries in leaderboard.values():
        for user_entries in question_entries.values():
            all_entries.extend(user_entries)
    
    sorted_entries = sorted(all_entries, key=lambda x: (-x.score, x.timestamp))
    return sorted_entries