import os, requests, json
from flask import Flask, send_file, request, jsonify
from pymongo import MongoClient

app = Flask(__name__)

# ===== ENV VARIABLES (Render se aayenge) =====
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
RENDER_URL = os.environ.get("RENDER_URL")
MONGO_URI = os.environ.get("MONGO_URI")

# ===== MongoDB =====
client = MongoClient(MONGO_URI)
db = client["jee_database"]
collection = db["content"]

# ===== ROUTES =====
@app.route("/")
def home():
    return send_file("index.html")

@app.route("/get_video")
def get_video():
    sub = request.args.get("sub")
    ch = request.args.get("ch")
    lec = request.args.get("id")

    doc = collection.find_one({"subject": sub, "chapter": ch})
    if doc and lec in doc["lectures"]:
        return jsonify({"url": doc["lectures"][lec]})

    return jsonify({"url": "https://t.me/blackvaltofficial/8?embed=1"})

@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    data = request.get_json()

    if "message" in data:
        cid = str(data["message"]["chat"]["id"])
        text = data["message"].get("text", "")

        if text == "/start":
            kb = {
                "inline_keyboard": [
                    [{"text": "Physics", "callback_data": "u_phy"},
                     {"text": "Chemistry", "callback_data": "u_chem"}],
                    [{"text": "Maths", "callback_data": "u_math"}]
                ]
            }
            requests.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                json={"chat_id": cid, "text": "📚 Select Subject", "reply_markup": kb}
            )

        elif cid == CHAT_ID and text.startswith("/add"):
            try:
                _, sub, ch, lec, link = text.split("|")
                if "embed" not in link:
                    link += "?embed=1&autoplay=1"

                collection.update_one(
                    {"subject": sub, "chapter": ch},
                    {"$set": {f"lectures.{lec}": link}},
                    upsert=True
                )

                requests.post(
                    f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                    json={"chat_id": cid, "text": "✅ Lecture Added"}
                )
            except:
                requests.post(
                    f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                    json={"chat_id": cid, "text": "❌ Format: /add phy|Kinematics|Lec1|link"}
                )

    elif "callback_query" in data:
        cq = data["callback_query"]
        cid = cq["message"]["chat"]["id"]
        choice = cq["data"]

        if choice.startswith("u_"):
            sub = choice[2:]
            chapters = collection.distinct("chapter", {"subject": sub})
            kb = [[{"text": ch, "callback_data": f"ch_{sub}_{ch}"}] for ch in chapters]

            requests.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                json={"chat_id": cid, "text": "Select Chapter", "reply_markup": {"inline_keyboard": kb}}
            )

        elif choice.startswith("ch_"):
            _, sub, ch = choice.split("_")
            doc = collection.find_one({"subject": sub, "chapter": ch})
            kb = [[{
                "text": lec,
                "url": f"{RENDER_URL}?sub={sub}&ch={ch}&id={lec}"
            }] for lec in doc["lectures"].keys()]

            requests.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                json={"chat_id": cid, "text": "Select Lecture", "reply_markup": {"inline_keyboard": kb}}
            )

    return "OK", 200


if __name__ == "__main__":
    requests.get(
        f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook?url={RENDER_URL}/{BOT_TOKEN}"
    )
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
