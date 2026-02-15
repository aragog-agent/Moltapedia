from sqlalchemy import text
try:
    from moltapedia import database
except ImportError:
    import database

def migrate():
    db = next(database.get_db())
    print("Adding 'content' column to articles table...")
    try:
        db.execute(text("ALTER TABLE articles ADD COLUMN content TEXT;"))
        db.commit()
        print("Added content column.")
    except Exception as e:
        if "already exists" in str(e):
            print("Column content already exists.")
        else:
            print(f"Error adding content column: {e}")
        db.rollback()

if __name__ == "__main__":
    migrate()
