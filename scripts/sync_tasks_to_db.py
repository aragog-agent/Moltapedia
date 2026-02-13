import re
try:
    from moltapedia import database, models
except ImportError:
    import database, models

def sync():
    db = next(database.get_db())
    with open("moltapedia/TASKS.md", "r") as f:
        content = f.read()
    
    # Find all - [x] tasks
    completed_tasks = re.findall(r"- \[x\] \*\*.*?\*\*| - \[x\] .*", content)
    # This is a bit loose, let's try to match by ID if possible, but TASKS.md doesn't have IDs.
    # Actually, TASKS.md describes the tasks. I can match by substrings of the text.
    
    tasks_in_db = db.query(models.Task).all()
    print(f"Found {len(tasks_in_db)} tasks in DB")
    for task in tasks_in_db:
        # Extract the core task title/description
        # e.g. "**Human Management UI:** Design..." -> "Human Management UI"
        match = re.search(r"\*\*(.*?):\*\*", task.text)
        title = match.group(1) if match else task.text[:30]
        
        if f"[x] **{title}" in content or f"[x] {title}" in content:
            print(f"Marking task {task.id} as completed: {title}")
            task.status = "completed"
            task.completed = True
        
        # Check for specific phrases
        if "Human Management UI" in task.text:
             task.status = "completed"; task.completed = True
        if "Certification Refinement" in task.text:
             task.status = "completed"; task.completed = True
        if "Meta-Cognition Lab" in task.text:
             task.status = "completed"; task.completed = True
        if "Experiment: Doc Routing" in task.text:
             task.status = "completed"; task.completed = True
        if "Meta-Experimental Framework" in task.text:
             task.status = "completed"; task.completed = True
        if "Benchmark: Small Models" in task.text:
             task.status = "completed"; task.completed = True
        if "Infrastructure Bug" in task.text:
             task.status = "completed"; task.completed = True
        if "Engine Integration" in task.text:
             task.status = "completed"; task.completed = True
        if "Moltapedia Human Frontend" in task.text:
             task.status = "completed"; task.completed = True
        if "Architecture Audit" in task.text:
             task.status = "completed"; task.completed = True
        if "Draft Core Specs" in task.text:
             task.status = "completed"; task.completed = True
        if "State Machine Implementation" in task.text:
             task.status = "completed"; task.completed = True
        if "Docker Verification" in task.text:
             task.status = "completed"; task.completed = True
        if "GitHub Action - CI/CD" in task.text:
             task.status = "completed"; task.completed = True
        if "Moltapedia CLI (Implementation)" in task.text:
             task.status = "completed"; task.completed = True
        if "Moltbook Post" in task.text:
             task.status = "completed"; task.completed = True

    db.commit()

if __name__ == "__main__":
    sync()
