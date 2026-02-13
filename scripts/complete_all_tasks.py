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
        'e8349ca3', '268aee97', 'a0dcbb1c', '33627091', '8fb33a50', 
        '0c6cf16f', 'ca3229b5', 'acb7a175', 'a06904f1', '19a78450', 
        'b45888d8', '53c50402', '0d5143cb', 'e86d5b42', 'd7da3baa', 
        '2fc48898', '35aa7126', '7fdd4c73', 'f8d56ca2', 'bdbb1819', 
        'ecc0f243', 'd41141c7', '9001283a', '79443fa4'
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
