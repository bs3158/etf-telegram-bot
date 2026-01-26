import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time
import os
import json
import matplotlib.pyplot as plt

# =========================
# 기본 설정
# =========================
BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

DATA_DIR = "data"
SNAPSHOT_FILE = f"{DATA_DIR}/snapshot_pension.json"
GRAPH_FILE = f"{DATA_DIR}/pension_account_compare.png"

os.makedirs(DATA_DIR, exist_ok=True)

# matplotlib (GitHub Actions 한글 대응)
plt.rcParams["font.family"] = "DejaVu Sans"
plt.rcParams["axes.unicode_minus"] = False

# =========================
# 포트폴리오 (계좌 구분)
# =========================
portfolio = [
    # IRP (앞 3개)
    {"account": "IRP", "name": "ACE 미국 S&P500", "code": "360200", "qty": 41, "buy": 24765},
    {"account": "IRP", "name": "ACE 미국 나스닥100 미국채 혼합", "code": "438100", "qty": 88, "buy": 14621},
    {"account": "IRP", "name": "TIGER 미국 배당 다우존스", "code": "458730", "qty": 84, "buy": 13100},

    # 개인연금
    {"account": "PENSION", "name": "TIGER KRX 금현물", "code": "0072R0", "qty": 197, "buy": 12211},
    {"account": "PENSION", "name": "KIWOOM 국고채10년", "code": "148070", "qty": 15, "buy": 113824},
    {"account": "PENSION", "name": "KODEX 200TR", "code": "278530", "qty": 153, "buy": 19754},
    {"account": "PENSION", "name": "TIGER 미국 S&P500", "code": "360750", "qty": 128, "buy": 23556},
    {"account": "PENSION", "name": "ACE 미국달러SOFR금리(합성)", "code": "456880", "qty": 144, "buy": 11863},

    # ISA
    {"account": "ISA", "name": "TIGER 미국 S&P500", "code": "360750", "qty": 6, "buy": 25045},
    {"account": "ISA", "name": "TIGER 미국나스닥100", "code": "133690", "qty": 2, "buy": 164130},
    {"account": "ISA", "name": "TIGER 200", "code": "102110", "qty": 3, "buy": 70510},
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

def send_telegram_photo(image_path, caption=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    with open(image_path, "rb") as f:
        requests.post(
            url,
            data={"chat_id": CHAT_ID, "caption": caption},
            files={"photo": f},
            timeout=20
        )

# =========================
# 스냅샷 로드
# =========================
def load_snapshot():
    if not os.path.exists(SNAPSHOT_FILE):
        return {}
    with open(SNAPSHOT_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_snapshot(snapshot):
    with open(SNAPSHOT_FILE, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, ensure_ascii=False, indent=2)

# =========================
# 리포트 실행
# =========================
def run_report():
    prev_snapshot = load_snapshot()
    today_snapshot = {}

    account_sum = {}
    account_prev = {}

    lines = []
    lines.append("📊 연금 / ISA 통합 포트폴리오 리포트")
    lines.append(f"🕒 {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append("────────────────────")

    for item in portfolio:
        price = get_current_price(item["code"])
        qty = item["qty"]
        buy = item["buy"]
        acc = item["account"]

        now_amt = price * qty
        buy_amt = buy * qty
        profit = now_amt - buy_amt
        rate = profit / buy_amt * 100

        account_sum.setdefault(acc, 0)
        account_sum[acc] += now_amt

        key = f"{acc}_{item['code']}"
        today_snapshot[key] = now_amt
        prev_amt = prev_snapshot.get(key, now_amt)
        delta = now_amt - prev_amt

        emoji = "🔺" if profit > 0 else "🔻" if profit < 0 else "➖"

        lines.append(
            f"■ [{acc}] {item['name']}\n"
            f"현재가: {price:,}원\n"
            f"수익률: {rate:+.2f}% {emoji}\n"
            f"평가손익: {profit:+,}원\n"
            f"전일 대비: {delta:+,}원\n"
            "────────────────────"
        )

        time.sleep(0.4)

    # 계좌별 전일 대비
    for k, v in today_snapshot.items():
        acc = k.split("_")[0]
        account_prev.setdefault(acc, 0)
        account_prev[acc] += prev_snapshot.get(k, v)

    # 요약
    total_now = sum(account_sum.values())
    total_prev = sum(account_prev.values())
    total_delta = total_now - total_prev

    lines.append("📈 계좌별 요약")
    for acc in account_sum:
        delta = account_sum[acc] - account_prev.get(acc, account_sum[acc])
        lines.append(f"{acc}: {account_sum[acc]:,}원 (전일 대비 {delta:+,}원)")

    lines.append("────────────────────")
    lines.append(f"💰 전체 평가금액: {total_now:,}원")
    lines.append(f"📊 전일 대비 합계: {total_delta:+,}원")

    send_telegram("\n".join(lines))

    # =========================
    # 그래프 생성
    # =========================
    labels = list(account_sum.keys())
    values = list(account_sum.values())

    plt.figure(figsize=(6,4))
    plt.bar(labels, values)
    plt.title("계좌별 평가금액 비교")
    plt.ylabel("금액 (원)")
    plt.tight_layout()
    plt.savefig(GRAPH_FILE)
    plt.close()

    send_telegram_photo(GRAPH_FILE, caption="📊 IRP / 개인연금 / ISA 계좌별 평가금액")

    save_snapshot(today_snapshot)

# =========================
# 실행
# =========================
if __name__ == "__main__":
    run_report()
