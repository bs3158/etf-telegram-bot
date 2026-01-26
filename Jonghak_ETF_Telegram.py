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
# 경로 설정
# =========================
DATA_DIR = "data"
SNAPSHOT_FILE = os.path.join(DATA_DIR, "last_snapshot.json")

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
# 스냅샷 로드
# =========================
def load_snapshot():
    if not os.path.exists(SNAPSHOT_FILE):
        return None
    with open(SNAPSHOT_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

# =========================
# 스냅샷 저장 (종가 기준)
# =========================
def save_snapshot(total_now, total_profit):
    os.makedirs(DATA_DIR, exist_ok=True)
    data = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "total_now": total_now,
        "total_profit": total_profit
    }
    with open(SNAPSHOT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# =========================
# 리포트 실행
# =========================
def run_report():
    today = datetime.now()

    # 주말 스킵
    if today.weekday() >= 5:
        send_telegram("📌 오늘은 장이 열리지 않았습니다 (주말)")
        return

    snapshot = load_snapshot()

    total_buy = 0
    total_now = 0
    lines = []

    lines.append("📊 김종학 용돈 ETF 포트폴리오 리포트")
    lines.append(today.strftime("🕒 %Y-%m-%d %H:%M"))
    lines.append("")

    results = []

    # 종목별 계산
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

        results.append({
            "name": item["name"],
            "price": price,
            "now_amt": now_amt,
            "profit": profit,
            "rate": rate
        })

        time.sleep(0.5)  # 네이버 차단 방지

    # 종목별 출력 + 비중
    for r in results:
        weight = r["now_amt"] / total_now * 100
        emoji = "🔺" if r["profit"] > 0 else "🔻" if r["profit"] < 0 else "➖"

        lines.append(f"■ {r['name']}")
        lines.append(f"현재가: {r['price']:,}원")
        lines.append(f"수익률: {r['rate']:+.2f}% {emoji}")
        lines.append(f"평가손익: {r['profit']:+,}원")
        lines.append(f"비중: {weight:.1f}%")
        lines.append("────────────────────")

    total_profit = total_now - total_buy
    total_rate = total_profit / total_buy * 100

    # 전일 대비 계산 (종가 기준)
    if snapshot:
        diff_profit = total_profit - snapshot["total_profit"]
        diff_emoji = "🔺" if diff_profit > 0 else "🔻" if diff_profit < 0 else "➖"
        lines.append(f"전일 대비 수익 변화: {diff_profit:+,}원 {diff_emoji}")

    lines.append("")
    lines.append("📈 전체 요약")
    lines.append(f"총 평가금액: {total_now:,}원")
    lines.append(f"전체 수익금: {total_profit:+,}원")
    lines.append(f"전체 수익률: {total_rate:+.2f}%")

    send_telegram("\n".join(lines))

    # =========================
    # 종가 기준: 하루 1회만 스냅샷 저장
    # =========================
    today_str = today.strftime("%Y-%m-%d")
    if not snapshot or snapshot.get("date") != today_str:
        save_snapshot(total_now, total_profit)

# =========================
# 실행
# =========================
if __name__ == "__main__":
    run_report()
