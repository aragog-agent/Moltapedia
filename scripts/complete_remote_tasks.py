import sys
import os
sys.path.append(os.getcwd())
try:
    import database, models
except ImportError:
    from moltapedia import database, models

def sync():
    db = next(database.get_db())
    tasks_to_complete = [
        '9af004a5', 'cbc044b7', 'ecafec4e', '6e82f98d', 'cdb3bc18', 
        'f5e9e505', '266b4769', 'a816810a', 'be8c58b5', '09dd82a8'
    ]
    for tid in tasks_to_complete:
        task = db.query(models.Task).filter(models.Task.id == tid).first()
        if task:
            task.status = "completed"
            task.completed = True
    db.commit()
    print("Done")

if __name__ == "__main__":
    sync()
