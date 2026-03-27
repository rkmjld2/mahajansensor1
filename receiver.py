import streamlit as st
import pymysql
import pandas as pd

# ================= CONFIG =================
st.set_page_config(page_title="ESP8266 Dashboard", layout="wide")
st.title("📡 ESP8266 → TiDB Sensor Dashboard")

# ================= DB CONNECTION (FINAL FIX) =================
def get_connection():
    try:
        secrets = st.secrets["tidb"]

        conn = pymysql.connect(
            host=secrets["host"],
            port=int(secrets["port"]),
            user=secrets["user"],
            password=secrets["password"],
            database=secrets["database"],
            ssl={'ca': None},
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=True   # ✅ VERY IMPORTANT
        )
        return conn

    except Exception as e:
        st.error(f"❌ DB Connection Error: {e}")
        return None

# ================= SECRET KEY =================
SECRET_KEY = st.secrets.get("security", {}).get(
    "secret_key",
    "12b5112c62284ea0b3da0039f298ec7a85ac9a1791044052b6df970640afb1c5"
)

# ================= TEST BUTTON =================
if st.button("🔍 Test DB"):
    conn = get_connection()
    if conn:
        st.success("✅ Connected to DB")
        conn.close()
    else:
        st.error("❌ Connection Failed")

# =====================================================
# ================= RECEIVER ===========================
# =====================================================
st.subheader("📨 ESP8266 Receiver")

params = st.query_params

s1 = params.get("s1")
s2 = params.get("s2")
s3 = params.get("s3")
key = params.get("key")

if None not in (s1, s2, s3, key):

    if key == SECRET_KEY:
        try:
            conn = get_connection()

            if conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO sensor_db (sensor1, sensor2, sensor3) VALUES (%s, %s, %s)",
                        (float(s1), float(s2), float(s3))
                    )

                conn.close()
                st.success("✅ Data Received & Stored")

        except Exception as e:
            st.error(f"❌ Insert Error: {e}")

    else:
        st.error("🚫 Invalid Key")

else:
    st.info("➡ Waiting for ESP8266 data...")

# =====================================================
# ================= DASHBOARD ==========================
# =====================================================
st.subheader("📊 Live Sensor Data")

conn = get_connection()

if conn:
    try:
        df = pd.read_sql(
            "SELECT * FROM sensor_db ORDER BY id DESC LIMIT 50",
            conn
        )
        conn.close()

        if len(df) == 0:
            st.warning("📭 No data available")
        else:
            # FORMAT TIMESTAMP
            df['timestamp'] = pd.to_datetime(df['timestamp'])

            # DISPLAY TABLE
            st.dataframe(df, use_container_width=True)

            # METRICS
            col1, col2, col3 = st.columns(3)

            col1.metric("Avg Sensor1", f"{df['sensor1'].mean():.1f}")
            col2.metric("Avg Sensor2", f"{df['sensor2'].mean():.1f}")
            col3.metric("Avg Sensor3", f"{df['sensor3'].mean():.1f}")

            # CHART
            st.line_chart(df[['sensor1', 'sensor2', 'sensor3']])

    except Exception as e:
        st.error(f"❌ Query Error: {e}")

else:
    st.error("❌ No DB Connection")
