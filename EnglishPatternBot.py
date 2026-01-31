import os
import pandas as pd
from datetime import datetime, timedelta, timezone
import requests

# ==========================================
# 1. 환경 변수 및 설정
# ==========================================
# GitHub Secrets에 저장된 값을 가져옵니다.
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
EXCEL_FILE = "English_90Days_Master.xlsx"

# 한국 시간(KST) 설정 (GitHub 서버는 UTC 기준이므로 필수)
KST = timezone(timedelta(hours=9))

def get_today_day(start_date_str="2026-02-01"):
    """시작일로부터 오늘이 몇 번째 날(Day 1 ~ 90)인지 계산"""
    try:
        start = datetime.strptime(start_date_str, "%Y-%m-%d").replace(tzinfo=KST)
        now = datetime.now(KST)
        delta_days = (now - start).days
        # 90일 주기로 순환 (Day 1 ~ Day 90)
        return (delta_days % 90) + 1
    except Exception as e:
        print(f"날짜 계산 오류: {e}")
        return 1

def send_telegram(text):
    """텔레그램 메시지 전송 함수"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID, 
        "text": text, 
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    try:
        response = requests.post(url, data=payload)
        return response.status_code
    except Exception as e:
        print(f"텔레그램 전송 오류: {e}")
        return 500

def main():
    # 환경 변수 체크
    if not BOT_TOKEN or not CHAT_ID:
        print("오류: BOT_TOKEN 또는 CHAT_ID 환경 변수가 설정되지 않았습니다.")
        return

    # 1. 오늘 학습할 Day 계산
    day = get_today_day()
    
    try:
        # 2. 엑셀 파일 로드
        if not os.path.exists(EXCEL_FILE):
            print(f"오류: {EXCEL_FILE} 파일을 찾을 수 없습니다.")
            return
            
        df = pd.read_excel(EXCEL_FILE)
        
        # 3. 오늘 날짜 데이터 필터링 (구문 3개)
        today_data = df[df["Day"] == day]
        
        if today_data.empty:
            print(f"오류: Day {day}에 해당하는 데이터가 엑셀에 없습니다.")
            return

        # 4. 작문 주제 추출 (첫 번째 행에서 가져옴)
        today_topic = today_data.iloc[0]["WritingTopic"]
        
        # 5. 메시지 포맷 구성
        message = f"<b>📅 Day {day} English Pattern</b>\n"
        message += "━━━━━━━━━━━━━━━━━━\n\n"
        
        for _, row in today_data.iterrows():
            message += f"💡 <b>{row['Pattern']}</b>\n"
            message += f"✍️ {row['Example']}\n"
            message += f"🇰🇷 {row['Korean']}\n\n"
        
        message += "━━━━━━━━━━━━━━━━━━\n"
        message += f"✏️ <b>오늘의 작문 주제</b>\n"
        message += f"<i>{today_topic}</i>"
        
        # 6. 전송 실행
        status = send_telegram(message)
        
        if status == 200:
            print(f"성공: Day {day} 메시지를 발송했습니다.")
        else:
            print(f"실패: 텔레그램 API 응답 코드 {status}")

    except Exception as e:
        print(f"실행 중 오류 발생: {e}")

if __name__ == "__main__":
    main()
