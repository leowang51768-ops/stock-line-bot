import os
import requests
import pandas as pd
import yfinance as yf

# LINE 授權設定（已直接寫死）
LINE_ACCESS_TOKEN = 'dJ/nmm07oXD1DIrt9CVfEvkbkRF+cTKR0Nbm9cNGVmhjtcSLU6+USSDrpkY8mSARyPJyvazonGtwBMC2j8AelHYNgbKppzzVE8CJdkVWPfjhjr9REk8l17Ms39kNGhKnm4gsXAFXzxbl0vgcVtbQ0QdB04t89/1O/w1cDnyilFU='
LINE_USER_ID = 'Ucab8145cf7e5c1ee3e38ee2f58c1d46'

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

def check_price_action():
    # 測試發送通知
    message = "【台股選股通知】系統測試成功，LINE 推播連線正常！"
    send_line_message(message)

if __name__ == '__main__':
    check_price_action()
