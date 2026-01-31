import os
import pandas as pd
import datetime
import requests
import random

# =========================
# 환경 변수
# =========================
BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

# =========================
# 텔레그램 전송 함수
# =========================
def send_telegram(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={
        "chat_id": CHAT_ID,
        "text": text,
        "disable_web_page_preview": True
    })

# =========================
# 엑셀 데이터 로드
# =========================
EXCEL_FILE = "English_90Patterns_with_Korean.xlsx"
df = pd.read_excel(EXCEL_FILE)

# =========================
# 날짜 기반 Day 계산 (1~90)
# =========================
def get_today_day(start_date="2026-01-31"):
    start = datetime.datetime.strptime(start_date, "%Y-%m-%d")
    today = datetime.datetime.now()
    delta = (today - start).days
    day = (delta % 90) + 1  # 1~90 반복
    return day

# =========================
# 혼자 영어 작문 주제 예시
# =========================
WRITING_TOPICS = [
    "Write about your favorite hobby.",
    "Describe your dream vacation.",
    "Write a short story about a memorable day.",
    "Describe your favorite food.",
    "Write about a goal you want to achieve this year.",
    "Describe your ideal weekend."
]

# =========================
# 오늘 구문 메시지 생성
# =========================
def generate_today_message():
    day = get_today_day()
    patterns_today = df[df["Day"] == day].sample(3, replace=True)  # 3개 구문 랜덤 선택
    topic = random.choice(WRITING_TOPICS)
    
    message = f"📚 English Pattern Day {day}\n\n"
    for idx, row in patterns_today.iterrows():
        message += f"• Pattern: {row['Pattern']}\n"
        message += f"• Example: {row['Example']}\n"
        message += f"• Korean: {row['Korean']}\n\n"
    message += f"✏️ 오늘의 작문 주제:\n{topic}"
    
    # 파일로 저장 (오후 5시에 재사용)
    with open("today_message.txt", "w", encoding="utf-8") as f:
        f.write(message)
    
    return message

# =========================
# 저장된 메시지 불러오기
# =========================
def load_saved_message():
    if os.path.exists("today_message.txt"):
        with open("today_message.txt", "r", encoding="utf-8") as f:
            return f.read()
    else:
        return None

# =========================
# MAIN
# =========================
def main():
    now = datetime.datetime.now()
    hour = now.hour
    
    # 오전 7시 (Day 메시지 생성)
    if hour == 7:
        message = generate_today_message()
    # 오후 5시 (동일 메시지 재사용)
    elif hour == 17:
        message = load_saved_message()
        if message is None:
            # 만약 파일이 없으면 새로 생성 (예외 처리)
            message = generate_today_message()
    else:
        # 지정된 시간 외에는 실행하지 않음
        return
    
    send_telegram(message)

if __name__ == "__main__":
    main()
