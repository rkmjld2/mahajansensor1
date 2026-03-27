import streamlit as st
import pymysql
import pandas as pd

st.set_page_config(page_title="ESP8266 Sensor Dashboard", layout="wide")
st.title("🔐 ESP8266 → TiDB Live Dashboard")

# ====================== DB CONNECTION ======================
def get_connection():
    try:
        conn = pymysql.connect(
            host=st.secrets["tidb"]["host"],
            port=int(st.secrets["tidb"]["port"]),
            user=st.secrets["tidb"]["user"],
            password=st.secrets["tidb"]["password"],
            database=st.secrets["tidb"]["database"],
            ssl={'ca': None},
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=True
        )
        return conn
    except Exception as e:
        st.error(f"❌ DB Connection Error: {e}")
        return None


# ====================== SECRET KEY ======================
SECRET_KEY = st.secrets["security"]["secret_key"]


# ====================== TEST BUTTON ======================
if st.button("🔍 Test DB"):
    conn = get_connection()
    if conn:
        st.success("✅ Database Connected")
        conn.close()
    else:
        st.error("❌ Connection Failed")


# ====================== RECEIVE DATA ======================
st.subheader("📨 ESP8266 Receiver")

params = st.query_params

s1 = params.get("s1")
s2 = params.get("s2")
s3 = params.get("s3")
key = params.get("key")

st.write("DEBUG:", s1, s2, s3, key)

# Debug (you can remove later)
st.write("DEBUG:", s1, s2, s3, key)

if all([s1, s2, s3, key]):

    if key == SECRET_KEY:
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

                conn.commit()

                # Show latest inserted row
                cur.execute("SELECT * FROM sensor_db ORDER BY id DESC LIMIT 1")
                latest = cur.fetchone()

                st.success("✅ Data Saved Successfully")
                st.write("Latest Record:", latest)

                cur.close()
                conn.close()

        except Exception as e:
            st.error(f"❌ Insert Error: {e}")

    else:
        st.error("🚫 Invalid Key")

else:
    st.info("Send data using URL: ?s1=25&s2=60&s3=512&key=YOUR_KEY")


# ====================== DASHBOARD ======================
st.subheader("📊 Live Sensor Data")

try:
    conn = get_connection()

    if conn:
        df = pd.read_sql(
            "SELECT id, sensor1, sensor2, sensor3, timestamp FROM sensor_db ORDER BY id DESC LIMIT 50",
            conn
        )
        conn.close()

        if df.empty:
            st.warning("📭 No data available")
        else:
            # Convert to numeric
            df["sensor1"] = pd.to_numeric(df["sensor1"], errors="coerce")
            df["sensor2"] = pd.to_numeric(df["sensor2"], errors="coerce")
            df["sensor3"] = pd.to_numeric(df["sensor3"], errors="coerce")

            st.dataframe(df, use_container_width=True)

            # Metrics
            col1, col2, col3 = st.columns(3)

            col1.metric("Avg Sensor 1", f"{df['sensor1'].mean():.2f}")
            col2.metric("Avg Sensor 2", f"{df['sensor2'].mean():.2f}")
            col3.metric("Avg Sensor 3", f"{df['sensor3'].mean():.2f}")

    else:
        st.error("❌ Could not connect to DB")

except Exception as e:
    st.error(f"❌ Query Error: {e}")
