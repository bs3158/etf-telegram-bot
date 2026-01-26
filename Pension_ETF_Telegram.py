import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time
import os
import json
import matplotlib.pyplot as plt

# =========================
# 텔레그램 설정
# =========================
BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

# =========================
# 세액공제 정보 (확정값)
# =========================
TAX_REFUND = 1_188_000  # 13.2% 기준 환급액

DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

SNAPSHOT_FILE = os.path.join(DATA_DIR, "snapshot_pension.json")

# =========================
# 포트폴리오
# =========================
IRP_PORTFOLIO = [
    {"name": "ACE 미국 S&P500", "code": "360200", "qty": 41, "buy": 24765},
    {"name": "ACE 미국 나스닥100 미국채 혼합 50액티브", "code": "438100", "qty": 88, "buy": 14621},
    {"name": "TIGER 미국 배당 다우존스", "code": "458730", "qty": 84, "buy": 13100},
]

PENSION_PORTFOLIO = [
    {"name": "TIGER KRX 금현물", "code": "0072R0", "qty": 197, "buy": 12211},
    {"name": "KIWOOM 국고채10년", "code": "148070", "qty": 15, "buy": 113824},
    {"name": "KODEX 200TR", "code": "278530", "qty": 153, "buy": 19754},
    {"name": "TIGER 미국 S&P500", "code": "360750", "qty": 128, "buy": 23556},
    {"name": "ACE 미국달러SOFR금리(합성)", "code": "456880", "qty": 144, "buy": 11863},
]

ISA_PORTFOLIO = [
    {"name": "TIGER 미국 S&P500", "code": "360750", "qty": 6, "buy": 25045},
    {"name": "TIGER 미국나스닥100", "code": "133690", "qty": 2, "buy": 164130},
    {"name": "TIGER 200", "code": "102110", "qty": 3, "buy": 70510},
]

# =========================
# 네이버 금융 현재가
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

def send_telegram_image(img_path, caption):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    with open(img_path, "rb") as f:
        requests.post(
            url,
            data={"chat_id": CHAT_ID, "caption": caption},
            files={"photo": f},
            timeout=20
        )

# =========================
# 스냅샷 로드/저장
# =========================
def load_snapshot():
    if not os.path.exists(SNAPSHOT_FILE):
        return {}
    with open(SNAPSHOT_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_snapshot(data):
    with open(SNAPSHOT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# =========================
# 계좌 계산
# =========================
def calc_portfolio(portfolio, snapshot, key):
    total_buy = total_now = 0
    lines = []
    today_snapshot = {}

    for item in portfolio:
        price = get_current_price(item["code"])
        buy_amt = item["qty"] * item["buy"]
        now_amt = item["qty"] * price
        profit = now_amt - buy_amt
        rate = profit / buy_amt * 100

        prev = snapshot.get(key, {}).get(item["code"], now_amt)
        diff = now_amt - prev

        emoji = "🔺" if profit > 0 else "🔻" if profit < 0 else "➖"

        lines.append(
            f"{emoji} {item['name']}\n"
            f"현재가: {price:,}원\n"
            f"수익률: {rate:+.2f}%\n"
            f"수익금: {profit:+,}원\n"
            f"전일대비: {diff:+,}원\n"
        )

        total_buy += buy_amt
        total_now += now_amt
        today_snapshot[item["code"]] = now_amt
        time.sleep(0.5)

    return lines, total_buy, total_now, today_snapshot

# =========================
# 그래프 생성
# =========================
def make_chart(summary):
    labels, rates = [], []
    for k, v in summary.items():
        rate = (v["now"] - v["buy"]) / v["buy"] * 100
        labels.append(k)
        rates.append(rate)

    plt.figure(figsize=(6,4))
    plt.bar(labels, rates)
    plt.axhline(0)
    plt.ylabel("수익률 (%)")
    plt.title("계좌별 성과 비교")
    plt.tight_layout()
    path = "account_performance.png"
    plt.savefig(path)
    plt.close()
    return path

# =========================
# 실행
# =========================
def run_report():
    snapshot = load_snapshot()
    today = {}

    lines = ["📊 연금·ISA 포트폴리오 리포트", datetime.now().strftime("%Y-%m-%d %H:%M"), ""]

    summary = {}

    for name, pf, key in [
        ("💼 IRP 계좌", IRP_PORTFOLIO, "IRP"),
        ("💰 개인연금 계좌", PENSION_PORTFOLIO, "PENSION"),
        ("📦 ISA 계좌", ISA_PORTFOLIO, "ISA"),
    ]:
        lines.append(name)
        l, buy, now, snap = calc_portfolio(pf, snapshot, key)
        lines.extend(l)

        profit = now - buy
        rate = profit / buy * 100

        lines.append(
            f"▶️ 소계\n"
            f"매수: {buy:,}원\n"
            f"평가: {now:,}원\n"
            f"수익: {profit:+,}원 ({rate:+.2f}%)\n"
        )

        summary[key] = {"buy": buy, "now": now}
        today[key] = snap

    # 세후 수익률 (연금)
    pension_buy = summary["IRP"]["buy"] + summary["PENSION"]["buy"]
    pension_now = summary["IRP"]["now"] + summary["PENSION"]["now"]
    real_buy = pension_buy - TAX_REFUND
    after_profit = pension_now - real_buy
    after_rate = after_profit / real_buy * 100

    lines.append(
        "💸 연금 세후 기준\n"
        f"세액공제 환급액: {TAX_REFUND:,}원\n"
        f"세후 수익금: {after_profit:+,}원\n"
        f"세후 수익률: {after_rate:+.2f}%\n"
    )

    send_telegram("\n".join(lines))

    img = make_chart(summary)
    send_telegram_image(img, "📈 계좌별 성과 비교")

    save_snapshot(today)

if __name__ == "__main__":
    run_report()

