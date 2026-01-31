import os
import pandas as pd
import requests
from datetime import datetime

# =========================
# 환경 변수
# =========================
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

if not BOT_TOKEN or not CHAT_ID:
    raise ValueError("BOT_TOKEN 또는 CHAT_ID 환경 변수가 설정되지 않았습니다.")

# =========================
# 텔레그램 전송
# =========================
def send_telegram(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    response = requests.post(url, data={
        "chat_id": CHAT_ID,
        "text": text,
        "disable_web_page_preview": True
    })
    print("Telegram status:", response.status_code)
    print("Telegram response:", response.text)

# =========================
# 엑셀에서 90일 패턴 읽기
# =========================
def load_patterns(file_path="English_90Patterns_with_Korean.xlsx"):
    df = pd.read_excel(file_path)
    # 컬럼: Day, Pattern, Example, Korean
    return df

# =========================
# 오늘 발송할 3개 패턴 선택
# =========================
def get_today_patterns(df):
    # 현재 한국 시간 기준
    now = datetime.utcnow() + pd.Timedelta(hours=9)
    day_index = now.day % 90  # 1~90 패턴 반복
    # slice: 3개씩
    today_df = df.iloc[day_index*3 : day_index*3+3]
    return today_df

# =========================
# 메시지 생성
# =========================
def create_message(today_df):
    now = datetime.utcnow() + pd.Timedelta(hours=9)
    date_str = now.strftime("%Y-%m-%d (%H:%M) KST")

    msg = f"📚 English Pattern 90 Days\n🗓 {date_str}\n\n"

    for idx, row in today_df.iterrows():
        msg += f"📌 Pattern {row['Day']}: {row['Pattern']}\n"
        msg += f"✏ Example: {row['Example']}\n"
        msg += f"🇰🇷 한국어: {row['Korean']}\n\n"

    # 영어 작문 주제
    msg += "📝 Today Writing Topic: Describe your favorite hobby in English.\n"

    return msg

# =========================
# 메시지 분할 전송
# =========================
def send_message_safe(message):
    max_len = 4000  # 텔레그램 메시지 안전 길이
    for i in range(0, len(message), max_len):
        send_telegram(message[i:i+max_len])

# =========================
# MAIN
# =========================
def main():
    df = load_patterns()
    today_df = get_today_patterns(df)
    message = create_message(today_df)
    send_message_safe(message)

if __name__ == "__main__":
    main()
