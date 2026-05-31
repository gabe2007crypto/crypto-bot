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

# 🔍 PASTE YOUR USERINFOBOT NUMBER INSIDE THESE QUOTES:
ALERT_CHAT_ID = "6832227515"

# Trigger percentage for automated background alerts (e.g., 5.0 = 5%)
PUMP_THRESHOLD_PERCENT = 5.0

# --- TIER 1: THE VIP RADAR LIST ---
# These are the coins the bot actively monitors 24/7 for automated pump alerts.
COIN_MAPPING = {
    "btc": "bitcoin",
    "eth": "ethereum",
    "sol": "solana",
    "bnb": "binancecoin",
    "xrp": "ripple",
    "wkc": "wiki-cat",
    "doge": "dogecoin",
    "shib": "shiba-inu",
    "pepe": "pepe"
}

PRICE_MEMORY = {}

# --- AUTOMATED PUMP DETECTOR ---
def pump_detector_loop():
    global PRICE_MEMORY
    print("🚨 Automated Pump Radar initialized and scanning...")
    time.sleep(10)
    while True:
        try:
            coin_ids = ",".join(COIN_MAPPING.values())
            url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_ids}&vs_currencies=usd"
            response = requests.get(url).json()
            
            for symbol, coin_id in COIN_MAPPING.items():
                if coin_id in response and "usd" in response[coin_id]:
                    current_price = response[coin_id]["usd"]
                    previous_price = PRICE_MEMORY.get(coin_id)
                    
                    if previous_price is not None:
                        price_change_pct = ((current_price - previous_price) / previous_price) * 100
                        if price_change_pct >= PUMP_THRESHOLD_PERCENT:
                            if current_price < 0.000001:
                                p_str = f"${current_price:.10f}"
                            elif current_price < 1.0:
                                p_str = f"${current_price:.6f}"
                            else:
                                p_str = f"${current_price:,} USD"
                                
                            alert_msg = (
                                f"🚨 **PUMP RADAR ALERT** 🚨\n\n"
                                f"🔥 **{symbol.upper()}** is skyrocketing!\n"
                                f"📈 **Growth:** +{price_change_pct:.2f}%\n"
                                f"💰 **Current Price:** {p_str}"
                            )
                            send_message(ALERT_CHAT_ID, alert_msg)
                    PRICE_MEMORY[coin_id] = current_price
        except Exception as e:
            print(f"Pump tracking error: {e}")
        time.sleep(300)

# --- KEEP ALIVE BACKGROUND TASK ---
def keep_alive_loop():
    time.sleep(20)
    while True:
        try: requests.get(RENDER_URL)
        except: pass
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
        requests.post(url, json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"})
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
                user_msg = text.lower()
                
                # 1. Welcome message when users hit "/start"
                if user_msg == "/start":
                    welcome_text = (
                        f"👋 **Welcome to the Advanced Crypto Radar Bot!**\n\n"
                        f"I am a cloud-hosted trading assistant designed to monitor market volatility.\n\n"
                        f"🛠 **Quick Start Guide:**\n"
                        f"• Type `/price btc` — Get live Bitcoin metrics\n"
                        f"• Type `/price wkc` — Get live WikiCat metrics\n"
                        f"• Type `/price <any_coin>` — Global search engine\n"
                        f"• Type `/help` — Re-open this operational manual\n\n"
                        f"--- \n"
                        f"👑 **Creator:** Built by [Gabe](https://t.me/gabe_tonic)\n"
                        f"📡 _System fully optimized for quick on-demand lookups._"
                    )
                    send_message(chat_id, welcome_text)
                
                # 2. Guide menu when users hit "/help"
                elif user_msg == "/help":
                    guide_text = (
                        f"📖 **Crypto Radar Operational Manual**\n\n"
                        f"To pull data instantly from the live pricing terminal, type your request using the format below:\n"
                        f"`/price <abbreviation>`\n\n"
                        f"📊 **System Capabilities:**\n"
                        f"• Global Search: Fetches any coin via direct search.\n"
                        f"• VIP Auto-Radar: Continuously tracks major chains in the background for sudden price pumps.\n\n"
                        f"--- \n"
                        f"👑 **Creator Support:** Contact [Gabe](https://t.me/gabe_tonic) for issues or feature requests."
                    )
                    send_message(chat_id, guide_text)
                
                # 3. TIER 2: Global Price Search Logic
                elif user_msg.startswith("/price"):
                    parts = text.split()
                    if len(parts) < 2:
                        send_message(chat_id, "💡 Please provide a coin abbreviation!\nExample: `/price btc` or `/price wkc`")
                        continue
                    
                    user_input = parts[1].lower()
                    
                    # First, check if it's in our VIP radar list
                    target_coin = COIN_MAPPING.get(user_input)
                    
                    try:
                        # If it's NOT in the VIP list, dynamically search the global database!
                        if not target_coin:
                            search_url = f"https://api.coingecko.com/api/v3/search?query={user_input}"
                            search_res = requests.get(search_url).json()
                            
                            # If the search finds a match, grab the exact ID
                            if search_res.get("coins") and len(search_res["coins"]) > 0:
                                target_coin = search_res["coins"][0]["id"]
                                actual_symbol = search_res["coins"][0]["symbol"]
                            else:
                                send_message(chat_id, f"⚠️ Could not find a coin matching '{user_input.upper()}'.")
                                continue
                        else:
                            actual_symbol = user_input.upper()

                        # Now fetch the actual price using the ID
                        url = f"https://api.coingecko.com/api/v3/simple/price?ids={target_coin}&vs_currencies=usd"
                        response = requests.get(url).json()
                        
                        if target_coin in response and "usd" in response[target_coin]:
                            price = response[target_coin]["usd"]
                            
                            # Smart formatting
                            if price < 0.000001:
                                price_str = f"${price:.10f}"
                            elif price < 1.0:
                                price_str = f"${price:.6f}"
                            else:
                                price_str = f"${price:,} USD"
                                
                            send_message(chat_id, f"💰 The current price of **{actual_symbol.upper()}** is {price_str}.")
                        else:
                            send_message(chat_id, f"⚠️ Could not pull price data for '{actual_symbol.upper()}'.")
                            
                    except Exception as e:
                        send_message(chat_id, "⚠️ Market server busy. Try again soon!")
                
                # 4. Fallback for unexpected messages
                else:
                    send_message(chat_id, "🤖 Commands unrecognized.\n\nUse `/start` to view the welcome layout or `/help` to view available tokens.")
        time.sleep(1)

@app.route("/")
def index():
    return "Global Search and Radar Engine Active!"

if __name__ == "__main__":
    threading.Thread(target=keep_alive_loop, daemon=True).start()
    threading.Thread(target=pump_detector_loop, daemon=True).start()
    threading.Thread(target=bot_loop, daemon=True).start()
    app.run(host="0.0.0.0", port=8080)
