import os
import requests
import pandas as pd
import yfinance as yf

# 從 GitHub Secrets 讀取金鑰
LINE_ACCESS_TOKEN = os.getenv('LINE_ACCESS_TOKEN')
LINE_USER_ID = os.getenv('LINE_USER_ID')

def send_line_message(msg):
    url = 'https://api.line.me/v2/bot/message/push'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {LINE_ACCESS_TOKEN}'
    }
    payload = {
        'to': LINE_USER_ID,
        'messages': [{'type': 'text', 'text': msg}]
    }
    response = requests.post(url, json=payload, headers=headers)
    return response.status_code

def check_price_action():
    # 觀察標的清單（台積電、鴻海、聯發科、台達電、啟碁）
    tickers = ['2330.TW', '2317.TW', '2454.TW', '2308.TW', '6285.TW']
    signals = []

    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            df = stock.history(period='5d')
            if len(df) < 2:
                continue
            
            # 取最近兩日 K 線資料
            prev = df.iloc[-2]
            curr = df.iloc[-1]
            
            stock_name = ticker.replace('.TW', '')
            
            # Price Action 訊號判斷 1: 看漲吞噬 (Bullish Engulfing)
            if (prev['Close'] < prev['Open']) and (curr['Close'] > curr['Open']) and \
               (curr['Close'] >= prev['Open']) and (curr['Open'] <= prev['Close']):
                signals.append(f"🟢 {stock_name}：出現【看漲吞噬】訊號")
                
            # Price Action 訊號判斷 2: 破底翻 / 破前低收高 (Pinbar)
            elif (curr['Low'] < prev['Low']) and (curr['Close'] > prev['Close']):
                signals.append(f"🚀 {stock_name}：出現【破底翻/強勢收復】訊號")
                
        except Exception as e:
            print(f"Error checking {ticker}: {e}")

    if signals:
        message = "📊 【Price Action 今日選股推播】\n\n" + "\n".join(signals)
    else:
        message = "📊 【Price Action 今日選股推播】\n\n今日重點標的未出現符合的裸 K 突破訊號，保持觀望。"
        
    return message

if __name__ == '__main__':
    msg = check_price_action()
    status = send_line_message(msg)
    print(f"LINE Notification Status: {status}")
