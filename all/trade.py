import yfinance as yf
import pandas as pd
import requests
import time
from datetime import datetime, timezone

# --- CONFIGURATION ---
TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
CHAT_ID = "YOUR_TELEGRAM_CHAT_ID"
SYMBOLS = ["GC=F", "EURUSD=X"] 

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print(f"Error sending Telegram: {e}")

def get_signal(symbol):
    try:
        # 1. Fetch Data with strict error handling
        data = yf.download(symbol, period="7d", interval="15m", progress=False, auto_adjust=True)
        
        # Check if data actually arrived
        if data is None or data.empty or len(data) < 200:
            return None

        # Fix potential multi-index headers
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)

        # --- CALCULATIONS ---
        data['EMA_200'] = data['Close'].ewm(span=200, adjust=False).mean()
        
        delta = data['Close'].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        avg_gain = gain.rolling(window=14).mean()
        avg_loss = loss.rolling(window=14).mean()
        rs = avg_gain / avg_loss
        data['RSI'] = 100 - (100 / (1 + rs))
        
        # 2. Extract Values
        last_price = float(data['Close'].iloc[-1])
        last_rsi = float(data['RSI'].iloc[-1])
        ema_200 = float(data['EMA_200'].iloc[-1])
        
        # 3. Time Filter
        current_hour = datetime.now(timezone.utc).hour
        is_prime_time = 12 <= current_hour <= 18 

        # --- DEBUG PRINT (So you can see it's working) ---
        print(f"[{symbol}] Price: {last_price:.2f} | RSI: {last_rsi:.2f} | Trend: {'UP' if last_price > ema_200 else 'DOWN'}")

        # --- SIGNAL LOGIC ---
        if is_prime_time:
            if last_price < ema_200 and last_rsi > 70:
                return f"🚨 *SELL* 🚨\nAsset: {symbol}\nPrice: {last_price:.4f}"
            elif last_price > ema_200 and last_rsi < 30:
                return f"✅ *BUY* ✅\nAsset: {symbol}\nPrice: {last_price:.4f}"
        
        return None

    except Exception as e:
        print(f"⚠️ Calculation Error for {symbol}: {e}")
        return None

print("🚀 Bot Active. Monitoring Markets...")

while True:
    for ticker in SYMBOLS:
        signal = get_signal(ticker)
        if signal:
            print(f"!!! SIGNAL FOUND FOR {ticker} !!!")
            send_telegram(signal)
    
    # Wait 5 minutes
    time.sleep(300)