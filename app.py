import streamlit as st
import pymysql
import json
from flask import Flask, request
from datetime import datetime

# Database credentials
DB_CONFIG = {
    "host": "gateway01.ap-southeast-1.prod.aws.tidbcloud.com",
    "port": 4000,
    "user": "ax6KHc1BNkyuaor.root",
    "password": "EP8isIWoEOQk7DSr",
    "database": "sensor",
    "ssl": {"ssl": True}
}

# Security key
SECRET_KEY = "12b5112c62284ea0b3da0039f298ec7a85ac9a1791044052b6df970640afb1c5"

# Flask backend inside Streamlit
app = Flask(__name__)

def insert_sensor_values(sensor1, sensor2, sensor3):
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO sensor_db (sensor1, sensor2, sensor3, timestamp) VALUES (%s, %s, %s, %s)",
        (sensor1, sensor2, sensor3, datetime.now())
    )
    conn.commit()
    cursor.close()
    conn.close()

@app.route("/insert", methods=["POST"])
def insert():
    data = request.get_json()
    if not data:
        return {"error": "No data received"}, 400
    try:
        insert_sensor_values(data["sensor1"], data["sensor2"], data["sensor3"])
        return {"status": "success"}, 200
    except Exception as e:
        return {"error": str(e)}, 500

# Streamlit UI
st.title("ESP8266 Sensor Dashboard")

conn = pymysql.connect(**DB_CONFIG)
cursor = conn.cursor()
cursor.execute("SELECT id, sensor1, sensor2, sensor3, timestamp FROM sensor_db ORDER BY id DESC LIMIT 10")
rows = cursor.fetchall()
cursor.close()
conn.close()

st.write("Latest Sensor Data:")
for row in rows:
    st.write({
        "id": row[0],
        "sensor1": row[1],
        "sensor2": row[2],
        "sensor3": row[3],
        "timestamp": row[4].strftime("%Y-%m-%d %H:%M:%S") if row[4] else None
    })
