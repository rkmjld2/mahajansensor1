import streamlit as st
import pymysql
import pandas as pd

# ================= CONFIG =================
st.set_page_config(page_title="ESP8266 Dashboard", layout="wide")
st.title("📡 ESP8266 → TiDB Sensor Dashboard")

# ================= DB CONNECTION =================
@st.cache_resource(ttl=600)
def get_connection():
    try:
        secrets = st.secrets.get("tidb", {})
        conn = pymysql.connect(
            host=secrets.get("host"),
            port=int(secrets.get("port", 4000)),
            user=secrets.get("user"),
            password=secrets.get("password"),
            database=secrets.get("database", "sensor"),
            ssl={'ca': None},
            cursorclass=pymysql.cursors.DictCursor
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
# ================= RECEIVER (ESP8266) =================
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
            sensor1 = float(s1)
            sensor2 = float(s2)
            sensor3 = float(s3)

            conn = get_connection()

            if conn:
                cur = conn.cursor()

                # INSERT DATA
                cur.execute(
                    "INSERT INTO sensor_db (sensor1, sensor2, sensor3) VALUES (%s, %s, %s)",
                    (sensor1, sensor2, sensor3)
                )

                conn.commit()

                cur.close()
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

            # SHOW TABLE
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
