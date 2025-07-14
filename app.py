from flask import Flask, render_template, request, redirect, session
import sqlite3

app = Flask(__name__)
app.secret_key = "your_secret_key_here"

# Инициализация базы данных
def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS matches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            winner TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS players (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
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
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            password TEXT
        )
    ''')
    # Добавляем тестового админа
    cursor.execute("INSERT OR IGNORE INTO admins (username, password) VALUES ('admin', 'password123')")
    conn.commit()
    conn.close()

# Получить все матчи
def get_matches():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM matches")
    matches = cursor.fetchall()
    result = []
    for match in matches:
        cursor.execute("SELECT * FROM players WHERE match_id=?", (match[0],))
        players = cursor.fetchall()
        result.append({
            "id": match[0],
            "date": match[1],
            "winner": match[2],
            "players": players
        })
    conn.close()
    return result

@app.route('/')
def home():
    matches = get_matches()
    return render_template("index.html", matches=matches)

@app.route('/login', methods=["POST"])
def login():
    username = request.form.get("username")
    password = request.form.get("password")

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM admins WHERE username=? AND password=?", (username, password))
    admin = cursor.fetchone()
    conn.close()

    if admin:
        session["logged_in"] = True
        return redirect("/add_match")
    else:
        return "Неверный логин или пароль", 401

@app.route('/logout')
def logout():
    session.pop("logged_in", None)
    return redirect("/")

@app.route('/add_match', methods=["GET", "POST"])
def add_match():
    if not session.get("logged_in"):
        return redirect("/")
    
    if request.method == "POST":
        date = request.form.get("date")
        winner = request.form.get("winner")
        
        player_nicks = request.form.getlist("player_nick[]")
        player_champs = request.form.getlist("player_champ[]")
        player_kdas = request.form.getlist("player_kda[]")
        player_teams = request.form.getlist("player_team[]")

        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO matches (date, winner) VALUES (?, ?)", (date, winner))
        match_id = cursor.lastrowid

        for nick, champ, kda, team in zip(player_nicks, player_champs, player_kdas, player_teams):
            cursor.execute("INSERT INTO players (match_id, nickname, champion, kda, team) VALUES (?, ?, ?, ?, ?)",
                           (match_id, nick, champ, kda, team))

        conn.commit()
        conn.close()
        return redirect("/")

    return render_template("add_match.html")

if __name__ == '__main__':
    app.run(debug=False)