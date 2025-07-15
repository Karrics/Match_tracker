from flask import Flask, render_template, request, redirect, session
import psycopg2
import os

app = Flask(__name__)
app.secret_key = "your_secret_key_here"

# Подключение к PostgreSQL
def get_db_connection():
    DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://postgres:vfnxNhtrth@db.arwdrcdztrinbsdcunky.supabase.co:5432/postgres")
    conn = psycopg2.connect(DATABASE_URL)
    return conn

# Инициализация таблиц
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Таблица матчей
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS matches (
            id SERIAL PRIMARY KEY,
            custom_id INTEGER UNIQUE,
            date TEXT,
            winner TEXT
        )
    ''')

    # Таблица игроков
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

    # Таблица админов
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admins (
            id SERIAL PRIMARY KEY,
            username TEXT UNIQUE,
            password TEXT
        )
    ''')

    # Таблица для счётчика
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS match_counter (
            id SERIAL PRIMARY KEY,
            current_value INTEGER NOT NULL DEFAULT 1
        )
    ''')

    # Вставляем тестового админа
    try:
        cursor.execute("INSERT INTO admins (username, password) VALUES ('admin', 'password123') ON CONFLICT (username) DO NOTHING")
    except:
        pass

    # Вставляем начальное значение счётчика, если его нет
    cursor.execute("SELECT COUNT(*) FROM match_counter")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO match_counter (current_value) VALUES (1)")

    conn.commit()
    conn.close()

# Получить все матчи
def get_matches():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM matches ORDER BY custom_id ASC")
    matches = cursor.fetchall()

    result = []
    for match in matches:
        cursor.execute("SELECT * FROM players WHERE match_id=%s", (match[0],))
        players = cursor.fetchall()
        result.append({
            "id": match[0],
            "custom_id": match[1],
            "date": match[2],
            "winner": match[3],
            "players": players
        })

    conn.close()
    return result

# Получить следующий номер матча
def get_next_custom_id():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE match_counter SET current_value = current_value + 1 RETURNING current_value - 1")
    next_id = cursor.fetchone()[0]
    conn.commit()
    conn.close()
    return next_id

@app.route('/')
def home():
    matches = get_matches()
    return render_template("index.html", matches=matches, session=session)

@app.route('/login', methods=["POST"])
def login():
    username = request.form.get("username")
    password = request.form.get("password")

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM admins WHERE username=%s AND password=%s", (username, password))
    admin = cursor.fetchone()
    conn.close()

    if admin:
        session["logged_in"] = True

    return redirect("/")

@app.route('/logout')
def logout():
    session.pop("logged_in", None)
    return redirect("/")

@app.route('/add_match', methods=["POST"])
def add_match():
    date = request.form.get("date")
    winner = request.form.get("winner")

    player_nicks = request.form.getlist("player_nick[]")
    player_champs = request.form.getlist("player_champ[]")
    player_kdas = request.form.getlist("player_kda[]")
    player_teams = request.form.getlist("player_team[]")

    conn = get_db_connection()
    cursor = conn.cursor()

    # Получаем уникальный порядковый номер матча
    custom_id = get_next_custom_id()

    # Добавляем матч
    cursor.execute("INSERT INTO matches (custom_id, date, winner) VALUES (%s, %s, %s) RETURNING id", (custom_id, date, winner))
    match_id = cursor.fetchone()[0]

    # Добавляем игроков
    for nick, champ, kda, team in zip(player_nicks, player_champs, player_kdas, player_teams):
        cursor.execute("INSERT INTO players (match_id, nickname, champion, kda, team) VALUES (%s, %s, %s, %s, %s)",
                       (match_id, nick, champ, kda, team))

    conn.commit()
    conn.close()
    return redirect("/")

@app.route('/delete_match/<int:match_id>', methods=['POST'])
def delete_match(match_id):
    if not session.get("logged_in"):
        return redirect("/")

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM players WHERE match_id=%s", (match_id,))
    cursor.execute("DELETE FROM matches WHERE id=%s", (match_id,))
    conn.commit()
    conn.close()

    return redirect("/")

if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)