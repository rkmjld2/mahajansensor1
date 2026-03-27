import streamlit as st
import pymysql
import pandas as pd

st.set_page_config(page_title="ESP8266 Sensor Dashboard", layout="wide")
st.title("🔐 ESP8266 → TiDB Live Dashboard")

# ====================== CONNECTION ======================
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


# ====================== TEST CONNECTION ======================
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

st.write("DEBUG PARAMS:", s1, s2, s3, key)

if None not in (s1, s2, s3, key):

    if key == SECRET_KEY:
        try:
            sensor1 = float(s1)
            sensor2 = float(s2)
            sensor3 = float(s3)

            st.write("Parsed:", sensor1, sensor2, sensor3)

            conn = get_connection()

            if conn:
                cur = conn.cursor()

                # 🔍 SHOW DB NAME
                cur.execute("SELECT DATABASE()")
                st.write("DB NAME:", cur.fetchone())

                # 🔍 SHOW TABLES
                cur.execute("SHOW TABLES")
                st.write("TABLES:", cur.fetchall())

                # 🔥 INSERT
                cur.execute(
                    "INSERT INTO sensor_db (sensor1, sensor2, sensor3) VALUES (%s,%s,%s)",
                    (sensor1, sensor2, sensor3)
                )

                conn.commit()

                # 🔍 VERIFY INSERT
                cur.execute("SELECT * FROM sensor_db ORDER BY id DESC LIMIT 5")
                rows = cur.fetchall()
                st.write("LATEST DATA:", rows)

                cur.close()
                conn.close()

                st.success("✅ Data Saved Successfully")

        except Exception as e:
            st.error(f"❌ Insert Error: {e}")

    else:
        st.error("🚫 Invalid Key")

else:
    st.info("Use URL: ?s1=25&s2=60&s3=512&key=YOUR_KEY")


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

        st.write(f"Total Records: {len(df)}")

        if df.empty:
            st.warning("📭 No data in table")
        else:
            # Convert safely
            for col in ["sensor1", "sensor2", "sensor3"]:
                df[col] = pd.to_numeric(df[col], errors="coerce")

            st.dataframe(df, use_container_width=True)

            col1, col2, col3 = st.columns(3)

            col1.metric("Avg S1", f"{df['sensor1'].mean():.2f}")
            col2.metric("Avg S2", f"{df['sensor2'].mean():.2f}")
            col3.metric("Avg S3", f"{df['sensor3'].mean():.2f}")

    else:
        st.error("❌ DB connection failed")

except Exception as e:
    st.error(f"❌ Query Error: {e}")
