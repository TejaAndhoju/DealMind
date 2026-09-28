import os
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

from app.engine import analyze_chat_stream, save_novel_solution
from app.db import get_conn

app = FastAPI(title="DealMind Enterprise API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

app.mount("/static", StaticFiles(directory="static"), name="static")

class ChatRequest(BaseModel):
    query: str
    deal_id: str = None

class SaveSolutionRequest(BaseModel):
    deal_company: str
    solution_text: str

@app.get("/")
def read_root():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return StreamingResponse(iter([f.read()]), media_type="text/html")

@app.get("/api/deals")
def get_deals():
    conn = get_conn()
    deals = [dict(row) for row in conn.execute("SELECT * FROM deals").fetchall()]
    conn.close()
    return deals

@app.get("/api/memories")
async def get_memories():
    conn = get_conn()
    # Any deal with a stored successful strategy is part of the memory bank
    won_deals = [dict(row) for row in conn.execute("SELECT * FROM deals WHERE success_reason != ''").fetchall()]
    conn.close()
    
    return won_deals

@app.post("/api/chat")
async def chat_endpoint(req: ChatRequest):
    return StreamingResponse(analyze_chat_stream(req.query, req.deal_id), media_type="text/event-stream")

@app.post("/api/save_solution")
async def save_solution_endpoint(req: SaveSolutionRequest):
    result = await save_novel_solution(req.deal_company, req.solution_text)
    
    # Update the deal stage to Strategy Applied in the local DB
    conn = get_conn()
    conn.execute("UPDATE deals SET stage = 'Strategy Applied', success_reason = ? WHERE company = ?", 
                 (req.solution_text, req.deal_company))
    conn.commit()
    conn.close()
    
class UpdateOutcomeRequest(BaseModel):
    deal_company: str
    outcome: str # 'Closed Won' or 'Closed Lost'

@app.post("/api/update_outcome")
async def update_outcome_endpoint(req: UpdateOutcomeRequest):
    conn = get_conn()
    conn.execute("UPDATE deals SET stage = ? WHERE company = ?", (req.outcome, req.deal_company))
    conn.commit()
    conn.close()
    return {"status": "success"}
