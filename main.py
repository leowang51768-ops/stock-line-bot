import os
import requests
import pandas as pd
import yfinance as yf

# LINE 授權設定
LINE_ACCESS_TOKEN = 'dJ/nmm07oXD1DIrt9CVfEvkbkRF+cTKR0Nbm9cNGVmhjtcSLU6+USSDrpkY8mSARyPJyvazonGtwBMC2j8AelHYNgbKppzzVE8CJdkVWPfjhjr9REk8l17Ms39kNGhKnm4gsXAFXzxbl0vgcVtbQ0QdB04t89/1O/w1cDnyilFU='.strip()
LINE_USER_ID = 'Ucab8145cf7e5c1ee3e38ee2f58c1d46'.strip()

def send_line_message(msg):
    if not msg or str(msg).strip() == '':
        msg = "今日無符合策略之台股選股訊號。"

    url = 'https://api.line.me/v2/bot/message/push'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {LINE_ACCESS_TOKEN}'
    }
    payload = {
        'to': LINE_USER_ID,
        'messages': [{'type': 'text', 'text': str(msg)}]
    }
    response = requests.post(url, json=payload, headers=headers)
    print(f"LINE Notification Status: {response.status_code}")
    print(f"LINE Response Detail: {response.text}")
    return response.status_code

def analyze_breakout_strategy():
    """
    依據真假突破框架設計的簡易篩選示範：
    1. 抓取近期日K線
    2. 檢查是否符合突破前高且帶量、站得住的條件
    """
    # 示範觀察清單（可自行擴增台股代號，例如台積電 2330.TW, 聯發科 2454.TW 等）
    watchlist = ['2330.TW', '2317.TW', '2454.TW', '2308.TW']
    signals = []

    for ticker in watchlist:
        try:
            # 取得近 60 天日K資料
            df = yf.download(ticker, period='60d', interval='1d', progress=False)
            if df.empty or len(df) < 30:
                continue
            
            # 處理 MultiIndex 欄位問題（防止 yfinance 格式新舊差異報錯）
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            close = df['Close']
            volume = df['Volume']

            # 核心邏輯：突破近 20 日最高價（證據四：站得住、走得開），且當日成交量放大超過平均量
            recent_high = close.iloc[-21:-1].max()
            avg_volume = volume.iloc[-21:-1].mean()

            current_close = close.iloc[-1]
            current_vol = volume.iloc[-1]

            # 條件：今日收盤價突破前高 且 成交量放大 1.2 倍以上（具備量價效率）
            if current_close > recent_high and current_vol > (avg_volume * 1.2):
                signals.append(f"🔥 【突破訊號】{ticker}\n- 現價: {current_close:.2f}\n- 突破 20 日高點: {recent_high:.2f}\n- 量能放大確認")
        
        except Exception as e:
            print(f"Error processing {ticker}: {e}")

    # 組合最終推播訊息
    if signals:
        message = "📊 今日台股突破/破底翻策略掃描結果：\n\n" + "\n\n".join(signals)
    else:
        message = "📊 今日台股掃描完畢：無標的同時符合突破與量價效率條件。"

    return message

if __name__ == '__main__':
    # 執行策略分析並發送 LINE 推播
    stock_report = analyze_breakout_strategy()
    send_line_message(stock_report)
