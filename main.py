import os
import requests
import pandas as pd
import yfinance as yf
from datetime import datetime

# 從 GitHub Secrets 讀取金鑰
LINE_ACCESS_TOKEN = os.getenv('LINE_ACCESS_TOKEN')
LINE_USER_ID = os.getenv('LINE_USER_ID')

if not LINE_ACCESS_TOKEN:
    print("⚠️ 警告：未讀取到 LINE_ACCESS_TOKEN，請檢查 GitHub Actions 的 env 設定！")
else:
    print(f"✅ 成功讀取 Token (字串長度: {len(LINE_ACCESS_TOKEN)})")

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
    print(f"LINE API Response Status: {response.status_code}")
    print(f"LINE API Response Body: {response.text}")
    return response.status_code

def check_price_action():
    stocks_to_track = {
        '2330.TW': '台積電', '6669.TW': '緯穎', '2317.TW': '鴻海', '2382.TW': '廣達', '2454.TW': '聯發科',
        '3443.TW': '創意', '2449.TW': '京元電子', '2383.TW': '台光電', '3653.TW': '健策', '3008.TW': '大立光',
        '3661.TW': '世芯-KY', '3264.TWO': '欣銓', '3231.TW': '緯創', '3017.TW': '奇鋐', '2345.TW': '智邦',
        '6488.TWO': '環球晶', '5483.TWO': '中美晶', '3711.TW': '日月光投控', '2356.TW': '英業達', '2376.TW': '技嘉',
        '6274.TWO': '台燿', '2368.TW': '金像電', '8046.TW': '南電', '4958.TW': '臻鼎-KY', '6213.TW': '聯茂',
        '3037.TW': '欣興', '3481.TW': '群創', '3324.TWO': '雙鴻', '2421.TW': '建準', '2308.TW': '台達電',
        '2301.TW': '光寶科', '6282.TW': '康舒', '3665.TW': '貿聯-KY', '3533.TW': '嘉澤', '5388.TW': '中磊',
        '6285.TW': '啟碁', '4908.TWO': '前鼎', '3105.TWO': '穩懋', '3234.TWO': '光環', '4979.TWO': '華星光',
        '3163.TWO': '波若威', '4977.TW': '眾達-KY', '2408.TW': '南亞科', '2344.TW': '華邦電', '2337.TW': '旺宏',
        '3374.TWO': '精材', '6139.TW': '亞翔', '6187.TWO': '萬潤', '2049.TW': '上銀', '1590.TW': '亞德客-KY',
        '1504.TW': '東元', '2359.TW': '所羅門', '3022.TW': '威強電', '4576.TW': '大銀微系統', '2464.TW': '盟立',
        '3491.TWO': '昇達科', '8039.TW': '台虹', '8086.TWO': '宏捷科', '2634.TW': '漢翔', '8033.TW': '雷虎',
        '2324.TW': '仁寶', '6781.TW': 'AES-KY', '3211.TWO': '順達', '4931.TWO': '新盛力', '8271.TW': '宇瞻',
        '4967.TWO': '十銓', '2313.TW': '華通', '8358.TWO': '金居', '3680.TWO': '家登', '3583.TW': '辛耘'
    }
    
    engulfing_signals = []
    spring_signals = []
    tickers = list(stocks_to_track.keys())
    
    print("⏳ 正在批次下載股價與成交量資料...")
    try:
        data = yf.download(tickers, period='6d', group_by='ticker', threads=True, progress=False)
    except Exception as e:
        print(f"❌ 批次下載失敗: {e}")
        return f"📊 【Price Action 選股推播】\n\n系統下載資料發生異常。"

    for ticker, stock_name in stocks_to_track.items():
        try:
            df = data[ticker].dropna()
            if len(df) < 6: # 需要至少 6 天來計算 5 日均量
                continue

            prev = df.iloc[-2]
            curr = df.iloc[-1]
            pure_code = ticker.split('.')[0]
            
            # 計算前 5 日平均成交量（不含今天）
            avg_volume_5d = df['Volume'].iloc[-6:-1].mean()
            # 判斷今天是否帶量（成交量大於 5 日均量）
            is_volume_up = curr['Volume'] > avg_volume_5d

            # 1. 看漲吞噬（加上成交量過濾：需帶量或至少成交量放大）
            if (prev['Close'] < prev['Open']) and (curr['Close'] > curr['Open']) and \
               (curr['Close'] >= prev['Open']) and (curr['Open'] <= prev['Close']) and is_volume_up:
                engulfing_signals.append(f"• {stock_name} ({pure_code})")

            # 2. 破底翻 / 強勢拉回（加上成交量過濾：需帶量收紅）
            elif (curr['Low'] < prev['Low']) and (curr['Close'] > curr['Open']) and \
                 (curr['Close'] > prev['Close']) and is_volume_up:
                spring_signals.append(f"• {stock_name} ({pure_code})")

        except Exception as e:
            print(f"⚠️ 處理 {ticker} ({stock_name}) 時發生錯誤: {e}")
            pass

    today_str = datetime.now().strftime('%Y-%m-%d')
    message = f"📊 【Price Action 盤後篩選】\n📅 日期：{today_str}\n追蹤標的：{len(stocks_to_track)} 檔\n━━━━━━━━━━━━━━━\n"

    if engulfing_signals:
        message += f"\n🟢 【看漲吞噬 (帶量)】 (共 {len(engulfing_signals)} 檔)\n" + "\n".join(engulfing_signals) + "\n"
    
    if spring_signals:
        message += f"\n🚀 【破底翻/強勢拉回 (帶量)】 (共 {len(spring_signals)} 檔)\n" + "\n".join(spring_signals) + "\n"

    if not engulfing_signals and not spring_signals:
        message += "\n今日無符合「帶量突破」條件之標的。"

    return message

if __name__ == '__main__':
    msg = check_price_action()
    print(msg)
    status = send_line_message(msg)
    print(f"LINE Notification Status: {status}")
