from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse,FileResponse
from contextlib import asynccontextmanager
import json
import logging
from .models import QuestionModel, AnswerInput, EvaluationResult, LeaderboardEntry
from .evaluation import evaluate_answer
from .calculate import main as calculate_main
from typing import List, Dict
from datetime import datetime
import os
import traceback
import json
from datetime import datetime
from pydantic import BaseModel
import asyncio
from sse_starlette.sse import EventSourceResponse


# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

questions: Dict[str, QuestionModel] = {}
leaderboard: Dict[str, Dict[str, List[LeaderboardEntry]]] = {}

LEADERBOARD_FILE = "leaderboard.json"
AVERAGE_SCORES_FILE = "average_scores.json"


clients = set()


async def send_update_notification():
    for client in clients:
        await client.put(json.dumps({"type": "update"}))


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
        
        # Determine if the new entry is the highest score
        if not user_entries or evaluation_result.score > max(entry.score for entry in user_entries):
            new_entry.is_highest = True
        
        # Reset flags for existing entries
        for entry in user_entries:
            entry.is_newest = False
            if new_entry.is_highest:
                entry.is_highest = False
        
        user_entries.append(new_entry)
        
        # Keep only the highest scoring entry and the newest entry
        highest_score_entry = max(user_entries, key=lambda x: x.score)
        newest_entry = new_entry  # The new entry is always the newest
        
        kept_entries = []
        if highest_score_entry != newest_entry:
            kept_entries = [highest_score_entry, newest_entry]
        else:
            kept_entries = [newest_entry]  # If the newest is also the highest, keep only one entry
        
        leaderboard[answer_input.question_id][answer_input.username] = kept_entries
        # Save the updated leaderboard
        save_leaderboard()
        # Calculate the average scores
        print('running calculation for average')
        calculate_main()
        # Send update notification to all connected clients
        await send_update_notification()
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
@app.get("/average-scores")
async def get_average_scores():
    try:
        with open(AVERAGE_SCORES_FILE, 'r', encoding='utf-8') as f:
            average_scores = json.load(f)
        logger.info("Average scores loaded successfully")
        return JSONResponse(content=average_scores)
    except FileNotFoundError:
        logger.error(f"Average scores file not found: {AVERAGE_SCORES_FILE}")
        raise HTTPException(status_code=404, detail="Average scores data not found")
    except json.JSONDecodeError:
        logger.error(f"Error decoding JSON from {AVERAGE_SCORES_FILE}")
        raise HTTPException(status_code=500, detail="Error reading average scores data")
    except Exception as e:
        logger.error(f"Error retrieving average scores: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error retrieving average scores: {str(e)}")
@app.get("/stream")
async def stream(request: Request):
    async def event_generator():
        client_queue = asyncio.Queue()
        clients.add(client_queue)
        try:
            while True:
                if await request.is_disconnected():
                    break
                yield {
                    "event": "message",
                    "data": await client_queue.get()
                }
        finally:
            clients.remove(client_queue)

    return EventSourceResponse(event_generator())

@app.get("/download-excel")
async def download_excel():
    file_path = "平均分數.xlsx"
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", filename="average_scores.xlsx")
    else:
        raise HTTPException(status_code=404, detail="File not found")
