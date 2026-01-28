import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time
import os
import json

# =========================
# 텔레그램 설정
# =========================
BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

# =========================
# 스냅샷 경로 (우리사주 전용)
# =========================
SNAPSHOT_PATH = "data/snapshot_woorisaju.json"

# =========================
# 포트폴리오 (우리사주)
# =========================
portfolio = [
    {"name": "현대차", "code": "005380", "qty": 239, "buy": 205789},
    {"name": "현대차우", "code": "005385", "qty": 20, "buy": 198908},
]

# =========================
# 현재가 조회
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
# 스냅샷 처리
# =========================
def load_snapshot():
    if not os.path.exists(SNAPSHOT_PATH):
        return {}
    with open(SNAPSHOT_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def save_snapshot(snapshot):
    os.makedirs("data", exist_ok=True)
    with open(SNAPSHOT_PATH, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, ensure_ascii=False, indent=2)

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
    prev_snapshot = load_snapshot()
    today_snapshot = {}

    total_buy = 0
    total_now = 0
    total_prev = 0

    lines = []
    lines.append("📊 우리사주 리포트")
    lines.append(f"🕒 {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append("")

    # 현재가 미리 조회
    prices = {}
    for item in portfolio:
        prices[item["code"]] = get_current_price(item["code"])
        time.sleep(0.3)

    for item in portfolio:
        code = item["code"]
        name = item["name"]
        qty = item["qty"]
        buy = item["buy"]
        price = prices[code]

        buy_amt = qty * buy
        now_amt = qty * price
        prev_amt = prev_snapshot.get(code, now_amt)

        profit = now_amt - buy_amt
        rate = profit / buy_amt * 100
        delta = now_amt - prev_amt

        total_buy += buy_amt
        total_now += now_amt
        total_prev += prev_amt

        today_snapshot[code] = now_amt

        emoji = "🔺" if profit > 0 else "🔻" if profit < 0 else "➖"
        delta_emoji = "🔺" if delta > 0 else "🔻" if delta < 0 else "➖"

        lines.append(
            f"■ {name}\n"
            f"현재가: {price:,}원\n"
            f"수익률: {rate:+.2f}% {emoji}\n"
            f"평가손익: {profit:+,}원\n"
            f"전일 대비: {delta:+,}원 {delta_emoji}"
        )
        lines.append("────────────────────")

        time.sleep(0.3)

    # 전체 요약
    total_profit = total_now - total_buy
    total_rate = total_profit / total_buy * 100
    total_delta = total_now - total_prev
    total_delta_emoji = "🔺" if total_delta > 0 else "🔻" if total_delta < 0 else "➖"

    lines.append("")
    lines.append("📈 전체 요약")
    lines.append(f"총 평가금액: {total_now:,}원")
    lines.append(f"전체 수익금: {total_profit:+,}원")
    lines.append(f"전체 수익률: {total_rate:+.2f}%")
    lines.append(f"전일 대비 합계: {total_delta:+,}원 {total_delta_emoji}")

    send_telegram("\n".join(lines))

    # 스냅샷 저장
    save_snapshot(today_snapshot)

# =========================
# 실행
# =========================
if __name__ == "__main__":
    run_report()
