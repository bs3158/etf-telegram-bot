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
    df.columns = [c.strip() for c in df.columns]  # 컬럼 공백 제거
    # 필요한 컬럼 존재 확인
    required_cols = ['Day', 'Pattern', 'Example', 'Korean']
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"엑셀에 컬럼 '{col}'이 없습니다.")
    return df

# =========================
# 오늘 발송할 3개 패턴 선택
# =========================
def get_today_patterns(df):
    now = datetime.utcnow() + pd.Timedelta(hours=9)
    day_index = (now.day - 1) % 90  # 0~89 인덱스
    start_row = day_index * 3
    end_row = start_row + 3
    # 범위 벗어나면 반복
    if end_row > len(df):
        end_row = len(df)
        start_row = max(0, end_row - 3)
    today_df = df.iloc[start_row:end_row]
    print(f"오늘 선택된 패턴 행: {start_row}~{end_row-1}")
    return today_df

# =========================
# 메시지 생성
# =========================
def create_message(today_df):
    now = datetime.utcnow() + pd.Timedelta(hours=9)
    date_str = now.strftime("%Y-%m-%d (%H:%M) KST")

    msg = f"📚 English Pattern 90 Days\n🗓 {date_str}\n\n"

    for _, row in today_df.iterrows():
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
    max_len = 4000
    for i in range(0, len(message), max_len):
        send_telegram(message[i:i+max_len])

# =========================
# MAIN
# =========================
def main():
    df = load_patterns()
    today_df = get_today_patterns(df)
    message = create_message(today_df)
    print("==== 생성된 메시지 ====")
    print(message[:500], "...\n")  # 일부 출력 확인
    send_message_safe(message)

if __name__ == "__main__":
    main()
