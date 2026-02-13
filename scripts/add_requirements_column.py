from sqlalchemy import text
try:
    from moltapedia import database
except ImportError:
    import database

def migrate():
    db = next(database.get_db())
    print("Adding requirements column to tasks table...")
    try:
        db.execute(text("ALTER TABLE tasks ADD COLUMN requirements VARCHAR;"))
        db.commit()
        print("Success.")
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()

if __name__ == "__main__":
    migrate()
