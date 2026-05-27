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

# This starts empty; the bot will automatically fill it with thousands of coins on startup!
COIN_MAPPING = {}

def fetch_master_coin_list():
    """Downloads all 12,000+ coin abbreviations from CoinGecko automatically."""
    global COIN_MAPPING
    print("Connecting to CoinGecko to download the master token list...")
    try:
        url = "https://api.coingecko.com/api/v3/coins/list"
        response = requests.get(url).json()
        
        # Build the dynamic mapping dictionary automatically
        temp_mapping = {}
        for coin in response:
            symbol = coin["symbol"].lower()
            coin_id = coin["id"]
            temp_mapping[symbol] = coin_id
            
        COIN_MAPPING = temp_mapping
        print(f"🔥 Success! Loaded {len(COIN_MAPPING)} crypto abbreviations into the Radar database.")
    except Exception as e:
        print(f"Error downloading master coin list: {e}")

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
                
                if text.lower().startswith("/price"):
                    parts = text.split()
                    
                    if len(parts) < 2:
                        send_message(chat_id, "💡 Please provide a coin abbreviation!\nExample: `/price btc` or `/price wkc`")
                        continue
                    
                    user_input = parts[1].lower()
                    
                    # Look up the abbreviation in our massive auto-generated dictionary
                    target_coin = COIN_MAPPING.get(user_input, user_input)
                    
                    try:
                        url = f"https://api.coingecko.com/api/v3/simple/price?ids={target_coin}&vs_currencies=usd"
                        response = requests.get(url).json()
                        
                        if target_coin in response and "usd" in response[target_coin]:
                            price = response[target_coin]["usd"]
                            
                            # Smart formatting for small penny/meme tokens
                            if price < 0.000001:
                                price_str = f"${price:.10f}"
                            elif price < 1.0:
                                price_str = f"${price:.6f}"
                            else:
                                price_str = f"${price:,} USD"
                                
                            send_message(chat_id, f"💰 The current price of {user_input.upper()} is {price_str}.")
                        else:
                            send_message(chat_id, f"⚠️ Could not find pricing for '{user_input.upper()}'. Make sure the abbreviation is correct!")
                    except Exception as e:
                        print(f"API Error: {e}")
                        send_message(chat_id, "⚠️ Market data service is temporarily busy. Try again in a moment!")
                else:
                    send_message(chat_id, f"🤖 Infinite Crypto Radar active!\n\nUse `/price shortcut` for ANY token in existence.\nExample:\n• `/price btc`\n• `/price wkc`\n• `/price eth`\n• `/price pepe`")
        time.sleep(1)

@app.route("/")
def index():
    return "Infinite Ticker Bot is alive and running!"

if __name__ == "__main__":
    # 1. Download the thousands of coins first
    fetch_master_coin_list()
    
    # 2. Start the background processes
    threading.Thread(target=keep_alive_loop, daemon=True).start()
    threading.Thread(target=bot_loop, daemon=True).start()
    app.run(host="0.0.0.0", port=8080)
