import os
import pandas as pd
from datetime import datetime, timedelta, timezone
import requests

# 환경 변수 설정
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
EXCEL_FILE = "English_90Patterns_with_Korean.xlsx"
KST = timezone(timedelta(hours=9))

# [매일 다른 작문 주제 리스트 - 최소 90개 확보 권장]
WRITING_TOPICS = [
    "Day1: Your favorite childhood memory.",
    "Day2: What is your dream job and why?",
    "Day3: Describe your perfect morning routine.",
    "Day4: If you won the lottery, what would you buy first?",
    "Day5: Who is the person you admire the most?",
    # ... 여기에 90번까지 주제를 추가하세요.
]

def get_today_info(start_date_str="2026-02-01"):
    """시작일부터 오늘까지의 일수를 계산 (Day 1, Day 2...)"""
    start = datetime.strptime(start_date_str, "%Y-%m-%d").replace(tzinfo=KST)
    now = datetime.now(KST)
    delta_days = (now - start).days
    
    day_count = (delta_days % 90) + 1  # 1~90일 반복
    return day_count

def main():
    day = get_today_info()
    
    # 1. 엑셀 로드 및 오늘 분량(3개) 추출
    df = pd.read_excel(EXCEL_FILE)
    today_patterns = df[df["Day"] == day]
    
    # 2. 작문 주제 선택 (인덱스 활용으로 매일 변경 보장)
    # 리스트 범위를 벗어나지 않도록 % 연산 사용
    topic = WRITING_TOPICS[(day - 1) % len(WRITING_TOPICS)]
    
    # 3. 메시지 조립
    message = f"<b>📅 Day {day} English Learning</b>\n"
    message += "━━━━━━━━━━━━━━━━━━\n\n"
    
    for _, row in today_patterns.iterrows():
        message += f"💡 <b>{row['Pattern']}</b>\n"
        message += f"✍️ {row['Example']}\n"
        message += f"🇰🇷 {row['Korean']}\n\n"
        
    message += "━━━━━━━━━━━━━━━━━━\n"
    message += f"✏️ <b>오늘의 작문 주제</b>\n"
    message += f"<i>{topic}</i>"
    
    # 4. 전송
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"})

if __name__ == "__main__":
    main()
