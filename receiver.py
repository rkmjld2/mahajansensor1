import streamlit as st
import pymysql
import pandas as pd

st.set_page_config(page_title="ESP8266 Sensor Dashboard", layout="wide")
st.title("🔐 ESP8266 → TiDB Live Dashboard")

# ====================== CONNECTION ======================
def get_connection():   # ❌ removed cache
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
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=True   # ✅ IMPORTANT
        )
        return conn
    except Exception as e:
        st.error(f"❌ Connection: {e}")
        return None


SECRET_KEY = st.secrets.get("security", {}).get(
    "secret_key",
    "12b5112c62284ea0b3da0039f298ec7a85ac9a1791044052b6df970640afb1c5"
)

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
            except Exception as e:
                st.error(f"❌ Test failed: {e}")
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

                cur.execute(
                    "INSERT INTO sensor_db (sensor1, sensor2, sensor3) VALUES (%s,%s,%s)",
                    (sensor1, sensor2, sensor3)
                )

                cur.close()
                conn.close()

                st.success("✅ Saved!")
                st.write(f"S1={sensor1}, S2={sensor2}, S3={sensor3}")

            else:
                st.error("❌ No DB")

        except Exception as e:
            st.error(f"❌ Save Error: {e}")
    else:
        st.error("🚫 Bad Key")
else:
    st.info("Use URL: ?s1=25&s2=60&s3=512&key=YOUR_KEY")

# ====================== DASHBOARD ======================
st.subheader("📊 Live Data")

try:
    conn = get_connection()

    if conn:
        df = pd.read_sql(
            "SELECT id, sensor1, sensor2, sensor3, timestamp FROM sensor_db ORDER BY id DESC LIMIT 50",
            conn
        )
        conn.close()

        st.write(f"**Found {len(df)} records**")

        if df.empty:
            st.warning("📭 EMPTY TABLE")
        else:
            # Convert to numeric safely
            for col in ['sensor1', 'sensor2', 'sensor3']:
                df[col] = pd.to_numeric(df[col], errors='coerce')

            st.dataframe(df, use_container_width=True)

            col1, col2, col3 = st.columns(3)

            col1.metric("Avg S1", f"{df['sensor1'].mean():.2f}" if df['sensor1'].notna().any() else "No data")
            col2.metric("Avg S2", f"{df['sensor2'].mean():.2f}" if df['sensor2'].notna().any() else "No data")
            col3.metric("Avg S3", f"{df['sensor3'].mean():.2f}" if df['sensor3'].notna().any() else "No data")

    else:
        st.error("❌ No connection")

except Exception as e:
    st.error(f"❌ Query Error: {e}")
