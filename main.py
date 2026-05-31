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
API_KEY = "CG-6dMY9ZoDuzPb74dPCT7gu4VM"

# 🔍 Your UserInfoBot Chat ID:
ALERT_CHAT_ID = "6832227515"

# --- TIER 1: THE VIP RADAR LIST ---
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

# --- KEEP ALIVE LOGIC ---
def keep_alive_loop():
    print("📡 Keep-alive background pinger initialized...")
    while True:
        try:
            requests.get(RENDER_URL)
            print("🔄 Successfully pinged Render instance to maintain activity.")
        except Exception as e:
            print(f"Keep-alive ping warning: {e}")
        time.sleep(300) # Ping server every 5 minutes

# --- 24-HOUR SMART MARKET RADAR (Runs every 3 hours) ---
def pump_detector_loop():
    print("🚨 Smart Market Radar initialized...")
    time.sleep(10)
    
    while True:
        try:
            coin_ids = ",".join(COIN_MAPPING.values())
            # Targets the markets endpoint for structural 24h percentage changes using your key
            url = f"https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&ids={coin_ids}&x_cg_demo_api_key={API_KEY}"
            
            response = requests.get(url)
            data = response.json()
            
            report_lines = []
            
            for coin in data:
                symbol = coin.get('symbol', '').upper()
                price = coin.get('current_price', 0)
                change_24h = coin.get('price_change_percentage_24h', 0)
                
                if price is None:
                    continue
                
                # Ultra-clean decimal formatter accommodating micro-caps
                if price < 0.000001:
                    p_str = f"${price:.10f}"
                elif price < 1.0:
                    p_str = f"${price:.6f}"
                else:
                    p_str = f"${price:,} USD"
                
                # Visual indicators for tracking positive vs negative performance
                emoji = "🟢" if change_24h and change_24h >= 0 else "🔴"
                sign = "+" if change_24h and change_24h >= 0 else ""
                
                report_lines.append(f"{emoji} **{symbol}**: {p_str} ({sign}{change_24h:.2f}% 24h)")
            
            # Send ONE clean compiled summary layout instead of repetitive text bombs
            if report_lines:
                alert_msg = "🚨 **3-HOUR VIP RADAR UPDATE** 🚨\n\n" + "\n".join(report_lines)
                send_message(ALERT_CHAT_ID, alert_msg)
                
        except Exception as e:
            print(f"Radar Engine error: {e}")
            
        # Put the background script to sleep for exactly 3 hours (10800 seconds)
        time.sleep(10800)

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
                    target_coin = COIN_MAPPING.get(user_input)
                    
                    try:
                        # If NOT in VIP list, search global database with API key applied
                        if not target_coin:
                            search_url = f"https://api.coingecko.com/api/v3/search?query={user_input}&x_cg_demo_api_key={API_KEY}"
                            search_res = requests.get(search_url).json()
                            
                            if search_res.get("coins") and len(search_res["coins"]) > 0:
                                target_coin = search_res["coins"][0]["id"]
                                actual_symbol = search_res["coins"][0]["symbol"]
                            else:
                                send_message(chat_id, f"⚠️ Could not find a coin matching '{user_input.upper()}'.")
                                continue
                        else:
                            actual_symbol = user_input.upper()

                        # Pull live on-demand single price using API key
                        url = f"https://api.coingecko.com/api/v3/simple/price?ids={target_coin}&vs_currencies=usd&x_cg_demo_api_key={API_KEY}"
                        response = requests.get(url).json()
                        
                        if target_coin in response and "usd" in response[target_coin]:
                            price = response[target_coin]["usd"]
                            
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
                        send_message(chat_id, f"⚠️ Price fetch error. Try again soon!")
                
                # 4. Fallback for unexpected inputs
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
