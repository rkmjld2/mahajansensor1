import streamlit as st
import pandas as pd
import pymysql

st.set_page_config(page_title="Sensor Dashboard", layout="wide")

st.title("📊 Live Sensor Dashboard")

# DB CONNECTION
def get_data():
    conn = pymysql.connect(
        host="gateway01.ap-southeast-1.prod.aws.tidbcloud.com",
        port=4000,
        user="ax6KHc1BNkyuaor.root",
        password="EP8isIWoEOQk7DSr",
        database="sensor"
    )

    query = "SELECT * FROM sensor_db ORDER BY id DESC LIMIT 100"
    df = pd.read_sql(query, conn)
    conn.close()
    return df

# AUTO REFRESH
st.sidebar.title("Settings")
refresh = st.sidebar.slider("Refresh (seconds)", 5, 60, 10)

# LOAD DATA
df = get_data()

# SHOW TABLE
st.subheader("📋 Latest Data")
st.dataframe(df, use_container_width=True)

# GRAPH
st.subheader("📈 Sensor Graph")

if not df.empty:
    df_chart = df.sort_values("id")
    st.line_chart(df_chart[["sensor1", "sensor2", "sensor3"]])
else:
    st.warning("No data available")

# AUTO REFRESH
#st.experimental_rerun()   // lines replace
import time
time.sleep(refresh)
st.rerun()
