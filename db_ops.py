import sqlite3
import pandas as pd

DB_PATH = "db/activity.db"

def get_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def create_table():
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS activities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            tanggal TEXT,
            kategori TEXT,
            deskripsi TEXT,
            durasi INTEGER
        )
    ''')
    conn.commit()
    conn.close()

def insert_activity(username, tanggal, kategori, deskripsi, durasi):
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "INSERT INTO activities (username, tanggal, kategori, deskripsi, durasi) VALUES (?, ?, ?, ?, ?)",
        (username, tanggal, kategori, deskripsi, durasi)
    )
    conn.commit()
    conn.close()

def fetch_by_user(username):
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM activities WHERE username=?", conn, params=(username,))
    conn.close()
    return df

def update_activity(id, kategori, deskripsi, durasi):
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE activities SET kategori=?, deskripsi=?, durasi=? WHERE id=?",
              (kategori, deskripsi, durasi, id))
    conn.commit()
    conn.close()

def delete_activity(id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM activities WHERE id=?", (id,))
    conn.commit()
    conn.close()
