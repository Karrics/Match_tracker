import psycopg2
import os

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://postgres.arwdrcdztrinbsdcunky:6U7YZ3hoVzt5ECd7@aws-0-eu-north-1.pooler.supabase.com:5432/postgres")

def init_db():
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS matches (
            id SERIAL PRIMARY KEY,
            custom_id INTEGER UNIQUE,
            date TEXT,
            winner TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS players (
            id SERIAL PRIMARY KEY,
            match_id INTEGER,
            nickname TEXT,
            champion TEXT,
            kda TEXT,
            team TEXT,
            FOREIGN KEY(match_id) REFERENCES matches(id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admins (
            id SERIAL PRIMARY KEY,
            username TEXT UNIQUE,
            password TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS match_counter (
            id SERIAL PRIMARY KEY,
            current_value INTEGER NOT NULL DEFAULT 1
        )
    ''')

    cursor.execute("INSERT INTO admins (username, password) VALUES ('admin', 'password123') ON CONFLICT (username) DO NOTHING")
    
    cursor.execute("SELECT COUNT(*) FROM match_counter")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO match_counter (current_value) VALUES (1)")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("✅ Таблицы успешно созданы!")