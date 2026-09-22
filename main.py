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

    # 175 檔台股 AI 產業鏈完整監控清單 (含上市.TW與上櫃.TWO)
STOCK_LIST = [
    # 1. 矽晶圓與晶圓代工
    "2330.TW", "6488.TWO", "3532.TW", "6182.TWO", "2303.TW", "5347.TWO", "6770.TW",
    
    # 2. 矽智財 (IP) 與客製化晶片 (ASIC)
    "3661.TW", "3443.TW", "3529.TW", "3035.TW", "6643.TWO", "6533.TW", "6531.TW", "8227.TWO", "6462.TWO", "6684.TWO",
    
    # 3. 高速傳輸、BMC、記憶體與控制器
    "5274.TWO", "5269.TW", "4966.TWO", "8299.TWO", "2454.TW", "2379.TW", "2408.TW", "2344.TW", "6485.TWO", "4967.TW", "3260.TWO", "3006.TW",
    
    # 4. 先進封裝 (CoWoS/FOPLP)、OSAT 封測與檢測分析
    "3374.TWO", "6789.TW", "3711.TW", "2449.TW", "6239.TW", "6257.TW", "2441.TW", "3289.TWO", "3587.TWO", "6830.TW", "8150.TW", "8110.TW", "2369.TW",
    
    # 5. CoWoS 設備、再生晶圓與廠務工程
    "3131.TWO", "3583.TW", "6187.TWO", "2467.TW", "6640.TWO", "5443.TWO", "1560.TW", "8028.TW", "3580.TWO", "8064.TWO", "6139.TW", "2404.TW", "5536.TW", "6196.TW", "6667.TWO", "6829.TW",
    
    # 6. 測試介面、探針卡與晶圓載具
    "6223.TWO", "6515.TW", "6510.TWO", "3680.TW", "7556.TWO", "6781.TW", "3689.TWO",
    
    # 7. 矽光子 (CPO)、光通訊與高階網通
    "3081.TWO", "4979.TWO", "4977.TW", "3234.TWO", "3363.TWO", "3163.TWO", "6442.TW", "2360.TW", "2345.TW", "3380.TW", "4903.TWO", "6530.TWO", "3047.TW", "6451.TWO",
    
    # 8. 散熱模組、液冷系統與水冷零組件
    "3017.TW", "3324.TWO", "3653.TW", "2421.TW", "8996.TW", "6805.TW", "3483.TWO", "3338.TW", "6125.TW", "6230.TW", "3071.TW", "6275.TWO", "4566.TW", "1575.TW",
    
    # 9. 電源供應器、高功率 PSU 與電網重電設備
    "2308.TW", "2301.TW", "2385.TW", "6412.TW", "1519.TW", "1503.TW", "1513.TW", "1514.TW", "6282.TW", "3090.TW", "3032.TW", "3078.TWO", "6203.TWO", "3540.TW",
    
    # 10. 高階 CCL、銅箔、PCB 與 ABF 載板
    "2383.TW", "8383.TWO", "6213.TW", "3037.TW", "2368.TW", "8046.TW", "3189.TW", "3044.TW", "2313.TW", "4958.TW", "3715.TW", "5469.TW", "6191.TW", "2355.TW", "3686.TW", "6269.TW",
    
    # 11. 伺服器機殼、高階滑軌、高速線束與連接器
    "2059.TW", "6584.TWO", "8210.TW", "3013.TW", "3665.TW", "3533.TW", "3693.TWO", "6290.TWO", "3217.TWO", "6117.TW", "3325.TW", "5426.TW", "8103.TW", "3605.TW", "3526.TWO",
    
    # 12. 伺服器系統整合 (ODM/OEM) 與 Edge AI / 光學鏡頭 / 機器人
    "3008.TW", "3406.TW", "2382.TW", "6669.TW", "3231.TW", "2317.TW", "2356.TW", "4938.TW", "2376.TW", "2357.TW", "2377.TW", "3515.TW", "3706.TW", "6933.TW", "2395.TW", "6414.TW", "6166.TW", "5289.TWO", "2359.TW", "4585.TWO", "6215.TW", "2324.TW", "2312.TW"
]

    
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
