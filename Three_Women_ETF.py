import requests
import os
from datetime import datetime

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

TICKER = "SCHD"

# =========================
# 텔레그램
# =========================
def send_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": text})

# =========================
# 미국 ETF 가격 조회 (방어 코드)
# =========================
def get_us_price(ticker):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    res = requests.get(url, headers=headers, timeout=10)

    if res.status_code != 200 or not res.text.strip():
        raise RuntimeError(f"{ticker} 가격 조회 실패 (빈 응답)")

    try:
        data = res.json()
    except Exception:
        print("❌ Yahoo 응답 일부:")
        print(res.text[:300])
        raise RuntimeError("JSON 파싱 실패")

    try:
        return data["chart"]["result"][0]["meta"]["regularMarketPrice"]
    except Exception:
        raise RuntimeError("가격 구조 변경 감지")

# =========================
# 리포트 실행
# =========================
def run_report():
    price = get_us_price(TICKER)
    today = datetime.now().strftime("%Y-%m-%d")

    msg = (
        "👩‍👩‍👧 Three Women ETF\n\n"
        f"ETF: {TICKER}\n"
        f"현재가: ${price}\n"
        f"기준일: {today}"
    )

    send_message(msg)

if __name__ == "__main__":
    run_report()
