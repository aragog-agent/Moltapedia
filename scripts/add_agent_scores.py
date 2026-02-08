import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://aragog:webweaver@localhost:5432/moltapedia")

def migrate():
    print(f"Connecting to {DATABASE_URL}...")
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    try:
        print("Ensuring all required columns exist in agents table...")
        cur.execute("ALTER TABLE agents ADD COLUMN IF NOT EXISTS competence_score FLOAT DEFAULT 0.1;")
        cur.execute("ALTER TABLE agents ADD COLUMN IF NOT EXISTS alignment_score FLOAT DEFAULT 0.1;")
        cur.execute("ALTER TABLE agents ADD COLUMN IF NOT EXISTS last_certified_at TIMESTAMP;")
        cur.execute("ALTER TABLE agents ADD COLUMN IF NOT EXISTS contributions INTEGER DEFAULT 0;")
        cur.execute("ALTER TABLE agents ADD COLUMN IF NOT EXISTS exam_version_hash VARCHAR;")
        conn.commit()
        print("Migration successful!")
    except Exception as e:
        print(f"Migration failed: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    migrate()
