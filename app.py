from flask import Flask, render_template, request, redirect
import sqlite3
import requests

app = Flask(__name__)

API_KEY = "94160d3999a4415cb6e7852c6780556c"

def get_currency_price(pair):
    url = f"https://api.twelvedata.com/price?symbol={pair}&apikey={API_KEY}"
    response = requests.get(url)
    data = response.json()
    
    if "price" in data:
        return float(data["price"])
    return None

def calculate_rr(entry, tp, sl):
    t_pips = (tp - entry) * 100
    s_pips = (entry - sl) * 100
    return t_pips / s_pips

def init_db():
    conn = sqlite3.connect("journal.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pair TEXT,
            entry REAL,
            tp REAL,
            sl REAL,
            rr REAL,
            execution_type TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        pair = request.form["pair"].upper()
        execution_type = request.form["execution_type"]
        
        if execution_type == "current":
            entry = get_currency_price(pair)
        else:
            entry = float(request.form["entry"])
        
        tp = float(request.form["tp"])
        sl = float(request.form["sl"])
        rr = calculate_rr(entry, tp, sl)

        conn = sqlite3.connect("journal.db")
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO trades (pair, entry, tp, sl, rr, execution_type)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (pair, entry, tp, sl, rr, execution_type))
        conn.commit()
        conn.close()

        return redirect("/")

    conn = sqlite3.connect("journal.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM trades")
    trades = cursor.fetchall()
    conn.close()

    return render_template("journal.html", trades=trades)

if __name__ == "__main__":
    app.run(debug=True)