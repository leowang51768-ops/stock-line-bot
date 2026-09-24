import os
import requests
import datetime
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime

# 從 GitHub Secrets 讀取金鑰
LINE_ACCESS_TOKEN = os.getenv('LINE_ACCESS_TOKEN')
LINE_USER_ID = os.getenv('LINE_USER_ID')

def get_tick_size(price: float) -> float:
    """根據台股升降單位 (Tick Size) 規則計算單一 Tick 價值"""
    if price < 10:
        return 0.01
    elif price < 50:
        return 0.05
    elif price < 100:
        return 0.1
    elif price < 500:
        return 0.5
    elif price < 1000:
        return 1.0
    else:
        return 5.0

def calculate_precise_stop_loss(df_40: pd.DataFrame, window: int = 15) -> tuple:
    """
    計算【多次重複跌不下去的頸線】與【下退 2 Ticks 的精準停損價】
    """
    recent_df = df_40.tail(window).copy()
    lows = recent_df['Low'].values
    current_price = float(recent_df['Close'].iloc[-1])
    tick = get_tick_size(current_price)
    
    # 尋找近 window 日內，相差在 2 個 Tick 之內且多次測試不破的低點區間
    sorted_lows = sorted(lows)
    neckline_price = None
    
    for i in range(len(sorted_lows) - 1):
        if abs(sorted_lows[i+1] - sorted_lows[i]) <= (2 * tick):
            # 取較低者作為多次重複跌不下去的強支撐頸線
            neckline_price = float(sorted_lows[i])
            break
            
    # 若無明顯多次重覆測試，則取近 N 日絕對最低點作為支撐
    if neckline_price is None:
        neckline_price = float(min(lows))
        
    # 精準停損價：防守牆下方扣除 2 個 Ticks 的容錯誤差，避免被假跌破洗盤
    stop_loss_price = neckline_price - (2 * tick)
    
    return round(neckline_price, 2), round(stop_loss_price, 2)

def send_line_messages(msg_list):
    """一次發送多則訊息（LINE Bot API 支援單次最多 5 則，並處理單則 5000 字限制）"""
    if not LINE_ACCESS_TOKEN or not LINE_USER_ID:
        print("⚠️ 缺少 LINE Token 或 User ID，跳過 LINE 發送步驟。")
        return 0

    url = 'https://api.line.me/v2/bot/message/push'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {LINE_ACCESS_TOKEN}'
    }
    
    final_messages = msg_list[:5]
    messages_payload = [{'type': 'text', 'text': m[:4500]} for m in final_messages]
    
    payload = {
        'to': LINE_USER_ID,
        'messages': messages_payload
    }
    
    response = requests.post(url, json=payload, headers=headers)
    print(f"LINE API Response Status: {response.status_code}")
    return response.status_code

def check_market_trend():
    """檢查大盤 (^TWII) 當天表現與漲跌幅"""
    try:
        market = yf.Ticker('^TWII')
        df_market = market.history(period='10d')
        
        # 修正：去除時區並截斷至 2026-09-24 23:59:59
        if df_market.index.tz is not None:
            df_market.index = df_market.index.tz_localize(None)
        df_market = df_market[df_market.index <= '2026-09-24 23:59:59']

        if len(df_market) < 2:
            return 0.0, "中性"
        
        prev_close = df_market['Close'].iloc[-2]
        curr_close = df_market['Close'].iloc[-1]
        market_chg = (curr_close - prev_close) / prev_close * 100
        
        return round(market_chg, 2), "正常"
    except Exception as e:
        print(f"⚠️ 取得大盤資訊失敗: {e}")
        return 0.0, "異常"

# 175 檔台股 AI 產業鏈完整監控清單
STOCKS_TO_TRACK = {
    # 1. 矽晶圓與晶圓代工
    "2330.TW": "台積電", "6488.TWO": "環球晶", "3532.TW": "台勝科", "6182.TWO": "合晶", 
    "2303.TW": "聯電", "5347.TWO": "世界先進", "6770.TW": "力積電",
    
    # 2. 矽智財 (IP) 與客製化晶片 (ASIC)
    "3661.TW": "世芯-KY", "3443.TW": "創意", "3529.TW": "力旺", "3035.TW": "智原", 
    "6643.TWO": "M31", "6533.TW": "晶心科", "6531.TW": "愛普*", "8227.TWO": "巨有科技", 
    "6462.TWO": "神盾", "6684.TWO": "安格",
    
    # 3. 高速傳輸、BMC、記憶體與控制器
    "5274.TWO": "信驊", "5269.TW": "祥碩", "4966.TWO": "譜瑞-KY", "8299.TWO": "群聯", 
    "2454.TW": "聯發科", "2379.TW": "瑞昱", "2408.TW": "南亞科", "2344.TW": "華邦電", 
    "6485.TWO": "點序", "4967.TW": "十銓", "3260.TWO": "威剛", "3006.TW": "晶豪科",
    
    # 4. 先進封裝 (CoWoS/FOPLP)、OSAT 封測與檢測分析
    "3374.TWO": "精材", "6789.TW": "采鈺", "3711.TW": "日月光投控", "2449.TW": "京元電子", 
    "6239.TW": "力成", "6257.TW": "矽格", "2441.TW": "超豐", "3289.TWO": "宜特", 
    "3587.TWO": "閎康", "6830.TW": "汎銓", "8150.TW": "南茂", "8110.TW": "華東", "2369.TW": "菱生",
    
    # 5. CoWoS 設備、再生晶圓與廠務工程
    "3131.TWO": "弘塑", "3583.TW": "辛耘", "6187.TWO": "萬潤", "2467.TW": "志聖", 
    "6640.TWO": "均華", "5443.TWO": "均豪", "1560.TW": "中砂", "8028.TW": "昇陽半導體", 
    "3580.TWO": "友威科", "8064.TWO": "東捷", "6139.TW": "亞翔", "2404.TW": "漢唐", 
    "5536.TW": "聖暉*", "6196.TW": "帆宣", "6667.TWO": "信紘科", "6829.TW": "千附精密",
    
    # 6. 測試介面、探針卡與晶圓載具
    "6223.TWO": "旺矽", "6515.TW": "穎崴", "6510.TWO": "精測", "3680.TW": "家登", 
    "7556.TWO": "意德士", "6781.TW": "華景電", "3689.TWO": "湧德",
    
    # 7. 矽光子 (CPO)、光通訊與高階網通
    "3081.TWO": "聯亞", "4979.TWO": "華星光", "4977.TW": "眾達-KY", "3234.TWO": "光環", 
    "3363.TWO": "上詮", "3163.TWO": "波若威", "6442.TW": "光聖", "2360.TW": "致茂", 
    "2345.TW": "智邦", "3380.TW": "明泰", "4903.TWO": "聯光通", "6530.TWO": "創威", 
    "3047.TW": "訊舟", "6451.TWO": "統新",
    
    # 8. 散熱模組、液冷系統與水冷零組件
    "3017.TW": "奇鋐", "3324.TWO": "雙鴻", "3653.TW": "健策", "2421.TW": "建準", 
    "8996.TW": "高力", "6805.TW": "富世達", "3483.TWO": "力致", "3338.TW": "泰碩", 
    "6125.TW": "廣運", "6230.TW": "尼得科超眾", "3071.TW": "協禧", "6275.TWO": "元山", 
    "4566.TW": "時碩工業", "1575.TW": "勝一",
    
    # 9. 電源供應器、高功率 PSU 與電網重電設備
    "2308.TW": "台達電", "2301.TW": "光寶科", "2385.TW": "群光", "6412.TW": "群電", 
    "1519.TW": "華城", "1503.TW": "士電", "1513.TW": "中興電", "1514.TW": "亞力", 
    "6282.TW": "康舒", "3090.TW": "全漢", "3032.TW": "偉訓", "3078.TWO": "僑威", 
    "6203.TWO": "海韻電", "3540.TW": "曜越",
    
    # 10. 高階 CCL、銅箔、PCB 與 ABF 載板
    "2383.TW": "台光電", "8383.TWO": "金居", "6213.TW": "台燿", "3037.TW": "欣興", 
    "2368.TW": "金像電", "8046.TW": "南電", "3189.TW": "景碩", "3044.TW": "健鼎", 
    "2313.TW": "華通", "4958.TW": "臻鼎-KY", "3715.TW": "定穎投控", "5469.TW": "瀚宇博", 
    "6191.TW": "精成科", "2355.TW": "敬鵬", "3686.TW": "榮科", "6269.TW": "台郡",
    
    # 11. 伺服器機殼、高階滑軌、高速線束與連接器
    "2059.TW": "川湖", "6584.TWO": "南俊國際", "8210.TW": "勤誠", "3013.TW": "晟銘電", 
    "3665.TW": "貿聯-KY", "3533.TW": "嘉澤", "3693.TWO": "營邦", "6290.TWO": "良維", 
    "3217.TWO": "優群", "6117.TW": "迎廣", "3325.TW": "旭品", "5426.TW": "振發", 
    "8103.TW": "瀚荃", "3605.TW": "宏致", "3526.TWO": "凡甲",
    
    # 12. 伺服器系統整合 (ODM/OEM) 與 Edge AI / 光學鏡頭 / 機器人
    "3008.TW": "大立光", "3406.TW": "玉晶光", "2382.TW": "廣達", "6669.TW": "緯穎", 
    "3231.TW": "緯創", "2317.TW": "鴻海", "2356.TW": "英業達", "4938.TW": "和碩", 
    "2376.TW": "技嘉", "2357.TW": "華碩", "2377.TW": "微星", "3515.TW": "華擎", 
    "3706.TW": "神達", "6933.TW": "AMAX-KY", "2395.TW": "研華", "6414.TW": "樺漢", 
    "6166.TW": "凌華", "5289.TWO": "宜鼎", "2359.TW": "所羅門", "4585.TWO": "達明", 
    "6215.TW": "和椿", "2324.TW": "仁寶", "2312.TW": "金寶"
}

def generate_stock_report():
    market_chg, market_status = check_market_trend()
    print(f"📈 今日大盤漲跌幅: {market_chg}%")

    signals_list = []
    tickers = list(STOCKS_TO_TRACK.keys())
    
    print("⏳ 正在批次下載 60 日技術面資料...")
    try:
        data = yf.download(tickers, period='60d', group_by='ticker', threads=True, progress=False)
    except Exception as e:
        print(f"❌ 批次下載失敗: {e}")
        return ["📊 【Price Action 選股推播】\n\n系統下載資料發生異常。"]

    for ticker, stock_name in STOCKS_TO_TRACK.items():
        try:
            if len(tickers) == 1:
                df = data.dropna()
            else:
                if ticker not in data or data[ticker].empty:
                    continue
                df = data[ticker].dropna()

            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            # -------------------------------------------------------------
            # 【修正】移除時區並精確過濾至 2026-09-24 當天 23:59:59 包含當天數據
            if df.index.tz is not None:
                df.index = df.index.tz_localize(None)
            df = df[df.index <= '2026-09-24 23:59:59']
            # -------------------------------------------------------------

            if len(df) < 40:
                continue

            df = df.sort_index(ascending=True)
            df_40 = df.iloc[-40:].copy()
            pure_code = ticker.split('.')[0]

            # 計算 5 日均線與 5 日均量
            df_40['MA5'] = df_40['Close'].rolling(window=5).mean()
            df_40['Vol_MA5'] = df_40['Volume'].rolling(window=5).mean()

            latest = df_40.iloc[-1]
            prev_1 = df_40.iloc[-2]

            d1_5 = df_40.iloc[-5:]
            d6_40 = df_40.iloc[-40:-5]

            curr_close = float(latest['Close'])
            curr_vol = float(latest['Volume'])
            ma5_vol = float(latest['Vol_MA5'])
            
            pct_change = (curr_close - float(prev_1['Close'])) / float(prev_1['Close']) * 100
            vol_ratio = curr_vol / ma5_vol if ma5_vol > 0 else 1.0

            # =========================================================
            # 【第一階段：1~5 天硬條件】（嚴格量價扣板機）
            # =========================================================
            
            # 1. 嚴格量能：成交量 >= 1000 張，且大於 5MA 均量 1.3 倍
            cond_vol = (curr_vol >= 1000) and (curr_vol > ma5_vol * 1.3)
            
            # 2. 均線與實體：站上 5MA，實體漲幅 >= 1.0%
            cond_ma5 = curr_close > float(latest['MA5'])
            body_pct = (curr_close - float(latest['Open'])) / float(latest['Open']) * 100
            is_real_body = body_pct >= 1.0

            # 3. 看漲吞噬：今日長紅包覆昨黑棒，且當日漲幅 >= 2.0%
            is_bullish_engulfing = is_real_body and \
                                   (float(prev_1['Close']) < float(prev_1['Open'])) and \
                                   (curr_close >= float(prev_1['Open'])) and \
                                   (float(latest['Open']) <= float(prev_1['Close'])) and \
                                   (pct_change >= 2.0)

            # 4. 真·破底翻：前2-5天創下近 20 天新低，今日帶量大漲突破前高（漲幅 >= 2.5%）
            low_20d = float(df_40['Low'].iloc[-20:].min())
            min_low_in_5d = float(d1_5['Low'].min())
            
            is_spring = is_real_body and \
                        (curr_close > float(prev_1['High'])) and \
                        (pct_change >= 2.5) and \
                        (min_low_in_5d == low_20d)

            has_trigger = is_bullish_engulfing or is_spring

            # 硬門檻過濾
            if not (cond_ma5 and cond_vol and has_trigger):
                continue

            # =========================================================
            # 【第二階段：6~40 天軟條件】（VCP 與結構標註）
            # =========================================================
            tags = []

            # VCP 波動收縮結構
            part1 = df_40.iloc[-40:-15]
            part2 = df_40.iloc[-15:-1]

            vol_p1 = (float(part1['High'].max()) - float(part1['Low'].min())) / float(part1['Low'].min())
            vol_p2 = (float(part2['High'].max()) - float(part2['Low'].min())) / float(part2['Low'].min())

            if (vol_p2 < vol_p1 * 0.7) and (vol_p1 < 0.35):
                tags.append("🔥 VCP波動收縮")

            # 箱型沉澱突破
            range_6_40 = (float(d6_40['High'].max()) - float(d6_40['Low'].min())) / float(d6_40['Low'].min())
            if range_6_40 < 0.15:
                tags.append("📦 箱型沉澱突破")

            if not tags:
                tags.append("⚡ 短線強勢爆量")

            triggers = []
            breakthrough_price = float(prev_1['High'])
            
            if is_bullish_engulfing: 
                triggers.append("看漲吞噬")
                breakthrough_price = float(prev_1['High'])
                
            if is_spring: 
                triggers.append("破底翻")
                breakthrough_price = float(prev_1['High'])

            tag_text = " | ".join(tags)
            trigger_text = "/".join(triggers)

            # =========================================================
            # 【第三階段：計算 1-3 條關鍵頸線 與 多次測試不破精準停損價】
            # =========================================================
            
            # 計算精準防守頸線與下退 2 個 Tick 停損價
            neckline_price, stop_loss_price = calculate_precise_stop_loss(df_40, window=15)
            
            # 抓取過去 60 日的高點分佈，抓出 1~3 條關鍵頸線
            recent_highs = df['High'].iloc[-60:]
            p75 = float(np.percentile(recent_highs, 75))
            p85 = float(np.percentile(recent_highs, 85))
            p95 = float(np.percentile(recent_highs, 95))
            
            raw_necks = [p75, p85, p95]
            unique_necks = []
            for n in sorted(raw_necks):
                if not unique_necks or abs(n - unique_necks[-1]) > (curr_close * 0.015):
                    unique_necks.append(round(n, 1))
            
            neck_str = " / ".join([str(n) for n in unique_necks[:3]])

            # 組裝個股回報訊息
            stock_info = (
                f"▪ {stock_name} ({pure_code})\n"
                f"  💰 {curr_close:.1f}元 | 漲幅 {pct_change:+.2f}% | 量增 {vol_ratio:.1f}倍\n"
                f"  🎯 今日突破價：{breakthrough_price:.1f}\n"
                f"  ⚔️ 關鍵頸線(1~3條)：{neck_str}\n"
                f"  🛡️ 多次防守頸線：{neckline_price:.1f}\n"
                f"  🛑 精準防守停損：{stop_loss_price:.1f} (跌破-2Ticks離場)\n"
                f"  💡 訊號：{trigger_text} ({tag_text})"
            )
            signals_list.append(stock_info)

        except Exception as e:
            print(f"⚠️ 處理 {ticker} ({stock_name}) 時發生錯誤: {e}")
            pass

    test_date_str = "2026-09-24"
    
    # 訊息第一則：大盤看板與風控狀態
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
        f"📅 日期：{test_date_str}\n"
        f"📈 加權指數：{market_chg:+.2f}%\n"
        f"----------------------------------\n"
        f"{market_warning}"
    )

    # 訊息第二則：個股篩選清單與統計
    if signals_list:
        signals_body = "\n\n".join(signals_list)
    else:
        signals_body = "☕ 今日無符合【1-5天嚴格觸發+站上5MA】之標的，保持耐心觀望。"

    msg_part2 = (
        f"📋 【精選觸發個股明細】(共 {len(signals_list)} 檔)\n"
        f"----------------------------------\n\n"
        f"{signals_body}\n\n"
        f"----------------------------------\n"
        f"🔍 追蹤標的總數：{len(STOCKS_TO_TRACK)} 檔\n"
        f"🛡️ 策略提醒：跌破『精準防守停損』或破 5 日線即刻執行紀律停損。"
    )

    return [msg_part1, msg_part2]

if __name__ == '__main__':
    messages = generate_stock_report()
    for m in messages:
        print(m)
        print("="*30)
    status = send_line_messages(messages)
    print(f"LINE Notification Status: {status}")
