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
            text = message.get("text", "").strip()

            if text:
                print(f"Received message: {text}")
                
                # Check if the user used the /price command
                if text.lower().startswith("/price"):
                    # Split the message into parts (e.g., ['/price', 'solana'])
                    parts = text.split()
                    
                    if len(parts) < 2:
                        send_message(chat_id, "💡 Please provide a coin name! Example: /price solana or /price ethereum")
                        continue
                    
                    # Get the coin name the user typed
                    target_coin = parts[1].lower()
                    
                    try:
                        # Fetch the custom coin price from CoinGecko
                        url = f"https://api.coingecko.com/api/v3/simple/price?ids={target_coin}&vs_currencies=usd"
                        response = requests.get(url).json()
                        
                        if target_coin in response and "usd" in response[target_coin]:
                            price = response[target_coin]["usd"]
                            send_message(chat_id, f"💰 The current price of {target_coin.upper()} is ${price:,} USD.")
                        else:
                            send_message(chat_id, f"⚠️ Could not find a coin named '{target_coin}' on CoinGecko. Double-check the spelling!")
                    except Exception as e:
                        print(f"API Error: {e}")
                        send_message(chat_id, "⚠️ Market data service is temporarily busy. Try again in a moment!")
                else:
                    send_message(chat_id, f"🤖 Multi-Crypto Radar active!\n\nUse `/price coin-name` to check any token.\nExample:\n• `/price bitcoin`\n• `/price solana`")
        time.sleep(1)

@app.route("/")
def index():
    return "Multi-Coin Bot is alive and running!"

if __name__ == "__main__":
    threading.Thread(target=keep_alive_loop, daemon=True).start()
    threading.Thread(target=bot_loop, daemon=True).start()
    app.run(host="0.0.0.0", port=8080)
