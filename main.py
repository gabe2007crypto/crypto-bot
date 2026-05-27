import requests
import time
import threading
from flask import Flask

# --- YOUR BOT SETUP ---
BOT_TOKEN = "8941579511:AAEOeBbL2BhOAOqgiRxtap1YCULDldwIoyk"
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

# --- THE FAKE WEB SERVER ---
app = Flask(__name__)


@app.route("/")
def index():
    return "Bot is alive and running!"


# --- YOUR BOT LOGIC ---
def get_updates(last_update_id):
    url = f"{BASE_URL}/getUpdates?offset={last_update_id + 1}"
    try:
        return requests.get(url).json()
    except Exception as e:
        print(f"Network error: {e}")
        return {"result": []}


def bot_loop():
    print("Bot is now listening for messages...")
    last_id = 0
    while True:
        updates = get_updates(last_id)
        if updates and "result" in updates and updates["result"]:
            for update in updates["result"]:
                last_id = update["update_id"]

                # Make sure the update is actually a text message
                if "message" in update and "text" in update["message"]:
                    chat_id = update["message"]["chat"]["id"]
                    text = update["message"]["text"]

                    print(f"Received: {text} from {chat_id}")

                    # Send a reply
                    requests.post(
                        f"{BASE_URL}/sendMessage",
                        json={"chat_id": chat_id, "text": f"I heard you say: {text}"},
                    )
        time.sleep(2)


# --- START EVERYTHING ---
if __name__ == "__main__":
    # 1. Start the bot in the background
    threading.Thread(target=bot_loop).start()

    # 2. Start the web server for Render
    # Render requires the host to be "0.0.0.0"
    app.run(host="0.0.0.0", port=8080)
