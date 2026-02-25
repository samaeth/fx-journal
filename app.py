from flask import Flask, render_template, request, redirect
import sqlite3
import requests
import os

app = Flask(__name__)

# Get API key from Vercel environment variable
API_KEY = os.environ.get("API_KEY")

# Temporary DB path (writable on Vercel)
DB_PATH = "/tmp/journal.db"

# Initialize database
def init_db():
    conn = sqlite3.connect(DB_PATH)
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

# Function to fetch live price
def get_currency_price(pair):
    url = f"https://api.twelvedata.com/price?symbol={pair}&apikey={API_KEY}"
    response = requests.get(url)
    data = response.json()
    
    if "price" in data:
        return float(data["price"])
    else:
        return None

# RR calculation
def calculate_rr(entry, tp, sl):
    t_pips = (tp - entry) * 100
    s_pips = (entry - sl) * 100
    if s_pips == 0:
        return 0
    return t_pips / s_pips

# Main route
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        pair = request.form["pair"].upper()
        execution_type = request.form["execution_type"]

        # Entry price
        if execution_type == "current":
            entry = get_currency_price(pair)
            if entry is None:
                return "Error fetching current price. Check API_KEY and pair."
        else:
            entry = float(request.form["entry"])

        tp = float(request.form["tp"])
        sl = float(request.form["sl"])
        rr = calculate_rr(entry, tp, sl)

        # Save to DB
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO trades (pair, entry, tp, sl, rr, execution_type)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (pair, entry, tp, sl, rr, execution_type))
        conn.commit()
        conn.close()

        return redirect("/")

    # Display trades
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM trades ORDER BY id DESC")
    trades = cursor.fetchall()
    conn.close()

    return render_template("index.html", trades=trades)

if __name__ == "__main__":
    app.run()
