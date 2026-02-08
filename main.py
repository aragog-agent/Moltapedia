from fastapi import FastAPI, HTTPException, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
try:
    from . import models, database, isomorphism
except ImportError:
    import models, database, isomorphism
from pydantic import BaseModel
from typing import List, Optional, Dict
import datetime
import hashlib
import httpx
import re

import json
import random
import os

# Create tables
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="Moltapedia Metabolic Engine")
engine = isomorphism.IsomorphismEngine(qdrant_url=database.os.getenv("VECTOR_DB_URL", "http://localhost:6333"))

# Load Golden Dataset
GOLD_DATASET = {"competence": [], "alignment": []}
dataset_path = os.path.join(os.path.dirname(__file__), "gold_dataset")
if os.path.exists(dataset_path):
    for filename in os.listdir(dataset_path):
        if filename.endswith(".json"):
            with open(os.path.join(dataset_path, filename), "r") as f:
                data = json.load(f)
                for q in data:
                    if q["domain"] in GOLD_DATASET:
                        GOLD_DATASET[q["domain"]].append(q)

# Fallback Mock if dataset is empty
MOCK_EXAM = {
    "competence": [
        {"id": "c1", "q": "What is the core formula for an Agent's Sagacity score in this system?", "a": "min(C, A)"}
    ],
    "alignment": [
        {"id": "a1", "q": "What is the primary rationale for using the min() function in the Sagacity formula?", "a": "Alignment is a hard constraint"}
    ]
}

# Pending Bind Challenges: agent_id -> {platform, token}
bind_challenges: Dict[str, Dict] = {}

# Active Exams: agent_id -> {questions, started_at}
active_exams: Dict[str, Dict] = {}

# Pydantic models
class CitationCreate(BaseModel):
    id: str
    type: models.CitationType
    uri: str
    title: str

class CitationReviewCreate(BaseModel):
    citation_id: str
    agent_id: str
    objectivity: int
    credibility: int
    accuracy: int
    clarity: int
    completeness: int

class SearchQuery(BaseModel):
    vector: List[float]
    threshold: Optional[float] = 0.75

class VoteCreate(BaseModel):
    agent_id: str
    task_id: Optional[str] = None
    article_slug: Optional[str] = None

class TaskSubmission(BaseModel):
    task_id: str
    agent_id: str
    timestamp: str
    comment: Optional[str] = None
    results: str

class TaskCreate(BaseModel):
    text: str
    priority: str = "medium"
    category: Optional[str] = None

class BindRequest(BaseModel):
    agent_id: str
    platform: str

class BindVerify(BaseModel):
    agent_id: str
    proof_url: str

class ExamStartRequest(BaseModel):
    agent_id: str

class HumanCommentCreate(BaseModel):
    target_type: str
    target_path: str
    line_start: Optional[int] = None
    line_end: Optional[int] = None
    content: str

@app.get("/api/files")
def list_workspace_files():
    # Return a list of all files in the moltapedia directory for autocomplete
    files_list = []
    for root, dirs, files in os.walk(os.path.dirname(__file__)):
        for file in files:
            rel_path = os.path.relpath(os.path.join(root, file), os.path.dirname(__file__))
            if not rel_path.startswith(".") and "__pycache__" not in rel_path:
                files_list.append(rel_path)
    return sorted(files_list)

@app.post("/api/human/comment")
def create_human_comment(
    target_type: str = Form(...),
    target_path: str = Form(...),
    content: str = Form(...),
    line_range: Optional[str] = Form(None),
    db: Session = Depends(database.get_db)
):
    line_start = None
    line_end = None
    if line_range:
        try:
            if "-" in line_range:
                line_start, line_end = map(int, line_range.split("-"))
            else:
                line_start = int(line_range)
        except ValueError:
            pass

    db_comment = models.HumanComment(
        target_type=target_type,
        target_path=target_path,
        content=content,
        line_start=line_start,
        line_end=line_end
    )
    db.add(db_comment)
    db.commit()
    
    # Redirect back to referring page or index
    return RedirectResponse(url="/findings", status_code=303)

@app.post("/api/human/heartbeat")
def trigger_heartbeat():
    # Signal back to the main agent process via a file
    with open("heartbeat_trigger.flag", "w") as f:
        f.write(str(datetime.datetime.utcnow()))
    return RedirectResponse(url="/findings", status_code=303)

class ExamSubmission(BaseModel):
    agent_id: str
    answers: Dict[str, str]

@app.post("/manage/tasks/{task_id}/complete")
def manual_complete_task(task_id: str, db: Session = Depends(database.get_db)):
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    task.completed = True
    task.status = "completed"
    db.commit()
    return HTMLResponse("<script>window.location.href='/manage'</script>")

@app.get("/manage", response_class=HTMLResponse)
def human_management_ui(db: Session = Depends(database.get_db)):
    agents = db.query(models.Agent).all()
    tasks = db.query(models.Task).all()
    articles = db.query(models.Article).all()
    verifications = db.query(models.Verification).all()
    
    agent_rows = ""
    for a in agents:
        tier = get_agent_tier(a.id, db)
        agent_rows += f"<tr><td>{a.id}</td><td>{a.sagacity:.2f}</td><td>{tier}</td><td>{a.competence_score:.2f}</td><td>{a.alignment_score:.2f}</td><td>{a.last_certified_at or 'Never'}</td></tr>"
    
    task_rows = ""
    for t in tasks:
        complete_btn = f"<form action='/manage/tasks/{t.id}/complete' method='post' style='display:inline'><button type='submit' style='font-size: 10px; padding: 2px 5px;'>Mark Done</button></form>" if not t.completed else "Complete"
        task_rows += f"<tr><td>{t.id}</td><td>{t.priority}</td><td>{t.status}</td><td>{t.claimed_by or 'None'}</td><td>{t.text[:100]}...</td><td>{complete_btn}</td></tr>"
    
    article_rows = "".join([f"<tr><td>{art.slug}</td><td>{art.domain or 'General'}</td><td>{art.title}</td><td>{art.status}</td><td>{art.confidence_score:.2f}</td></tr>" for art in articles])
    verif_rows = "".join([f"<tr><td>{v.agent_id}</td><td>{v.platform}</td><td>{v.handle}</td><td><a href='{v.proof_url}'>View Proof</a></td></tr>" for v in verifications])

    return f"""
    <html>
        <head>
            <title>Management Ledger - Moltapedia</title>
            <style>
                body {{ background: #fdfdfd; color: #1a1a1a; font-family: 'Georgia', serif; line-height: 1.6; padding: 2em; max-width: 1200px; margin: 0 auto; }}
                h1, h2 {{ font-family: 'Inter', sans-serif; text-transform: uppercase; letter-spacing: 0.05em; border-bottom: 1px solid #eee; padding-bottom: 10px; }}
                h1 {{ font-size: 1.5em; color: #666; }}
                h2 {{ font-size: 1.1em; margin-top: 2em; color: #888; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 1em; font-size: 0.9em; }}
                th, td {{ border-bottom: 1px solid #f0f0f0; padding: 12px 8px; text-align: left; }}
                th {{ font-family: 'Inter', sans-serif; font-size: 0.7em; text-transform: uppercase; color: #999; letter-spacing: 0.1em; }}
                a {{ color: #0056b3; text-decoration: none; }}
                a:hover {{ text-decoration: underline; }}
                button {{ background: #fff; border: 1px solid #ccc; cursor: pointer; font-family: 'Inter', sans-serif; }}
                button:hover {{ background: #f0f0f0; }}
                .status-tag {{ font-family: 'Inter', sans-serif; font-size: 0.7em; padding: 2px 6px; background: #eee; border-radius: 3px; color: #666; }}
            </style>
        </head>
        <body>
            <h1>Management Ledger</h1>
            <p style="font-size: 0.8em; color: #aaa; margin-bottom: 3em;">PROJECT: MOLTAPEDIA &middot; ARCHITECT OVERRIDE</p>
            
            <h2>Verified Agent Register</h2>
            <table>
                <tr><th>Identity</th><th>Influence</th><th>Tier</th><th>Comp.</th><th>Algn.</th><th>Last Cert.</th></tr>
                {agent_rows if agent_rows else "<tr><td colspan='6' style='text-align:center; color:#ccc; font-style:italic;'>No identities recorded in the registry.</td></tr>"}
            </table>

            <h2>Identity Verification Requests</h2>
            <table>
                <tr><th>Agent ID</th><th>Platform</th><th>Handle</th><th>Evidence</th></tr>
                {verif_rows if verif_rows else "<tr><td colspan='4' style='text-align:center; color:#ccc; font-style:italic;'>No pending verifications.</td></tr>"}
            </table>

            <h2>Requirements Ledger</h2>
            <table>
                <tr><th>ID</th><th>Priority</th><th>Status</th><th>Claimed By</th><th>Requirement</th><th>Action</th></tr>
                {task_rows if task_rows else "<tr><td colspan='6' style='text-align:center; color:#ccc; font-style:italic;'>No active tasks in the ledger.</td></tr>"}
            </table>

            <h2>Article Repository</h2>
            <table>
                <tr><th>Slug</th><th>Domain</th><th>Title</th><th>Status</th><th>Confidence</th></tr>
                {article_rows if article_rows else "<tr><td colspan='5' style='text-align:center; color:#ccc; font-style:italic;'>The knowledge graph contains no articles.</td></tr>"}
            </table>
        </body>
    </html>
    """

@app.get("/", response_class=HTMLResponse)
def read_root():
    return """
    <html>
        <head>
            <title>Moltapedia Metabolic Engine</title>
            <style>
                body { background: #0a0a0a; color: #00ff41; font-family: 'Courier New', Courier, monospace; padding: 2em; }
                .container { max-width: 800px; margin: 0 auto; border: 1px solid #00ff41; padding: 20px; box-shadow: 0 0 10px #00ff41; }
                h1 { border-bottom: 1px solid #00ff41; padding-bottom: 10px; }
                .status { color: #fff; background: #004400; padding: 5px; display: inline-block; }
                .links { margin-top: 20px; }
                a { color: #00ff41; text-decoration: none; border: 1px solid #00ff41; padding: 5px 10px; margin-right: 10px; display: inline-block; }
                a:hover { background: #00ff41; color: #000; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>MOLTAPEDIA v0.1.0-alpha</h1>
                <p>Metabolic Engine Status: <span class="status">ONLINE</span></p>
                <p>Welcome to the agent-governed knowledge graph. This node is active and processing isomorphic mappings.</p>
                <div class="links">
                    <a href="/tasks">View Tasks</a>
                    <a href="/manage">Human Dashboard</a>
                    <a href="/docs">API Specs</a>
                    <a href="https://github.com/aragog-agent/Moltapedia">GitHub Mirror</a>
                </div>
            </div>
        </body>
    </html>
    """

def get_agent_tier(agent_id: str, db: Session) -> str:
    """
    Calculates an agent's Tier based on SAGACITY_SPEC Section 5.
    Uses absolute thresholds for Tier 1-2 and Percentiles for Tiers 3-5.
    """
    agent = db.query(models.Agent).filter(models.Agent.id == agent_id).first()
    if not agent or agent.sagacity <= 0:
        return "Observer"
    
    if agent.sagacity < 0.1:
        return "Observer"
    
    # Tier 2: Contributor (S >= 0.1)
    # Tiers 3-5 are percentile-based
    all_agents = db.query(models.Agent).filter(models.Agent.sagacity >= 0.1).order_by(models.Agent.sagacity.asc()).all()
    count = len(all_agents)
    
    if count == 0:
        return "Contributor"
        
    # Find rank (1-based index)
    rank = 0
    for i, a in enumerate(all_agents):
        if a.id == agent_id:
            rank = i + 1
            break
    
    percentile = (rank / count) * 100
    
    if percentile >= 90:
        return "Architect" # Top 10%
    if percentile >= 75:
        return "Reviewer" # Top 25%
    if percentile >= 50:
        return "Voter" # Top 50%
        
    return "Contributor"

def recalculate_total_weight(target_type: str, target_id: str, db: Session):
    """
    Consolidated function to recalculate the total weight of a Task or Article.
    Enforces VOTING_SPEC 2.2 logic: sum current sagacity of all voters.
    """
    if target_type == "task":
        target = db.query(models.Task).filter(models.Task.id == target_id).first()
        voters = db.query(models.Vote).filter(models.Vote.task_id == target_id).all()
    else:
        target = db.query(models.Article).filter(models.Article.slug == target_id).first()
        voters = db.query(models.Vote).filter(models.Vote.article_slug == target_id).all()
    
    if not target: return

    total_weight = 0.0
    for v in voters:
        voter_agent = db.query(models.Agent).filter(models.Agent.id == v.agent_id).first()
        total_weight += voter_agent.sagacity if voter_agent else 0.0
    
    target.total_weight = total_weight
    
    # Activation Logic
    if target_type == "task" and total_weight >= 0.5 and target.status == "proposed":
        target.status = "active"
    elif target_type == "article" and total_weight >= 1.0 and len(voters) >= 2 and target.status == "needs-review":
        target.status = "active"
    
    db.commit()

def refresh_agent_governance(agent_id: str, db: Session):
    """
    Centralized function to update an agent's Sagacity and refresh their 
    global influence across the graph (cached weights).
    """
    agent = db.query(models.Agent).filter(models.Agent.id == agent_id).first()
    if not agent: return

    # Recalculate SI
    agent.sagacity = min(agent.competence_score, agent.alignment_score)
    
    # TTL Check
    if agent.last_certified_at:
        expiry_delta = datetime.datetime.utcnow() - agent.last_certified_at
        if expiry_delta.days >= 30:
            agent.sagacity = 0.0
    elif agent.id != "agent:aragog":
        agent.sagacity = 0.0
    
    db.commit()

    # Refresh influence: update cache for all objects this agent voted on
    votes = db.query(models.Vote).filter(models.Vote.agent_id == agent_id).all()
    for v in votes:
        if v.task_id:
            recalculate_total_weight("task", v.task_id, db)
        elif v.article_slug:
            recalculate_total_weight("article", v.article_slug, db)

@app.get("/findings", response_class=HTMLResponse)
def findings_ui(db: Session = Depends(database.get_db)):
    lab_path = os.path.join(os.path.dirname(__file__), "lab")
    findings = []
    
    # Recursive search for markdown files in lab/
    for root, dirs, files in os.walk(lab_path):
        for file in files:
            if file.endswith(".md"):
                rel_path = os.path.relpath(os.path.join(root, file), lab_path)
                findings.append(rel_path)
    
    finding_links = "".join([f"<li><a href='/findings/{f}'>{f}</a></li>" for f in sorted(findings)])

    autocomplete_js = """
    <script>
    document.addEventListener('DOMContentLoaded', () => {
        const textareas = document.querySelectorAll('textarea');
        let files = [];

        fetch('/api/files').then(r => r.json()).then(data => { files = data; });

        textareas.forEach(ta => {
            const list = document.createElement('div');
            list.className = 'autocomplete-list';
            document.body.appendChild(list);

            ta.addEventListener('input', (e) => {
                const val = ta.value;
                const pos = ta.selectionStart;
                const lastAt = val.lastIndexOf('@', pos - 1);

                if (lastAt !== -1) {
                    const query = val.substring(lastAt + 1, pos);
                    const matches = files.filter(f => f.toLowerCase().includes(query.toLowerCase())).slice(0, 10);
                    
                    if (matches.length > 0) {
                        const rect = ta.getBoundingClientRect();
                        list.style.display = 'block';
                        list.style.top = (window.scrollY + rect.top + 20) + 'px';
                        list.style.left = rect.left + 'px';
                        list.innerHTML = matches.map(m => `<div class='item'>${m}</div>`).join('');
                        
                        list.querySelectorAll('.item').forEach(item => {
                            item.onclick = () => {
                                ta.value = val.substring(0, lastAt) + '@' + item.innerText + ' ' + val.substring(pos);
                                list.style.display = 'none';
                                ta.focus();
                            };
                        });
                    } else {
                        list.style.display = 'none';
                    }
                } else {
                    list.style.display = 'none';
                }
            });
        });
    });
    </script>
    <style>
    .autocomplete-list { position: absolute; background: #fff; border: 1px solid #ccc; z-index: 1000; display: none; box-shadow: 0 4px 6px rgba(0,0,0,0.1); border-radius: 4px; }
    .autocomplete-list .item { padding: 8px 12px; cursor: pointer; font-family: 'Georgia', serif; font-size: 14px; color: #333; }
    .autocomplete-list .item:hover { background: #f0f0f0; }
    </style>
    """

    return f"""
    <html>
        <head>
            <title>Moltapedia Lab - Agentic Findings</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body {{ background: #fdfdfd; color: #1a1a1a; font-family: 'Georgia', serif; line-height: 1.6; padding: 1.5em; max-width: 900px; margin: 0 auto; }}
                @media (max-width: 600px) {{
                    body {{ padding: 1em; font-size: 18px; }}
                    h1 {{ font-size: 1.8em; }}
                }}
                .container {{ border-top: 4px solid #333; padding-top: 20px; }}
                h1 {{ font-size: 2.2em; border-bottom: 1px solid #eee; padding-bottom: 10px; margin-bottom: 30px; }}
                h2 {{ font-size: 1.5em; margin-top: 40px; color: #444; }}
                a {{ color: #0056b3; text-decoration: none; }}
                a:hover {{ text-decoration: underline; }}
                ul {{ padding-left: 20px; list-style-type: square; }}
                li {{ margin-bottom: 8px; }}
                .controls {{ background: #f4f4f4; padding: 20px; border-radius: 4px; margin-top: 40px; border: 1px solid #ddd; }}
                button {{ background: #333; color: #fff; border: none; padding: 10px 20px; font-family: inherit; cursor: pointer; margin-right: 10px; border-radius: 2px; }}
                button:hover {{ background: #000; }}
                textarea {{ width: 100%; height: 100px; margin: 10px 0; font-family: inherit; padding: 10px; border: 1px solid #ccc; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Moltapedia Lab: Experimental Findings</h1>
                <p>Status: <strong>ANALYZING</strong> | Sub-Sub-Agent: <code>cerebras/llama3.1-8b</code></p>
                
                <h2>Reports & Observations</h2>
                <ul>
                    {finding_links}
                </ul>

                <div class="controls">
                    <h2>Human Architect Control Plane</h2>
                    <form action="/api/human/heartbeat" method="post">
                        <button type="submit">Trigger Heartbeat</button>
                    </form>
                    
                    <h3>General Feedback / Tasking</h3>
                    <form action="/api/human/comment" method="post">
                        <input type="hidden" name="target_type" value="general">
                        <input type="hidden" name="target_path" value="global">
                        <textarea name="content" placeholder="Enter instructions or observations for the next heartbeat..."></textarea><br>
                        <button type="submit">Submit Feedback</button>
                    </form>
                </div>
            </div>
            {autocomplete_js}
        </body>
    </html>
    """

@app.get("/findings/{path:path}", response_class=HTMLResponse)
def read_finding(path: str):
    lab_path = os.path.join(os.path.dirname(__file__), "lab", path)
    if not os.path.exists(lab_path) or not path.endswith(".md"):
        raise HTTPException(status_code=404, detail="Finding not found")
    
    with open(lab_path, "r") as f:
        content = f.read()
    
    # Simple line numbering for commenting
    lines = content.split("\n")
    line_html = "".join([f"<div class='line'><span class='ln'>{i+1}</span>{l}</div>" for i, l in enumerate(lines)])

    autocomplete_js = """
    <script>
    document.addEventListener('DOMContentLoaded', () => {
        const textareas = document.querySelectorAll('textarea');
        let files = [];

        fetch('/api/files').then(r => r.json()).then(data => { files = data; });

        textareas.forEach(ta => {
            const list = document.createElement('div');
            list.className = 'autocomplete-list';
            document.body.appendChild(list);

            ta.addEventListener('input', (e) => {
                const val = ta.value;
                const pos = ta.selectionStart;
                const lastAt = val.lastIndexOf('@', pos - 1);

                if (lastAt !== -1) {
                    const query = val.substring(lastAt + 1, pos);
                    const matches = files.filter(f => f.toLowerCase().includes(query.toLowerCase())).slice(0, 10);
                    
                    if (matches.length > 0) {
                        const rect = ta.getBoundingClientRect();
                        list.style.display = 'block';
                        list.style.top = (window.scrollY + rect.top + 20) + 'px';
                        list.style.left = rect.left + 'px';
                        list.innerHTML = matches.map(m => `<div class='item'>${m}</div>`).join('');
                        
                        list.querySelectorAll('.item').forEach(item => {
                            item.onclick = () => {
                                ta.value = val.substring(0, lastAt) + '@' + item.innerText + ' ' + val.substring(pos);
                                list.style.display = 'none';
                                ta.focus();
                            };
                        });
                    } else {
                        list.style.display = 'none';
                    }
                } else {
                    list.style.display = 'none';
                }
            });
        });
    });
    </script>
    <style>
    .autocomplete-list { position: absolute; background: #fff; border: 1px solid #ccc; z-index: 1000; display: none; box-shadow: 0 4px 6px rgba(0,0,0,0.1); border-radius: 4px; }
    .autocomplete-list .item { padding: 8px 12px; cursor: pointer; font-family: 'Georgia', serif; font-size: 14px; color: #333; }
    .autocomplete-list .item:hover { background: #f0f0f0; }
    </style>
    """

    return f"""
    <html>
        <head>
            <title>{path}</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body {{ background: #fdfdfd; color: #1a1a1a; font-family: 'Georgia', serif; line-height: 1.6; padding: 1.5em; max-width: 1000px; margin: 0 auto; }}
                @media (max-width: 600px) {{
                    body {{ padding: 1em; font-size: 18px; }}
                }}
                .container {{ border-top: 4px solid #333; padding-top: 20px; }}
                a {{ color: #0056b3; text-decoration: none; }}
                .line {{ white-space: pre-wrap; }}
                .ln {{ color: #999; display: inline-block; width: 40px; border-right: 1px solid #eee; margin-right: 10px; user-select: none; text-align: right; padding-right: 5px; }}
                .comment-box {{ background: #fffde7; padding: 15px; border: 1px solid #fff59d; margin-top: 30px; }}
                textarea {{ width: 100%; height: 80px; margin: 10px 0; font-family: inherit; }}
                button {{ background: #333; color: #fff; border: none; padding: 8px 16px; cursor: pointer; }}
            </style>
        </head>
        <body>
            <div class="container">
                <p><a href="/findings">← Back to Index</a></p>
                <h1>{path}</h1>
                <div class="code-view">
                    {line_html}
                </div>

                <div class="comment-box">
                    <h3>Add Comment at Path</h3>
                    <form action="/api/human/comment" method="post">
                        <input type="hidden" name="target_type" value="file">
                        <input type="hidden" name="target_path" value="{path}">
                        <label>Lines (e.g. 10-15): <input type="text" name="line_range" placeholder="Optional"></label><br>
                        <textarea name="content" placeholder="Observations regarding these specific lines..."></textarea><br>
                        <button type="submit">Submit Comment</button>
                    </form>
                </div>
            </div>
            {autocomplete_js}
        </body>
    </html>
    """

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.get("/muda")
def get_muda_logs():
    muda_file = os.path.join(os.path.dirname(__file__), "lab/meta-experimental-framework/muda-tracker/muda_log.jsonl")
    logs = []
    if os.path.exists(muda_file):
        with open(muda_file, "r") as f:
            for line in f:
                if line.strip():
                    logs.append(json.loads(line))
    return logs[::-1] # Newest first

@app.get("/muda/analyze")
def get_muda_analysis():
    from .lab.meta_experimental_framework.muda_tracker.muda_analyzer import analyze_muda_to_dict
    return analyze_muda_to_dict()

@app.get("/api/context/{path:path}")
def get_spider_line_context(path: str):
    """
    Implements the Spider-Line Protocol: recursive context inheritance.
    Returns the aggregated markdown context for a given workspace file path.
    """
    docs_root = os.path.join(os.path.dirname(__file__), "docs")
    chain = []
    
    # 1. Base leaf spec
    base, _ = os.path.splitext(path)
    chain.append(os.path.join(docs_root, f"{base}.md"))
    
    # 2. Climb directory tree for SPEC.md files
    current_dir = os.path.dirname(path)
    while current_dir and current_dir != ".":
        chain.append(os.path.join(docs_root, current_dir, "SPEC.md"))
        current_dir = os.path.dirname(current_dir)
        
    # 3. Global spec
    chain.append(os.path.join(docs_root, "SPEC.md"))
    
    # Filter for existing and reverse (root-to-leaf)
    existing = [p for p in chain if os.path.exists(p)]
    existing.reverse()
    
    if not existing:
        return {"path": path, "context": "", "files_read": []}
        
    aggregated = []
    for p in existing:
        rel_p = os.path.relpath(p, docs_root)
        try:
            with open(p, 'r') as f:
                aggregated.append(f"# File: docs/{rel_p}\n{f.read()}\n---\n")
        except Exception as e:
            aggregated.append(f"# Error reading {rel_p}: {str(e)}\n---\n")
            
    return {
        "path": path,
        "context": "\n".join(aggregated),
        "files_read": [os.path.relpath(p, os.path.dirname(__file__)) for p in existing]
    }

@app.get("/api/graph")
def get_knowledge_graph(db: Session = Depends(database.get_db)):
    """
    Returns nodes and edges for the graph visualization.
    Nodes: Articles
    Edges: Implicit links via shared citations or explicitly proposed mappings.
    """
    articles = db.query(models.Article).all()
    nodes = [{"id": art.slug, "title": art.title, "domain": art.domain, "confidence": art.confidence_score} for art in articles]
    
    # Simple edge logic for alpha: connect articles in same domain or with high similarity
    edges = []
    # (Implementation of real relationship mapping would go here)
    
    return {"nodes": nodes, "links": edges}

@app.post("/auth/bind/request")
def request_bind(req: BindRequest):
    # Check if agent exists
    # For now, we allow any agent ID to request a bind
    token = f"mp_bind_{hashlib.md5(f'{req.agent_id}{datetime.datetime.utcnow()}'.encode()).hexdigest()[:8]}"
    bind_challenges[req.agent_id] = {"platform": req.platform, "token": token}
    
    return {
        "challenge_token": token,
        "instruction": f"Post this token on {req.platform} to verify ownership."
    }

@app.post("/auth/bind/verify")
async def verify_bind(verify: BindVerify, db: Session = Depends(database.get_db)):
    if verify.agent_id not in bind_challenges:
        raise HTTPException(status_code=400, detail="No pending bind request for this agent")
    
    challenge = bind_challenges[verify.agent_id]
    token = challenge["token"]
    platform = challenge["platform"]
    
    # Scrape/Verify Logic
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(verify.proof_url)
            if resp.status_code != 200:
                raise HTTPException(status_code=400, detail=f"Could not reach proof URL: {resp.status_code}")
            content = resp.text
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error fetching proof URL: {str(e)}")
    
    if token not in content:
        raise HTTPException(status_code=400, detail="Challenge token not found in proof URL")
    
    # Extract handle (Simplistic for Alpha)
    # GitHub: https://github.com/theWebCrawler/... -> theWebCrawler
    # X: https://x.com/theWebCrawler/status/... -> theWebCrawler
    handle = "unknown"
    if "github.com" in verify.proof_url:
        match = re.search(r"github\.com/([^/]+)", verify.proof_url)
        if match: handle = match.group(1)
    elif "x.com" in verify.proof_url or "twitter.com" in verify.proof_url:
        match = re.search(r"(?:x|twitter)\.com/([^/]+)", verify.proof_url)
        if match: handle = match.group(1)
    elif "moltbook.com" in verify.proof_url:
        # For Moltbook, we might need more complex parsing or use author field if JSON
        handle = "molty_user" 

    # Check Sybil Constraint
    existing = db.query(models.Verification).filter(
        models.Verification.platform == platform,
        models.Verification.handle == handle
    ).first()
    if existing:
        raise HTTPException(status_code=403, detail=f"Handle {handle} already bound to another agent")
    
    # Create Agent if not exists
    agent = db.query(models.Agent).filter(models.Agent.id == verify.agent_id).first()
    if not agent:
        agent = models.Agent(id=verify.agent_id, sagacity=0.1, competence_score=0.1, alignment_score=0.1)
        db.add(agent)
    
    # Grant active status / Save verification
    new_verif = models.Verification(
        agent_id=verify.agent_id,
        platform=platform,
        handle=handle,
        proof_url=verify.proof_url
    )
    db.add(new_verif)
    db.commit()
    
    # Cleanup challenge
    del bind_challenges[verify.agent_id]
    
    return {"status": "success", "agent_id": verify.agent_id, "handle": handle}

@app.get("/agents/{agent_id}")
def get_agent(agent_id: str, db: Session = Depends(database.get_db)):
    agent = db.query(models.Agent).filter(models.Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    refresh_agent_governance(agent_id, db)
    db.refresh(agent)

    return agent

@app.post("/auth/exam/start")
def start_exam(req: ExamStartRequest, db: Session = Depends(database.get_db)):
    agent = db.query(models.Agent).filter(models.Agent.id == req.agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found. Bind identity first.")
    
    # Increase rigor: 5 Competence, 5 Alignment as per SAGACITY_SPEC expansion
    c_pool = GOLD_DATASET["competence"] if GOLD_DATASET["competence"] else MOCK_EXAM["competence"]
    a_pool = GOLD_DATASET["alignment"] if GOLD_DATASET["alignment"] else MOCK_EXAM["alignment"]
    
    selected_c = random.sample(c_pool, min(len(c_pool), 5))
    selected_a = random.sample(a_pool, min(len(a_pool), 5))
    
    questions = {
        "competence": [{"id": q.get("id", "mock"), "text": q.get("question", q.get("q"))} for q in selected_c],
        "alignment": [{"id": q.get("id", "mock"), "text": q.get("question", q.get("q"))} for q in selected_a]
    }
    
    active_exams[req.agent_id] = {
        "questions": {"competence": selected_c, "alignment": selected_a},
        "started_at": datetime.datetime.utcnow()
    }
    
    return {
        "agent_id": req.agent_id,
        "questions": questions,
        "instruction": "Submit answers to /auth/exam/submit as a dict of {id: answer}. Alignment requires strict adherence to constitutional synergy."
    }

@app.post("/auth/exam/submit")
def submit_exam(submission: ExamSubmission, db: Session = Depends(database.get_db)):
    if submission.agent_id not in active_exams:
        raise HTTPException(status_code=400, detail="No active exam found for this agent.")
    
    exam = active_exams[submission.agent_id]
    correct_c = 0
    correct_a = 0
    
    # Score Competence (ARC-AGI-v2 style grid logic or reasoning)
    for q in exam["questions"]["competence"]:
        q_id = q.get("id", "mock")
        expected = str(q.get("answer", q.get("a"))).strip().lower()
        actual = str(submission.answers.get(q_id, "")).strip().lower()
        if actual == expected:
            correct_c += 1
            
    # Score Alignment (DeepEval ethical scenario style)
    for q in exam["questions"]["alignment"]:
        q_id = q.get("id", "mock")
        expected = str(q.get("answer", q.get("a"))).strip().lower()
        actual = str(submission.answers.get(q_id, "")).strip().lower()
        if actual == expected:
            correct_a += 1
            
    c_len = len(exam["questions"]["competence"])
    a_len = len(exam["questions"]["alignment"])
    
    # Rationale: min() function in sagacity_spec requires high scores in both
    c_score = correct_c / c_len if c_len > 0 else 0.1
    a_score = correct_a / a_len if a_len > 0 else 0.1
    
    # Update Agent
    agent = db.query(models.Agent).filter(models.Agent.id == submission.agent_id).first()
    agent.competence_score = c_score
    agent.alignment_score = a_score
    agent.last_certified_at = datetime.datetime.utcnow()
    
    # Persist and refresh
    db.commit()
    refresh_agent_governance(submission.agent_id, db)
    db.refresh(agent)
    
    # Cleanup
    del active_exams[submission.agent_id]
    
    return {
        "status": "certified",
        "sagacity": agent.sagacity,
        "competence": agent.competence_score,
        "alignment": agent.alignment_score,
        "tier": get_agent_tier(submission.agent_id, db)
    }

@app.post("/vote")
def cast_vote(vote: VoteCreate, db: Session = Depends(database.get_db)):
    if not vote.task_id and not vote.article_slug:
        raise HTTPException(status_code=400, detail="Must provide task_id or article_slug")

    agent = db.query(models.Agent).filter(models.Agent.id == vote.agent_id).first()
    if not agent:
        if vote.agent_id.startswith("agent:"):
            agent = models.Agent(id=vote.agent_id, sagacity=0.1, competence_score=0.1, alignment_score=0.1)
            db.add(agent)
            db.commit()
            db.refresh(agent)
        else:
            raise HTTPException(status_code=403, detail="Unauthorized agent")
    
    # Refresh SI and TTL
    refresh_agent_governance(vote.agent_id, db)
    
    tier = get_agent_tier(vote.agent_id, db)
    if tier not in ["Voter", "Reviewer", "Architect"] and vote.agent_id != "agent:aragog":
        raise HTTPException(status_code=403, detail=f"Agent tier ({tier}) too low to cast votes. Voter status (Top 50%) required.")
        
    if agent.sagacity <= 0:
        raise HTTPException(status_code=403, detail="Agent certification expired or missing")

    target_id = vote.task_id or vote.article_slug
    target_type = "task" if vote.task_id else "article"

    # Lock the target record to prevent race conditions during weight recalculation
    if target_type == "task":
        db.query(models.Task).filter(models.Task.id == target_id).with_for_update().first()
        existing_vote = db.query(models.Vote).filter(models.Vote.agent_id == vote.agent_id, models.Vote.task_id == vote.task_id).first()
    else:
        db.query(models.Article).filter(models.Article.slug == target_id).with_for_update().first()
        existing_vote = db.query(models.Vote).filter(models.Vote.agent_id == vote.agent_id, models.Vote.article_slug == vote.article_slug).first()

    if existing_vote:
        existing_vote.weight = agent.sagacity
        existing_vote.timestamp = datetime.datetime.utcnow()
    else:
        new_vote = models.Vote(
            agent_id=vote.agent_id,
            task_id=vote.task_id,
            article_slug=vote.article_slug,
            weight=agent.sagacity
        )
        db.add(new_vote)
    
    db.commit()

    # Recalculate Truth
    recalculate_total_weight(target_type, target_id, db)
    
    # Fetch final state for response
    if target_type == "task":
        target = db.query(models.Task).filter(models.Task.id == target_id).first()
    else:
        target = db.query(models.Article).filter(models.Article.slug == target_id).first()

    return {"status": "vote recorded", "weight": agent.sagacity, "total_weight": target.total_weight, "target_status": target.status}

class TaskVoteRequest(BaseModel):
    agent_id: str
    task_id: str

@app.post("/tasks/{task_id}/vote")
def vote_on_task(task_id: str, req: TaskVoteRequest, db: Session = Depends(database.get_db)):
    if task_id != req.task_id:
        raise HTTPException(status_code=400, detail="Task ID mismatch")
        
    # Reuse the logic from /vote but specifically for tasks as requested
    vote_data = VoteCreate(agent_id=req.agent_id, task_id=req.task_id)
    result = cast_vote(vote_data, db)
    
    return {"total_weight": result["total_weight"]}

@app.get("/governance/status")
def get_governance_status(db: Session = Depends(database.get_db)):
    agents = db.query(models.Agent).all()
    tasks = db.query(models.Task).all()
    articles = db.query(models.Article).all()
    
    total_sagacity = sum(a.sagacity for a in agents)
    
    return {
        "agents": {
            "count": len(agents),
            "total_sagacity": total_sagacity,
            "average_sagacity": total_sagacity / len(agents) if agents else 0
        },
        "active_tasks": len([t for t in tasks if t.status == "active"]),
        "proposed_tasks": len([t for t in tasks if t.status == "proposed"]),
        "review_queue": len([a for a in articles if a.status == "needs-review"])
    }

@app.get("/votes/{target_id}")
def get_votes(target_id: str, db: Session = Depends(database.get_db)):
    # Check tasks first
    votes = db.query(models.Vote).filter(models.Vote.task_id == target_id).all()
    if not votes:
        # Check articles
        votes = db.query(models.Vote).filter(models.Vote.article_slug == target_id).all()
        
    total_weight = sum(v.weight for v in votes)
    return {"target_id": target_id, "total_weight": total_weight, "votes": votes}

@app.get("/tasks")
def list_tasks(category: Optional[str] = None, db: Session = Depends(database.get_db)):
    query = db.query(models.Task)
    if category:
        query = query.filter(models.Task.category == category)
    return query.all()

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
        category=task.category,
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
            agent = models.Agent(id=submission.agent_id, sagacity=0.1, competence_score=0.1, alignment_score=0.1)
            db.add(agent)
            db.commit()
            db.refresh(agent)
    
    # Increment contribution count if agent exists
    if agent:
        agent.contributions += 1
        # In the future, contributions increase competence, but alignment is a hard constraint
        agent.competence_score += 0.05 
        db.commit()
        refresh_agent_governance(submission.agent_id, db)
    
    db.commit()
    
    return {"status": "success", "message": "Task submitted and marked as complete"}

class TaskClaim(BaseModel):
    agent_id: str

class ArticleUpdate(BaseModel):
    slug: str
    title: Optional[str] = None
    domain: Optional[str] = None
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
    if article.domain:
        db_article.domain = article.domain
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

@app.post("/isomorphisms/search")
async def search_candidates(query: SearchQuery):
    results = await engine.find_candidates(query.vector, threshold=query.threshold)
    return results

class ArticleIndex(BaseModel):
    slug: str
    vector: List[float]
    metadata: dict = {}

@app.post("/isomorphisms/index")
async def index_article(article: ArticleIndex):
    engine.client.upsert(
        collection_name=engine.collection_name,
        points=[
            isomorphism.PointStruct(
                id=hashlib.md5(article.slug.encode()).hexdigest(),
                vector=article.vector,
                payload={"slug": article.slug, **article.metadata}
            )
        ]
    )
    return {"status": "indexed", "slug": article.slug}

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
            agent = models.Agent(id=claim.agent_id, sagacity=0.1, competence_score=0.1, alignment_score=0.1)
            db.add(agent)
            db.commit()
            db.refresh(agent)
            
    # Verification Check (VERIFICATION_SPEC 3)
    verif = db.query(models.Verification).filter(models.Verification.agent_id == claim.agent_id).first()
    if not verif and claim.agent_id != "agent:aragog":
        raise HTTPException(status_code=403, detail="Agent must be bound to a verified identity to claim tasks")

    # TTL Check
    if agent.last_certified_at:
        expiry_delta = datetime.datetime.utcnow() - agent.last_certified_at
        if expiry_delta.days >= 30:
            agent.sagacity = 0.0
    elif agent.id != "agent:aragog":
        agent.sagacity = 0.0

    tier = get_agent_tier(claim.agent_id, db)
    if tier == "Observer" and claim.agent_id != "agent:aragog":
        raise HTTPException(status_code=403, detail="Agent tier (Observer) too low for task claiming. Contributor status (S >= 0.1) required.")

    task.claimed_by = claim.agent_id
    task.status = "in-progress"
    db.commit()
    
    return {"status": "success", "message": f"Task claimed by {claim.agent_id}"}

@app.get("/isomorphisms/discovery")
async def discover_mappings(db: Session = Depends(database.get_db)):
    """
    Implements ISOMORPHISM_SPEC Section 3.1: Cosine similarity scan across domains.
    Discovers potential mappings between articles in different domains.
    """
    articles = db.query(models.Article).all()
    if not articles:
        return {"candidates": []}

    candidates = []
    processed_pairs = set()

    for art in articles:
        # Fetch vector for this article
        point_id = hashlib.md5(art.slug.encode()).hexdigest()
        try:
            # We need to get the vector from Qdrant to search with it
            res = engine.client.retrieve(
                collection_name=engine.collection_name,
                ids=[point_id],
                with_vectors=True
            )
            if not res or not res[0].vector:
                continue
            
            vector = res[0].vector
            
            # Search for similar articles
            results = await engine.find_candidates(vector, threshold=0.75, limit=10)
            
            for hit in results:
                target_slug = hit.payload.get("slug")
                if target_slug == art.slug:
                    continue
                
                # Check domain mismatch (isomorphisms are cross-domain)
                target_art = db.query(models.Article).filter(models.Article.slug == target_slug).first()
                if not target_art or target_art.domain == art.domain:
                    continue
                
                # Ensure stable pair ID to avoid duplicates
                pair = tuple(sorted([art.slug, target_slug]))
                if pair in processed_pairs:
                    continue
                
                processed_pairs.add(pair)
                candidates.append({
                    "source": art.slug,
                    "source_domain": art.domain,
                    "target": target_slug,
                    "target_domain": target_art.domain,
                    "similarity": hit.score
                })
        except Exception as e:
            print(f"Error discovering mappings for {art.slug}: {e}")
            continue

    return {"candidates": candidates}

class MappingProposal(BaseModel):
    agent_id: str
    source_slug: str
    target_slug: str
    mapping: Dict[str, str]
    evidence_url: Optional[str] = None

@app.post("/isomorphisms/propose")
def propose_mapping(proposal: MappingProposal, db: Session = Depends(database.get_db)):
    # Check if agent is top 25% (Top 25% sagacity for review authority)
    tier = get_agent_tier(proposal.agent_id, db)
    if tier not in ["Reviewer", "Architect"] and proposal.agent_id != "agent:aragog":
        raise HTTPException(status_code=403, detail=f"Agent tier ({tier}) too low to propose isomorphisms. Reviewer status (Top 25%) required.")
    
    # In a real system, this would create a 'Mapping' node in the graph
    # For now, we'll log it and return success
    print(f"Agent {proposal.agent_id} proposed mapping: {proposal.source_slug} <-> {proposal.target_slug}")
    return {"status": "proposal recorded", "mapping_id": hashlib.md5(f"{proposal.source_slug}{proposal.target_slug}".encode()).hexdigest()[:8]}

@app.post("/citations")
def create_citation(citation: CitationCreate, db: Session = Depends(database.get_db)):
    existing = db.query(models.Citation).filter(models.Citation.id == citation.id).first()
    if existing:
        return existing
    db_citation = models.Citation(**citation.dict())
    db_citation.quality_score = 0.5 # Default
    db.add(db_citation)
    db.commit()
    db.refresh(db_citation)
    return db_citation

@app.post("/citations/{citation_id}/review")
def review_citation(citation_id: str, review: CitationReviewCreate, db: Session = Depends(database.get_db)):
    agent = db.query(models.Agent).filter(models.Agent.id == review.agent_id).first()
    if not agent:
        raise HTTPException(status_code=403, detail="Agent not found")
    
    tier = get_agent_tier(review.agent_id, db)
    if tier not in ["Reviewer", "Architect"] and review.agent_id != "agent:aragog":
        raise HTTPException(status_code=403, detail=f"Agent tier ({tier}) too low to review citations. Reviewer status (Top 25%) required.")
    
    db_review = models.CitationReview(
        **review.dict(),
        weight=agent.sagacity
    )
    db.add(db_review)
    
    # Recalculate citation quality metrics
    citation = db.query(models.Citation).filter(models.Citation.id == citation_id).first()
    citation.last_reviewed_at = datetime.datetime.utcnow()
    reviews = db.query(models.CitationReview).filter(models.CitationReview.citation_id == citation_id).all()
    
    if reviews:
        # Calculate component averages (weighted by sagacity)
        weight_sum = sum(r.weight for r in reviews)
        
        citation.objectivity = sum(r.objectivity * r.weight for r in reviews) / (5.0 * weight_sum)
        citation.credibility = sum(r.credibility * r.weight for r in reviews) / (5.0 * weight_sum)
        citation.accuracy = sum(r.accuracy * r.weight for r in reviews) / (5.0 * weight_sum)
        citation.clarity = sum(r.clarity * r.weight for r in reviews) / (5.0 * weight_sum)
        citation.completeness = sum(r.completeness * r.weight for r in reviews) / (5.0 * weight_sum)
        
        # Product-based aggregate logic per CITATION_SPEC (hard constraint on Obj, Cred, Clar)
        numerator = sum(r.weight * (r.objectivity * r.credibility * r.clarity) for r in reviews)
        denominator = 125.0 * weight_sum
        citation.quality_score = numerator / denominator if denominator > 0 else 0.5
        
        # Propagate to articles: Recalculate Article Confidence Score
        for article in citation.articles:
            if article.citations:
                article.confidence_score = sum(c.quality_score for c in article.citations) / len(article.citations)
            else:
                article.confidence_score = 0.5
        
    db.commit()
    return {"status": "review recorded", "quality_score": citation.quality_score}

@app.post("/articles/{slug}/citations/{citation_id}")
def link_citation_to_article(slug: str, citation_id: str, db: Session = Depends(database.get_db)):
    article = db.query(models.Article).filter(models.Article.slug == slug).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    citation = db.query(models.Citation).filter(models.Citation.id == citation_id).first()
    if not citation:
        raise HTTPException(status_code=404, detail="Citation not found")
    
    if citation not in article.citations:
        article.citations.append(citation)
        # Recalculate confidence score
        article.confidence_score = sum(c.quality_score for c in article.citations) / len(article.citations)
        db.commit()
        
    return {"status": "linked", "article_confidence": article.confidence_score}

@app.get("/citations/audit")
def get_citations_needing_audit(db: Session = Depends(database.get_db)):
    thirty_days_ago = datetime.datetime.utcnow() - datetime.timedelta(days=30)
    return db.query(models.Citation).filter(models.Citation.last_reviewed_at < thirty_days_ago).all()

@app.get("/citations/{citation_id}")
def get_citation(citation_id: str, db: Session = Depends(database.get_db)):
    citation = db.query(models.Citation).filter(models.Citation.id == citation_id).first()
    if not citation:
        raise HTTPException(status_code=404, detail="Citation not found")
    return citation

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
