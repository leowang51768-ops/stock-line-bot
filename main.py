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

def send_line_messages(msg_list):
    """一次發送多則訊息（LINE Bot API 支援單次最多 5 則）"""
    url = 'https://api.line.me/v2/bot/message/push'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {LINE_ACCESS_TOKEN}'
    }
    messages_payload = [{'type': 'text', 'text': m} for m in msg_list]
    payload = {
        'to': LINE_USER_ID,
        'messages': messages_payload
    }
    response = requests.post(url, json=payload, headers=headers)
    print(f"LINE API Response Status: {response.status_code}")
    print(f"LINE API Response Body: {response.text}")
    return response.status_code

def check_market_trend():
    """檢查大盤 (^TWII) 當天表現與漲跌幅"""
    try:
        market = yf.Ticker('^TWII')
        df_market = market.history(period='2d')
        if len(df_market) < 2:
            return 0.0, "中性"
        
        prev_close = df_market['Close'].iloc[-2]
        curr_close = df_market['Close'].iloc[-1]
        market_chg = (curr_close - prev_close) / prev_close * 100
        
        return round(market_chg, 2), "正常"
    except Exception as e:
        print(f"⚠️ 取得大盤資訊失敗: {e}")
        return 0.0, "異常"

def generate_stock_report():
    market_chg, market_status = check_market_trend()
    print(f"📈 今日大盤漲跌幅: {market_chg}%")

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
        return ["📊 【Price Action 選股推播】\n\n系統下載資料發生異常。"]

    for ticker, stock_name in stocks_to_track.items():
        try:
            df = data[ticker].dropna()
            if len(df) < 6:
                continue

            prev = df.iloc[-2]
            curr = df.iloc[-1]
            pure_code = ticker.split('.')[0]
            
            curr_close = curr['Close']
            pct_change = (curr_close - prev['Close']) / prev['Close'] * 100
            
            avg_volume_5d = df['Volume'].iloc[-6:-1].mean()
            vol_ratio = curr['Volume'] / avg_volume_5d if avg_volume_5d > 0 else 1.0
            is_volume_up = curr['Volume'] > avg_volume_5d

            # 1. 看漲吞噬
            if (prev['Close'] < prev['Open']) and (curr['Close'] > curr['Open']) and \
               (curr['Close'] >= prev['Open']) and (curr['Close'] <= prev['Open']) and is_volume_up:
                line_str = f"▪ {stock_name} ({pure_code})\n  💰 {curr_close:.1f}元 | 漲幅 {pct_change:+.2f}% | 量增 {vol_ratio:.1f}倍\n  💡 特性：帶量吞噬 (參考勝率 ~58%)"
                engulfing_signals.append(line_str)

            # 2. 破底翻 / 強勢拉回
            elif (curr['Low'] < prev['Low']) and (curr['Close'] > curr['Open']) and \
                 (curr['Close'] > prev['Close']) and is_volume_up:
                line_str = f"▪ {stock_name} ({pure_code})\n  💰 {curr_close:.1f}元 | 漲幅 {pct_change:+.2f}% | 量增 {vol_ratio:.1f}倍\n  💡 特性：破底翻揚 (參考勝率 ~56%)"
                spring_signals.append(line_str)

        except Exception as e:
            print(f"⚠️ 處理 {ticker} ({stock_name}) 時發生錯誤: {e}")
            pass

    today_str = datetime.now().strftime('%Y-%m-%d')
    
    # 訊息第一則：大盤看板與風控狀態
    market_warning = ""
    if market_chg <= -1.5:
        market_warning = "🚨 【風控注意】大盤重挫逾 1.5%，系統性風險高，建議縮小部位或暫緩多方進場。"
    elif market_chg < 0:
        market_warning = "⚠️ 【盤勢提醒】大盤震盪收黑，操作請嚴設停損。"
    else:
        market_warning = "🟢 【盤勢狀態】大盤穩健，有利順勢多方操作。"

    msg_part1 = (
        f"╔══════════════════╗\n"
        f"  📊 Price Action 盤後策略看板\n"
        f"╚══════════════════╝\n"
        f"📅 日期：{today_str}\n"
        f"📈 加權指數：{market_chg:+.2f}%\n"
        f"----------------------------------\n"
        f"{market_warning}"
    )

    # 訊息第二則：個股篩選清單與統計
    msg_part2_body = []
    if engulfing_signals:
        msg_part2_body.append(f"🟢 【看漲吞噬訊號】(共 {len(engulfing_signals)} 檔)\n\n" + "\n\n".join(engulfing_signals))
    
    if spring_signals:
        msg_part2_body.append(f"🚀 【破底翻/強勢拉回】(共 {len(spring_signals)} 檔)\n\n" + "\n\n".join(spring_signals))

    if not engulfing_signals and not spring_signals:
        msg_part2_body.append("☕ 今日無符合嚴格量價條件之標的，保持耐心觀望。")

    msg_part2 = (
        f"📋 【篩選結果明細】\n"
        f"----------------------------------\n\n" +
        "\n\n".join(msg_part2_body) +
        f"\n\n----------------------------------\n"
        f"🔍 追蹤標的總數：{len(stocks_to_track)} 檔"
    )

    return [msg_part1, msg_part2]

if __name__ == '__main__':
    messages = generate_stock_report()
    for m in messages:
        print(m)
        print("="*30)
    status = send_line_messages(messages)
    print(f"LINE Notification Status: {status}")
