import streamlit as st
import pymysql
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Secure Sensor Receiver", layout="wide")
st.title("🔐 Secure ESP8266 → TiDB Sensor Receiver")

# Fixed DB Connection - YOUR TiDB creds, NO FILE PATH
@st.cache_resource
def get_connection():
    try:
        # Direct from secrets.toml [tidb] OR hardcoded for local
        secrets = st.secrets.get("tidb", {})
        conn = pymysql.connect(
            host=secrets.get("host", "gateway01.ap-southeast-1.prod.aws.tidbcloud.com"),
            port=int(secrets.get("port", 4000)),
            user=secrets.get("user", "ax6KHc1BNkyuaor.root"),
            password=secrets.get("password", "EP8isIWoEOQk7DSr"),
            database=secrets.get("database", "sensor"),
            ssl={'ca': None},  # Cloud-safe: encrypted, no CA file needed
            autocommit=True,
            cursorclass=pymysql.cursors.DictCursor,
            charset='utf8mb4'
        )
        return conn
    except Exception as e:
        st.error(f"❌ DB Error: {e}")
        st.info("**Fix**: Check TiDB cluster status or secrets.toml")
        raise

SECRET_KEY = st.secrets.get("security", {}).get("secret_key", "12b5112c62284ea0b3da0039f298ec7a85ac9a1791044052b6df970640afb1c5")

# ====================== RECEIVE DATA ======================
st.subheader("📨 ESP8266 Data Receiver")
params = st.query_params

s1 = params.get("s1")  # sensor1
s2 = params.get("s2")  # sensor2  
s3 = params.get("s3")  # sensor3
device_id = params.get("device_id", "ESP8266_01")
received_key = params.get("key")

if s1 and s2 and s3 and received_key:
    if received_key == SECRET_KEY:
        try:
            sensor1 = float(s1)
            sensor2 = float(s2)
            sensor3 = float(s3)

            conn = get_connection()
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO sensor_db (sensor1, sensor2, sensor3, timestamp)
                    VALUES (%s, %s, %s, NOW())
                """, (sensor1, sensor2, sensor3))
            conn.close()

            st.success("✅ Data Saved to TiDB!")
            col1, col2, col3 = st.columns(3)
            col1.metric("Sensor1", f"{sensor1}")
            col2.metric("Sensor2", f"{sensor2}")
            col3.metric("Sensor3", f"{sensor3}")
            st.balloons()

        except Exception as e:
            st.error(f"❌ Save failed: {e}")
    else:
        st.error("🚫 Invalid Key!")
else:
    st.info("**ESP8266 URL**: `https://yourapp.streamlit.app/?s1=25.5&s2=60&s3=512&key=YOUR_SECRET_KEY&device_id=ESP01`")

# ====================== LIVE DATA ======================
st.subheader("📊 Last 20 Readings")
try:
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM sensor_db ORDER BY id DESC LIMIT 20", conn)
    conn.close()
    if not df.empty:
        st.dataframe(df, use_container_width=True)
        st.metric("Avg S1", f"{df['sensor1'].mean():.1f}")
        st.metric("Avg S2", f"{df['sensor2'].mean():.1f}")
        st.metric("Avg S3", f"{df['sensor3'].mean():.1f}")
    else:
        st.warning("No data. Send from ESP8266!")
except Exception as e:
    st.error(f"❌ Read Error: {e}")

st.caption(f"Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}")
