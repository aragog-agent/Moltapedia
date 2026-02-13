from sqlalchemy import text
try:
    from moltapedia import database
except ImportError:
    import database

def migrate():
    db = next(database.get_db())
    print("Adding columns to task_submissions table...")
    columns = [
        ("metabolic_impact", "FLOAT DEFAULT 0.0"),
        ("verification_status", "VARCHAR DEFAULT 'pending'")
    ]
    for name, type_def in columns:
        try:
            db.execute(text(f"ALTER TABLE task_submissions ADD COLUMN {name} {type_def};"))
            db.commit()
            print(f"Added {name}.")
        except Exception as e:
            if "already exists" in str(e):
                print(f"Column {name} already exists.")
            else:
                print(f"Error adding {name}: {e}")
            db.rollback()

if __name__ == "__main__":
    migrate()