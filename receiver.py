import streamlit as st
import pymysql
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Secure Sensor Receiver", layout="centered")
st.title("🔐 Secure ESP8266 Sensor Receiver")
st.markdown("**Only authorized ESP8266 can send data**")

# Database Connection
@st.cache_resource
def get_connection():
    secrets = st.secrets["tidb"]
    ca_path = "isrg_root_x1.pem"

    return pymysql.connect(
        host=secrets["host"],
        port=secrets["port"],
        user=secrets["user"],
        password=secrets["password"],
        database=secrets["database"],
        ssl={'ca': ca_path, 'verify_cert': True},
        autocommit=True,
        cursorclass=pymysql.cursors.DictCursor
    )

# Get secret key from Streamlit secrets
SECRET_KEY = st.secrets["security"]["secret_key"]

# ====================== RECEIVE SECURE DATA ======================
st.subheader("📨 Receiving Data from ESP8266")

params = st.query_params

temperature = params.get("temperature")
humidity = params.get("humidity")
device_id = params.get("device_id", "ESP8266_01")
received_key = params.get("key")

if temperature and humidity and received_key:
    if received_key == SECRET_KEY:
        try:
            temp = float(temperature)
            hum = float(humidity)

            conn = get_connection()
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO readings (temperature, humidity, device_id, created_at)
                    VALUES (%s, %s, %s, NOW())
                """, (temp, hum, device_id))
            conn.close()

            st.success("✅ Secure Data Received & Saved Successfully!")
            st.write(f"**Temperature:** {temp} °C")
            st.write(f"**Humidity:** {hum} %")
            st.write(f"**Device:** {device_id}")
            st.balloons()

        except Exception as e:
            st.error(f"❌ Save Error: {e}")
    else:
        st.error("❌ Invalid Secret Key! Access Denied.")
else:
    st.info("Waiting for authorized data from ESP8266...")

# Show recent data
st.subheader("📋 Last 10 Readings")
try:
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM sensor_db ORDER BY created_at DESC LIMIT 10", conn)
    conn.close()
    if not df.empty:
        st.dataframe(df, use_container_width=True)
    else:
        st.warning("No data yet.")
except Exception as e:
    st.error(f"Database Error: {e}")

st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
st.caption("🔒 Protected with Secret Key")