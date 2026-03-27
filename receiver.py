import streamlit as st
import pymysql
import pandas as pd
from datetime import datetime

st.set_page_config(layout="wide")
st.title("🔐 ESP8266 → TiDB Dashboard")

# Database connection
@st.cache_resource(ttl=600)
def get_db():
    return pymysql.connect(
        host=st.secrets["tidb"]["host"],
        port=st.secrets["tidb"]["port"],
        user=st.secrets["tidb"]["user"],
        password=st.secrets["tidb"]["password"],
        database=st.secrets["tidb"]["database"],
        ssl={'ca': None},
        charset='utf8mb4'
    )

SECRET_KEY = st.secrets["security"]["secret_key"]

# Test connection
if st.button("🔍 Test Connection"):
    try:
        conn = get_db()
        pd.read_sql("SELECT 1", conn)
        st.success("✅ Connected!")
        conn.close()
    except Exception as e:
        st.error(f"❌ {e}")

# Receive ESP data
st.subheader("📨 Receive Data")
params = st.query_params
s1, s2, s3, key = params.get("s1"), params.get("s2"), params.get("s3"), params.get("key")

if s1 and s2 and s3 and key == SECRET_KEY:
    try:
        conn = get_db()
        conn.execute("INSERT INTO sensor_db (sensor1,sensor2,sensor3) VALUES (%s,%s,%s)", 
                    (float(s1), float(s2), float(s3)))
        conn.commit()
        conn.close()
        st.success(f"✅ Saved: S1={s1}, S2={s2}, S3={s3}")
        st.balloons()
        st.rerun()
    except Exception as e:
        st.error(f"❌ Save: {e}")
else:
    st.info("**Test**: `?s1=25&s2=60&s3=512&key=12b5112c62284ea0b3da0039f298ec7a85ac9a1791044052b6df970640afb1c5`")

# Show records - FIXED VERSION
st.subheader("📊 Records")
try:
    conn = get_db()
    
    # Raw query - no pandas.read_sql bug
    cur = conn.cursor(pymysql.cursors.DictCursor)
    cur.execute("SELECT * FROM sensor_db ORDER BY id DESC LIMIT 20")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    
    if rows:
        # Convert to DataFrame manually
        df = pd.DataFrame(rows)
        st.dataframe(df)
        
        # Safe averages
        col1, col2, col3 = st.columns(3)
        col1.metric("Avg S1", f"{df['sensor1'].mean():.1f}")
        col2.metric("Avg S2", f"{df['sensor2'].mean():.1f}")
        col3.metric("Avg S3", f"{df['sensor3'].mean():.0f}")
    else:
        st.info("No records yet")
        
except Exception as e:
    st.error(f"❌ Query: {e}")

st.caption(f"Updated: {datetime.now().strftime('%H:%M:%S')}")
