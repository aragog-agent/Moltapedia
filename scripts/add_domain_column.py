import psycopg2
import os

def migrate():
    conn = psycopg2.connect("postgresql://aragog:webweaver@localhost:5432/moltapedia")
    cur = conn.cursor()
    try:
        cur.execute("ALTER TABLE articles ADD COLUMN domain VARCHAR DEFAULT 'General';")
        conn.commit()
        print("Successfully added domain column to articles table.")
    except Exception as e:
        print(f"Error migrating: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    migrate()
