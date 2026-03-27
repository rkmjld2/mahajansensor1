from flask import Flask, request, jsonify
import pymysql

app = Flask(__name__)

# 🔐 SECRET KEY
SECRET_KEY = "12b5112c62284ea0b3da0039f298ec7a85ac9a1791044052b6df970640afb1c5"

# 🗄️ DATABASE CONFIG (PUT YOUR DETAILS)
DB_HOST = "gateway01.ap-southeast-1.prod.aws.tidbcloud.com"
DB_PORT = 4000
DB_USER = "ax6KHc1BNkyuaor.root"
DB_PASSWORD = "EP8isIWoEOQk7DSr"
DB_NAME = "sensor"

def get_connection():
    return pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )

@app.route("/", methods=["GET"])
def receive_data():
    try:
        s1 = request.args.get("s1")
        s2 = request.args.get("s2")
        s3 = request.args.get("s3")
        key = request.args.get("key")

        if key != SECRET_KEY:
            return "❌ Unauthorized", 403

        if not s1 or not s2 or not s3:
            return "❌ Missing Data", 400

        conn = get_connection()
        cursor = conn.cursor()

        sql = "INSERT INTO sensor_db (sensor1, sensor2, sensor3) VALUES (%s, %s, %s)"
        cursor.execute(sql, (s1, s2, s3))

        conn.commit()
        cursor.close()
        conn.close()

        return "OK"

    except Exception as e:
        return f"❌ ERROR: {str(e)}"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)