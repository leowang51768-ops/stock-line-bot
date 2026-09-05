import os
import requests
import pandas as pd
import yfinance as yf

# 從 GitHub Secrets 讀取金鑰
LINE_ACCESS_TOKEN = 'dJ/nmm07oXD1DIrt9CVfEvkbkRF+cTKR0Nbm9cNGVmhjtcSLU6+USSDrpkY8mSARyPJyvazonGtwBMC2j8AelHYNgbKppzzVE8CJdkVWPfjhjr9REk8l17Ms39kNGhKnm4gsXAFXzxbl0vgcVtbQ0QdB04t89/1O/w1cDnyilFU='
LINE_USER_ID = 'Ucab8145cf7e5c1ee3e38ee2f58c1d46'


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
    # 觀察標的清單（上市使用 .TW，上櫃使用 .TWO）
    tickers = [
        '2330.TW',   # 台積電
        '5347.TWO',  # 世界
        '3711.TW',   # 日月光投控
        '6239.TW',   # 力成
        '3189.TW',   # 景碩
        '2449.TW',   # 京元電子
        '3131.TWO',  # 弘塑
        '3583.TW',   # 辛耘
        '3324.TWO',  # 雙鴻
        '3017.TW',   # 奇鋐
        '3338.TWO',  # 泰碩
        '2421.TW',   # 建準
        '4979.TWO',  # 華星光
        '4906.TW',   # 正文
        '3363.TWO',  # 上詮
        '6442.TW',   # 光聖
        '3081.TWO',  # 聯亞
        '3037.TW',   # 欣興
        '6669.TW',   # 緯穎
        '2382.TW'    # 廣達
    ]
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

            stock_name = ticker.replace('.TW', '').replace('.TWO', '')

            # Price Action 訊號判斷 1: 看漲吞噬 (Bullish Engulfing)
            if (prev['Close'] < prev['Open']) and (curr['Close'] > curr['Open']) and \
               (curr['Close'] >= prev['Open']) and (curr['Open'] <= prev['Close']):
                signals.append(f"🟢 {stock_name}：出現【看漲吞噬】訊號")

            # Price Action 訊號判斷 2: 破底翻 / 破前低收高 (Pinbar)
            elif (curr['Low'] < prev['Low']) and (curr['Close'] > prev['Close']):
                signals.append(f"🚀 {stock_name}：出現【破底翻/強勢拉回】訊號")

        except Exception as e:
            print(f"Error checking {ticker}: {e}")

    if signals:
        message = "📊 【Price Action 今日選股推播】\n\n" + "\n".join(signals)
    else:
        message = "📊 【Price Action 今日選股推播】\n\n今日無符合訊號之標的。"

    return message

if __name__ == '__main__':
    msg = check_price_action()
    status = send_line_message(msg)
    print(f"LINE Notification Status: {status}")
