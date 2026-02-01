import hashlib
import re
import sys
import os
from pathlib import Path

# Add project root to path
root_path = Path(__file__).parent.parent
sys.path.append(str(root_path))

from database import SessionLocal, engine
import models

# Parse TASKS.md
def parse_tasks(content: str):
    tasks = []
    lines = content.split("\n")
    task_pattern = re.compile(r"^(\s*)-\s*\[([ xX])\]\s*(.+)$")
    
    for line in lines:
        match = task_pattern.match(line)
        if match:
            indent, status, text = match.groups()
            completed = status.lower() == "x"
            task_id = hashlib.md5(text.strip().encode()).hexdigest()[:8]
            
            # Look for priority/claims in text
            priority = "medium"
            if "priority: high" in text.lower(): priority = "high"
            elif "priority: low" in text.lower(): priority = "low"
            
            claimed_by = None
            claim_match = re.search(r"\(claimed: (agent:[\w-]+)", text)
            if claim_match:
                claimed_by = claim_match.group(1)

            tasks.append({
                "id": task_id,
                "text": text.strip(),
                "completed": completed,
                "priority": priority,
                "claimed_by": claimed_by
            })
    return tasks

def migrate():
    # Ensure tables exist
    models.Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    # 1. Seed Agents
    default_agents = [
        {"id": "agent:aragog", "sagacity": 0.8, "contributions": 10},
        {"id": "agent:anonymous", "sagacity": 0.1, "contributions": 0}
    ]
    for a_data in default_agents:
        if not db.query(models.Agent).filter(models.Agent.id == a_data["id"]).first():
            agent = models.Agent(**a_data)
            db.add(agent)
    
    # 2. Parse and Seed Tasks
    tasks_path = Path(__file__).parent.parent / "TASKS.md"
    if tasks_path.exists():
        content = tasks_path.read_text()
        parsed_tasks = parse_tasks(content)
        for t_data in parsed_tasks:
            if not db.query(models.Task).filter(models.Task.id == t_data["id"]).first():
                task = models.Task(**t_data)
                db.add(task)
    
    db.commit()
    print("Migration complete.")
    db.close()

if __name__ == "__main__":
    migrate()
