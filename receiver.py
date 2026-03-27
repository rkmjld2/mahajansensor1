import streamlit as st
import pymysql
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Secure Sensor Receiver", layout="wide")
st.title("🔐 ESP8266 → TiDB Sensor Dashboard")

# FIXED Connection - No autocommit, proper context
@st.cache_resource(ttl=300)  # Refresh every 5min
def get_connection():
    try:
        secrets = st.secrets.get("tidb", {})
        conn = pymysql.connect(
            host=secrets.get("host", "gateway01.ap-southeast-1.prod.aws.tidbcloud.com"),
            port=int(secrets.get("port", 4000)),
            user=secrets.get("user", "ax6KHc1BNkyuaor.root"),
            password=secrets.get("password", "EP8isIWoEOQk7DSr"),
            database=secrets.get("database", "sensor"),
            ssl={'ca': None},  # Safe for cloud
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        return conn
    except Exception as e:
        st.error(f"❌ Connection failed: {e}")
        st.stop()

SECRET_KEY = st.secrets.get("security", {}).get("secret_key", "12b5112c62284ea0b3da0039f298ec7a85ac9a1791044052b6df970640afb1c5")

# Test Connection Button
if st.button("🔍 Test TiDB Connection"):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1")
        st.success("✅ TiDB Connected!")
        conn.close()
    except Exception as e:
        st.error(f"❌ Test failed: {e}")

# ====================== RECEIVE DATA ======================
st.subheader("📨 Receive from ESP8266")
params = st.query_params

s1 = params.get("s1")
s2 = params.get("s2")
s3 = params.get("s3")
device_id = params.get("device_id", "ESP01")
received_key = params.get("key")

if s1 and s2 and s3 and received_key:
    if received_key == SECRET_KEY:
        try:
            sensor1, sensor2, sensor3 = float(s1), float(s2), float(s3)
            
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO sensor_db (sensor1, sensor2, sensor3) 
                VALUES (%s, %s, %s)
            """, (sensor1, sensor2, sensor3))
            conn.commit()
            cur.close()
            conn.close()

            col1, col2, col3 = st.columns(3)
            col1.success(f"**S1**: {sensor1}")
            col2.success(f"**S2**: {sensor2}")
            col3.success(f"**S3**: {sensor3}")
            st.balloons()

        except Exception as e:
            st.error(f"❌ Insert failed: {e}")
    else:
        st.error("🚫 Wrong Key!")
else:
    st.info("**Test URL**: `?s1=25&s2=60&s3=512&key=12b5112c62284ea0b3da0039f298ec7a85ac9a1791044052b6df970640afb1c5`")

# ====================== SHOW DATA ======================
st.subheader("📊 Live Data")
try:
    with get_connection() as conn:
        df = pd.read_sql("SELECT * FROM sensor_db ORDER BY id DESC LIMIT 20", conn)
    
    if not df.empty:
        st.dataframe(df, use_container_width=True)
        col1, col2, col3 = st.columns(3)
        col1.metric("Avg Sensor1", f"{df['sensor1'].mean():.1f}")
        col2.metric("Avg Sensor2", f"{df['sensor2'].mean():.1f}")
        col3.metric("Avg Sensor3", f"{df['sensor3'].mean():.0f}")
    else:
        st.info("📭 No data yet - send from ESP!")
except Exception as e:
    st.error(f"❌ Query failed: {e}")
    st.info("**Check**: Table `sensor.sensor_db` exists?")

st.caption(f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}")
