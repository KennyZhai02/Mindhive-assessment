# ingest/create_outlets_db.py
import sqlite3
import pandas as pd

def create_outlets_db():
    df = pd.read_csv("data/outlets.csv")
    conn = sqlite3.connect("data/outlets.db")
    df.to_sql("outlets", conn, if_exists="replace", index=False)
    conn.close()
    print("SQLite database created at data/outlets.db")

if __name__ == "__main__":
    create_outlets_db()