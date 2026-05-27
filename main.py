import os
import time
import requests
import threading
from flask import Flask

app = Flask(__name__)

# --- CONFIGURATION ---
BOT_TOKEN = "8941579511:AAEOeBbL2BhOAOqgiRxtap1YCULDldwIoyk"
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"
RENDER_URL = "https://crypto-bot-cfzt.onrender.com"
TRACKED_COIN = "bitcoin" 

# --- KEEP ALIVE BACKGROUND TASK ---
def keep_alive_loop():
    """Pings the server every 5 minutes so Render never falls asleep."""
    time.sleep(20)
    while True:
        try:
            print("Sending keep-alive heartbeat...")
            requests.get(RENDER_URL)
        except Exception as e:
            print(f"Keep-alive ping failed: {e}")
        time.sleep(300)

# --- CRYPTO TRACKER BACKGROUND TASK ---
def crypto_tracker_loop():
    """Watches crypto prices every 60 seconds."""
    print("Crypto tracking system initialized...")
    while True:
        try:
            url = f"https://api.coingecko.com/api/v3/simple/price?ids={TRACKED_COIN}&vs_currencies=usd"
            response = requests.get(url).json()
            if TRACKED_COIN in response:
                current_price = response[TRACKED_COIN]["usd"]
                print(f"Current {TRACKED_COIN.upper()} Price: ${current_price}")
        except Exception as e:
            print(f"Market fetch error: {e}")
        time.sleep(60)

# --- TELEGRAM BOT LOGIC ---
def get_updates(last_update_id):
    try:
        url = f"{BASE_URL}/getUpdates?offset={last_update_id + 1}"
        return requests.get(url).json()
    except Exception as e:
        return {"result": []}

def send_message(chat_id, text):
    try:
        url = f"{BASE_URL}/sendMessage"
        requests.post(url, json={"chat_id": chat_id, "text": text})
    except Exception as e:
        print(f"Failed to send message: {e}")

def bot_loop():
    print("Bot is now listening for messages...")
    last_update_id = 0
    while True:
        updates = get_updates(last_update_id)
        for update in updates.get("result", []):
            last_update_id = update["update_id"]
            message = update.get("message", {})
            chat_id = message.get("chat", {}).get("id")
            text = message.get("text", "")

            if text:
                print(f"Received message: {text}")
                if text.lower() == "/price":
                    try:
                        url = f"https://api.coingecko.com/api/v3/simple/price?ids={TRACKED_COIN}&vs_currencies=usd"
                        price = requests.get(url).json()[TRACKED_COIN]["usd"]
                        send_message(chat_id, f"💰 The current price of {TRACKED_COIN.upper()} is ${price} USD.")
                    except:
                        send_message(chat_id, "⚠️ Could not retrieve market data right now.")
                else:
                    send_message(chat_id, f"🤖 Radar active. Use /price to check current market status.")
        time.sleep(1)

@app.route("/")
def index():
    return "Bot is alive and running!"

# This launches all three background systems smoothly together when the file boots up
if __name__ == "__main__":
    threading.Thread(target=keep_alive_loop, daemon=True).start()
    threading.Thread(target=crypto_tracker_loop, daemon=True).start()
    threading.Thread(target=bot_loop, daemon=True).start()
    app.run(host="0.0.0.0", port=8080)
