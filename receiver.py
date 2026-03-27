import streamlit as st
import pymysql
import pandas as pd
from datetime import datetime

# Page config
st.set_page_config(page_title="ESP8266 Sensor Dashboard", layout="wide")

# Title
st.title("🔐 ESP8266 Secure Sensor Receiver → TiDB")
st.markdown("**Receive 3 sensors via HTTP + Display live data**")

# ====================== CONNECTION ======================
@st.cache_resource(ttl=600)
def get_connection():
    """TiDB connection - safe for local/cloud"""
    try:
        # From .streamlit/secrets.toml [tidb]
        secrets = st.secrets.get("tidb", {})
        conn = pymysql.connect(
            host=secrets.get("host", "gateway01.ap-southeast-1.prod.aws.tidbcloud.com"),
            port=int(secrets.get("port", 4000)),
            user=secrets.get("user", "ax6KHc1BNkyuaor.root"),
            password=secrets.get("password", "EP8isIWoEOQk7DSr"),
            database=secrets.get("database", "sensor"),
            ssl={'ca': None},  # Encrypted, cloud-safe
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        return conn
    except Exception as e:
        st.error(f"❌ Connection Error: {e}")
        st.stop()

# Secret key for ESP8266 auth
SECRET_KEY = st.secrets.get("security", {}).get("secret_key", "12b5112c62284ea0b3da0039f298ec7a85ac9a1791044052b6df970640afb1c5")

# ====================== TEST CONNECTION ======================
col1, col2 = st.columns(2)
with col1:
    if st.button("🔍 Test Connection", use_container_width=True):
        try:
            with get_connection() as conn:
                cur = conn.cursor()
                cur.execute("SELECT 1 as test")
                st.success("✅ TiDB Connected!")
        except Exception as e:
            st.error(f"❌ Test failed: {e}")

# ====================== RECEIVE ESP DATA ======================
st.subheader("📨 ESP8266 Data Receiver")
params = st.query_params

s1 = params.get("s1")
s2 = params.get("s2") 
s3 = params.get("s3")
device_id = params.get("device_id", "ESP01")
received_key = params.get("key")

if s1 and s2 and s3 and received_key:
    if received_key[0:64] == SECRET_KEY:  # First 64 chars
        try:
            sensor1 = float(s1)
            sensor2 = float(s2)
            sensor3 = float(s3)

            with get_connection() as conn:
                cur = conn.cursor()
                cur.execute("""
                    INSERT INTO sensor_db (sensor1, sensor2, sensor3) 
                    VALUES (%s, %s, %s)
                """, (sensor1, sensor2, sensor3))
                conn.commit()

            col1, col2, col3 = st.columns(3)
            col1.success(f"Sensor1: **{sensor1:.1f}**")
            col2.success(f"Sensor2: **{sensor2:.1f}**")
            col3.success(f"Sensor3: **{sensor3:.0f}**")
            st.balloons()
            st.rerun()

        except Exception as e:
            st.error(f"❌ Insert Error: {e}")
    else:
        st.error("🚫 **Invalid Secret Key**")
        st.stop()
else:
    st.info("""
    **ESP8266 Test URL**:  
    `https://yourapp.streamlit.app/?s1=25.5&s2=60.0&s3=512&key=12b5112c62284ea0b3da0039f298ec7a85ac9a1791044052b6df970640afb1c5`
    """)

# ====================== LIVE DASHBOARD ======================
st.subheader("📊 Live Sensor Data")
try:
    with get_connection() as conn:
        df = pd.read_sql("""
            SELECT id, timestamp, sensor1, sensor2, sensor3 
            FROM sensor_db 
            ORDER BY id DESC LIMIT 50
        """, conn)

    if not df.empty:
        # Safe numeric conversion
        for col in ['sensor1', 'sensor2', 'sensor3']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        st.dataframe(df, use_container_width=True)
        
        # Metrics (safe)
        col1, col2, col3 = st.columns(3)
        s1_mean = df['sensor1'].mean()
        col1.metric("Sensor1", f"{s1_mean:.1f}" if pd.notna(s1_mean) else "N/A")
        
        s2_mean = df['sensor2'].mean()
        col2.metric("Sensor2", f"{s2_mean:.1f}" if pd.notna(s2_mean) else "N/A")
        
        s3_mean = df['sensor3'].mean()
        col3.metric("Sensor3", f"{s3_mean:.0f}" if pd.notna(s3_mean) else "N/A")
        
        st.plotly_chart(
            pd.DataFrame({
                'time': range(len(df)),
                'S1': df['sensor1'],
                'S2': df['sensor2'],
                'S3': df['sensor3']
            }).plot(x='time', y=['S1', 'S2', 'S3']).figure,
            use_container_width=True
        )
    else:
        st.info("📤 No data yet - send from ESP8266!")

except Exception as e:
    st.error(f"❌ Dashboard Error: {e}")
    st.info("**Run**: `DROP TABLE sensor_db; CREATE TABLE...` (previous message)")

# Footer
st.markdown("---")
st.caption(f"🕐 Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}")
st.caption("Deployed on Streamlit Cloud | ESP8266 → HTTP → TiDB")
