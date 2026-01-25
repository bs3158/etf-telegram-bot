import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time

# =========================
# 텔레그램 설정
# =========================
BOT_TOKEN = "8218610510:AAELuynXvDvAXGaS8owhR77v79GH3TG94M4"
CHAT_ID = "43643771"

# =========================
# 포트폴리오
# =========================
portfolio = [
    {"name": "TIGER KRX 금현물", "code": "0072R0", "qty": 878, "buy": 9932},
    {"name": "KIWOOM 국고채10년", "code": "148070", "qty": 76, "buy": 115909},
    {"name": "KODEX 200TR", "code": "278530", "qty": 575, "buy": 15176},
    {"name": "TIGER 미국 S&P500", "code": "360750", "qty": 413, "buy": 21355},
    {"name": "ACE 미국달러SOFR금리(합성)", "code": "456880", "qty": 759, "buy": 11582},
]

# =========================
# 네이버 금융 현재가 조회
# =========================
def get_current_price(code):
    url = f"https://finance.naver.com/item/main.naver?code={code}"
    headers = {"User-Agent": "Mozilla/5.0"}
    res = requests.get(url, headers=headers, timeout=10)
    soup = BeautifulSoup(res.text, "html.parser")

    price = soup.select_one("p.no_today span.blind")
    if not price:
        raise ValueError("현재가 조회 실패")

    return int(price.text.replace(",", ""))

# =========================
# 텔레그램 전송
# =========================
def send_telegram(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": text}, timeout=10)

# =========================
# 리포트 실행
# =========================
def run_report():
    total_buy = 0
    total_now = 0
    lines = []

    lines.append("📊 ETF 포트폴리오 리포트")
    time_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines.append(f"🕒 {time_str}")

    lines.append("────────────────────")

    for item in portfolio:
        price = get_current_price(item["code"])
        qty = item["qty"]
        buy = item["buy"]

        buy_amt = qty * buy
        now_amt = qty * price
        profit = now_amt - buy_amt
        rate = profit / buy_amt * 100

        total_buy += buy_amt
        total_now += now_amt

        emoji = "🔺" if profit > 0 else "🔻" if profit < 0 else "➖"

        lines.append(
            f"{emoji} {item['name']}\n"
            f"현재가: {price:,}원\n"
            f"수익률: {rate:+.2f}%\n"
            f"수익금: {profit:+,}원\n"
        )

        time.sleep(0.5)  # 네이버 차단 방지

    total_profit = total_now - total_buy
    total_rate = total_profit / total_buy * 100

    lines.append("📈 전체 요약")
    lines.append(f"총 매수금액: {total_buy:,}원")
    lines.append(f"총 평가금액: {total_now:,}원")
    lines.append(f"총 수익금: {total_profit:+,}원")
    lines.append(f"전체 수익률: {total_rate:+.2f}%")

    send_telegram("\n".join(lines))

# =========================
# 실행
# =========================
if __name__ == "__main__":
    run_report()
