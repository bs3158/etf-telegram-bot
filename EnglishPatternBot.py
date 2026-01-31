import pandas as pd
from datetime import datetime
import os
import requests

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

def send_telegram(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={
        "chat_id": CHAT_ID,
        "text": text,
        "disable_web_page_preview": True
    })

# 엑셀 불러오기
df = pd.read_excel("English_90Patterns_with_Korean.xlsx", dtype=str)

def get_today_patterns(df):
    now = datetime.utcnow() + pd.Timedelta(hours=9)
    day_number = (now.day - 1) % 90 + 1  # 1~90 Day
    df_sorted = df.sort_values(by="Day")
    today_df = df_sorted[df_sorted["Day"] == str(day_number)]
    # 한 Day에 3개가 없으면 다음 Day에서 채우기
    if len(today_df) < 3:
        needed = 3 - len(today_df)
        next_rows = df_sorted[df_sorted["Day"] == str((day_number % 90) + 1)]
        today_df = pd.concat([today_df, next_rows.head(needed)], ignore_index=True)
    return today_df, day_number

def build_message():
    today_df, day_number = get_today_patterns(df)
    now = datetime.utcnow() + pd.Timedelta(hours=9)
    msg = f"📚 English Pattern 90 Days\n🗓 {now.strftime('%Y-%m-%d (%H:%M)')} KST\n\n"
    for idx, row in today_df.iterrows():
        msg += f"📌 Pattern {row['Pattern']} : {row['English']}\n"
        msg += f"✏ Example: {row['Example']}\n"
        msg += f"🇰🇷 한국어: {row['Korean']}\n\n"
    msg += "📝 Today Writing Topic: Describe your favorite hobby in English."
    return msg

if __name__ == "__main__":
    message = build_message()
    send_telegram(message)
