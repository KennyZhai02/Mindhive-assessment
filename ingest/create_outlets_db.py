import sqlite3
import pandas as pd
import os

def create_outlets_db():
    # Create sample outlet data for testing
    outlets_data = [
        {
            "name": "ZUS Coffee - SS 2",
            "address": "No. 1, Jalan SS 2/72, SS 2, 47300 Petaling Jaya, Selangor",
            "opening_hours": "8:00 AM - 10:00 PM",
            "services": "Dine-in, Takeaway, Delivery"
        },
        {
            "name": "ZUS Coffee - Bangsar",
            "address": "No. 2, Jalan Telawi 3, Bangsar, 59100 Kuala Lumpur",
            "opening_hours": "7:00 AM - 11:00 PM",
            "services": "Dine-in, Takeaway, Delivery"
        },
        {
            "name": "ZUS Coffee - Subang",
            "address": "Lot G-13, Subang Parade, Jalan SS16/1, 47500 Subang Jaya, Selangor",
            "opening_hours": "9:00 AM - 9:00 PM",
            "services": "Dine-in, Takeaway"
        },
        {
            "name": "ZUS Coffee - KLCC",
            "address": "L2-15, Suria KLCC, Jalan Ampang, 50088 Kuala Lumpur",
            "opening_hours": "10:00 AM - 10:00 PM",
            "services": "Dine-in, Takeaway, Delivery"
        },
        {
            "name": "ZUS Coffee - Damansara",
            "address": "G-03, Damansara Uptown, Jalan SS21/1, 47400 Petaling Jaya, Selangor",
            "opening_hours": "8:00 AM - 10:00 PM",
            "services": "Dine-in, Takeaway, Delivery"
        }
    ]

    df = pd.DataFrame(outlets_data)
    conn = sqlite3.connect("data/outlets.db")
    df.to_sql("outlets", conn, if_exists="replace", index=False)
    conn.close()
    print(f"SQLite database created at data/outlets.db with {len(outlets_data)} outlets")

if __name__ == "__main__":
    create_outlets_db()