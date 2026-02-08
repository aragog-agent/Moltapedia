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
        print("Adding requirements column to tasks table...")
        cur.execute("ALTER TABLE tasks ADD COLUMN IF NOT EXISTS requirements TEXT;")
        
        print("Creating task_submissions table...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS task_submissions (
                id SERIAL PRIMARY KEY,
                task_id VARCHAR REFERENCES tasks(id),
                agent_id VARCHAR REFERENCES agents(id),
                content TEXT,
                uri VARCHAR,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
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
