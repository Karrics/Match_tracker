from flask import Flask, render_template, request, redirect, session
import psycopg2
import os

app = Flask(__name__)
app.secret_key = "your_secret_key_here"

# Подключение к PostgreSQL
def get_db_connection():
    DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://postgres.arwdrcdztrinbsdcunky:6U7YZ3hoVzt5ECd7@aws-0-eu-north-1.pooler.supabase.com:5432/postgres")
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    return conn

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

@app.route('/')
def home():
    matches = get_matches()
    known_nicks = ["Karrics", "Shanhua", "HeBiBoBa", "Bolt n Jolt", "KinderVI", "Falke", "Ivabat", "wagoogus", "みどりみこ", "Nochy", "neofelis788", "T1kTakCat", "Frurik", "Rataty2001", "K0к0li0", "BENDYBOY", "Angel"]
    return render_template("index.html", matches=matches, session=session, nicks=known_nicks)

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



@app.route('/add_match', methods=["GET", "POST"])
def add_match():
    if not session.get("logged_in"):
        return redirect("/")

    known_nicks = ["Karrics", "Shanhua", "HeBiBoBa", "Bolt n Jolt", "KinderVI", "Falke", "Ivabat", "wagoogus", "みどりみこ", "Nochy", "neofelis788", "T1kTakCat", "Frurik", "Rataty2001", "K0к0li0", "BENDYBOY", "Angel"]

    if request.method == "POST":
        date = request.form.get("date")
        winner = request.form.get("winner")

        player_nicks = request.form.getlist("player_nick[]")
        player_champs = request.form.getlist("player_champ[]")
        player_kdas = request.form.getlist("player_kda[]")
        player_teams = request.form.getlist("player_team[]")

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("UPDATE match_counter SET current_value = current_value + 1 RETURNING current_value - 1")
        next_id = cursor.fetchone()[0]
        conn.commit()

        cursor.execute("INSERT INTO matches (custom_id, date, winner) VALUES (%s, %s, %s) RETURNING id",
                       (next_id, date, winner))
        match_id = cursor.fetchone()[0]

        for nick, champ, kda, team in zip(player_nicks, player_champs, player_kdas, player_teams):
            cursor.execute("INSERT INTO players (match_id, nickname, champion, kda, team) VALUES (%s, %s, %s, %s, %s)",
                           (match_id, nick, champ, kda, team))

        conn.commit()
        conn.close()
        return redirect("/")
    
    return render_template("add_match.html", nicks=known_nicks)

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
    port = int(os.environ.get("PORT", 10000))  # Render использует порт 10000 по умолчанию
    app.run(host="0.0.0.0", port=port)