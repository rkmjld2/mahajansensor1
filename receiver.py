import streamlit as st
import pymysql
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="ESP8266 Sensor Dashboard", layout="wide")
st.title("🔐 ESP8266 → TiDB Live Dashboard")

# ====================== CONNECTION ======================
@st.cache_resource(ttl=600)
def get_connection():
    """Safe TiDB connection"""
    try:
        secrets = st.secrets.get("tidb", {})
        conn = pymysql.connect(
            host=secrets.get("host", "gateway01.ap-southeast-1.prod.aws.tidbcloud.com"),
            port=int(secrets.get("port", 4000)),
            user=secrets.get("user", "ax6KHc1BNkyuaor.root"),
            password=secrets.get("password", "EP8isIWoEOQk7DSr"),
            database=secrets.get("database", "sensor"),
            ssl={'ca': None},
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        return conn
    except Exception as e:
        st.error(f"❌ Connection: {e}")
        return None

SECRET_KEY = st.secrets.get("security", {}).get("secret_key", "12b5112c62284ea0b3da0039f298ec7a85ac9a1791044052b6df970640afb1c5")

# ====================== TEST BUTTON ======================
col1, col2 = st.columns([1,3])
with col1:
    if st.button("🔍 Test DB", use_container_width=True):
        conn = get_connection()
        if conn:
            try:
                cur = conn.cursor()
                cur.execute("SELECT 1")
                st.success("✅ Connected!")
                cur.close()
                conn.close()
            except:
                st.error("❌ Test failed")
        else:
            st.error("❌ No connection")

# ====================== RECEIVE DATA ======================
st.subheader("📨 ESP8266 Receiver")
params = st.query_params

s1 = params.get("s1")
s2 = params.get("s2")
s3 = params.get("s3")
received_key = params.get("key")

if s1 and s2 and s3 and received_key:
    if received_key.startswith(SECRET_KEY):
        try:
            sensor1 = float(s1)
            sensor2 = float(s2)
            sensor3 = float(s3)

            conn = get_connection()
            if conn:
                cur = conn.cursor()
                cur.execute("INSERT INTO sensor_db (sensor1, sensor2, sensor3) VALUES (%s,%s,%s)", 
                           (sensor1, sensor2, sensor3))
                conn.commit()
                cur.close()
                conn.close()
                
                col1, col2, col3 = st.columns(3)
                col1.metric("S1", sensor1)
                col2.metric("S2", sensor2)
                col3.metric("S3", sensor3)
                st.success("✅ Saved!")
                st.balloons()
                st.rerun()
            else:
                st.error("❌ No DB")
        except Exception as e:
            st.error(f"❌ Save: {e}")
    else:
        st.error("🚫 Bad Key")
else:
    st.info("**URL**: `?s1=25&s2=60&s3=512&key=12b5112c62284ea0...`")

# ====================== DASHBOARD ======================
st.subheader("📊 Live Data")
conn = get_connection()
if conn:
    try:
        df = pd.read_sql("SELECT * FROM sensor_db ORDER BY id DESC LIMIT 50", conn)
        conn.close()
        
        if not df.empty:
            # Safe numeric
            for col in ['sensor1','sensor2','sensor3']:
                if col in df:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            st.dataframe(df, use_container_width=True)
            
            col1,col2,col3 = st.columns(3)
            col1.metric("Avg S1", f"{df.sensor1.mean():.1f}")
            col2.metric("Avg S2", f"{df.sensor2.mean():.1f}")
            col3.metric("Avg S3", f"{df.sensor3.mean():.0f}")
        else:
            st.info("No data yet")
            
    except Exception as e:
        st.error(f"❌ Read: {e}")
else:
    st.warning("Connect first")

st.markdown("---")
st.caption(f"Updated: {datetime.now().strftime('%H:%M:%S')}")
