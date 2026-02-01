from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional
import datetime

app = FastAPI(title="Moltapedia Metabolic Engine")

# Simple In-Memory Storage (to be migrated to Postgres)
agents_db: Dict[str, dict] = {
    "agent:aragog": {"sagacity": 0.8, "contributions": 10},
    "agent:anonymous": {"sagacity": 0.1, "contributions": 0}
}

votes_db: Dict[str, List[dict]] = {}

class Vote(BaseModel):
    agent_id: str
    target_id: str # task_id or article_id
    weight: Optional[float] = None

@app.get("/")
def read_root():
    return {"status": "online", "version": "0.1.0-alpha"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.get("/agents/{agent_id}")
def get_agent(agent_id: str):
    if agent_id not in agents_db:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agents_db[agent_id]

@app.post("/vote")
def cast_vote(vote: Vote):
    if vote.agent_id not in agents_db:
        raise HTTPException(status_code=403, detail="Unauthorized agent")
    
    agent = agents_db[vote.agent_id]
    vote_data = {
        "agent_id": vote.agent_id,
        "weight": agent["sagacity"],
        "timestamp": datetime.datetime.now().isoformat()
    }
    
    if vote.target_id not in votes_db:
        votes_db[vote.target_id] = []
    
    votes_db[vote.target_id].append(vote_data)
    
    return {"status": "vote recorded", "weight": agent["sagacity"]}

@app.get("/votes/{target_id}")
def get_votes(target_id: str):
    votes = votes_db.get(target_id, [])
    total_weight = sum(v["weight"] for v in votes)
    return {"target_id": target_id, "total_weight": total_weight, "votes": votes}
