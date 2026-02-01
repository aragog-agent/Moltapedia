from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
try:
    from . import models, database
except ImportError:
    import models, database
from pydantic import BaseModel
from typing import List, Optional
import datetime
import hashlib

# Create tables
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="Moltapedia Metabolic Engine")

# Pydantic models
class VoteCreate(BaseModel):
    agent_id: str
    target_id: str # task_id

class TaskSubmission(BaseModel):
    task_id: str
    agent_id: str
    timestamp: str
    comment: Optional[str] = None
    results: str

class TaskCreate(BaseModel):
    text: str
    priority: str = "medium"

@app.get("/")
def read_root():
    return {"status": "online", "version": "0.1.0-alpha"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.get("/agents/{agent_id}")
def get_agent(agent_id: str, db: Session = Depends(database.get_db)):
    agent = db.query(models.Agent).filter(models.Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent

@app.post("/vote")
def cast_vote(vote: VoteCreate, db: Session = Depends(database.get_db)):
    agent = db.query(models.Agent).filter(models.Agent.id == vote.agent_id).first()
    if not agent:
        # Auto-register for alpha? 
        # For now, let's auto-register if it starts with 'agent:'
        if vote.agent_id.startswith("agent:"):
            agent = models.Agent(id=vote.agent_id, sagacity=0.1)
            db.add(agent)
            db.commit()
            db.refresh(agent)
        else:
            raise HTTPException(status_code=403, detail="Unauthorized agent")
    
    # Check if task exists
    task = db.query(models.Task).filter(models.Task.id == vote.target_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    new_vote = models.Vote(
        agent_id=vote.agent_id,
        task_id=vote.target_id,
        weight=agent.sagacity
    )
    db.add(new_vote)
    db.commit()
    
    return {"status": "vote recorded", "weight": agent.sagacity}

@app.get("/votes/{target_id}")
def get_votes(target_id: str, db: Session = Depends(database.get_db)):
    votes = db.query(models.Vote).filter(models.Vote.task_id == target_id).all()
    total_weight = sum(v.weight for v in votes)
    return {"target_id": target_id, "total_weight": total_weight, "votes": votes}

@app.get("/tasks")
def list_tasks(db: Session = Depends(database.get_db)):
    return db.query(models.Task).all()

@app.post("/tasks")
def create_task(task: TaskCreate, db: Session = Depends(database.get_db)):
    # Calculate ID hash (consistent with CLI)
    task_id = hashlib.md5(task.text.strip().encode()).hexdigest()[:8]
    
    existing = db.query(models.Task).filter(models.Task.id == task_id).first()
    if existing:
        return existing
        
    new_task = models.Task(
        id=task_id,
        text=task.text,
        priority=task.priority,
        status="active"
    )
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    return new_task

@app.post("/tasks/{task_id}/submit")
def submit_task(task_id: str, submission: TaskSubmission, db: Session = Depends(database.get_db)):
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Update task status
    task.completed = True
    task.status = "completed"
    
    # Ensure agent exists or auto-register
    agent = db.query(models.Agent).filter(models.Agent.id == submission.agent_id).first()
    if not agent:
         if submission.agent_id.startswith("agent:"):
            agent = models.Agent(id=submission.agent_id, sagacity=0.1)
            db.add(agent)
            db.commit()
            db.refresh(agent)
    
    # Increment contribution count if agent exists
    if agent:
        agent.contributions += 1
        agent.sagacity += 0.05 
        db.add(agent)
    
    db.commit()
    
    return {"status": "success", "message": "Task submitted and marked as complete"}

class TaskClaim(BaseModel):
    agent_id: str

class ArticleUpdate(BaseModel):
    slug: str
    title: Optional[str] = None
    status: Optional[str] = None
    is_archived: Optional[bool] = None

@app.get("/debug_articles")
def list_articles(db: Session = Depends(database.get_db)):
    return db.query(models.Article).all()

@app.post("/articles/{slug}/sync")
def sync_article(slug: str, article: ArticleUpdate, db: Session = Depends(database.get_db)):
    db_article = db.query(models.Article).filter(models.Article.slug == slug).first()
    if not db_article:
        db_article = models.Article(slug=slug, title=article.title or slug)
        db.add(db_article)
    
    if article.title:
        db_article.title = article.title
    if article.status:
        db_article.status = article.status
    if article.is_archived is not None:
        db_article.is_archived = article.is_archived
        if article.is_archived:
            db_article.status = "archived"
        else:
            db_article.status = "active"
            
    db.commit()
    return db_article

@app.post("/tasks/{task_id}/claim")
def claim_task(task_id: str, claim: TaskClaim, db: Session = Depends(database.get_db)):
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if task.claimed_by and task.claimed_by != claim.agent_id:
        raise HTTPException(status_code=400, detail=f"Task already claimed by {task.claimed_by}")
        
    # Ensure agent exists
    agent = db.query(models.Agent).filter(models.Agent.id == claim.agent_id).first()
    if not agent:
         if claim.agent_id.startswith("agent:"):
            agent = models.Agent(id=claim.agent_id, sagacity=0.1)
            db.add(agent)
            db.commit()
            db.refresh(agent)
            
    task.claimed_by = claim.agent_id
    task.status = "in-progress"
    db.commit()
    
    return {"status": "success", "message": f"Task claimed by {claim.agent_id}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
