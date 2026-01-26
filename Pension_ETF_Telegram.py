import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time
import os
import json
import matplotlib.pyplot as plt
from matplotlib import font_manager, rc

# =========================
# 텔레그램 설정
# =========================
BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

DATA_DIR = "data"
SNAPSHOT_FILE = f"{DATA_DIR}/snapshot_pension.json"
GRAPH_FILE = f"{DATA_DIR}/pension_account_compare.png"

os.makedirs(DATA_DIR, exist_ok=True)

# =========================
# 🔤 한글 폰트 설정 (GitHub Actions 대응)
# =========================
font_path = "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc"
if os.path.exists(font_path):
    font_prop = font_manager.FontProperties(fname=font_path)
    rc("font", family=font_prop.get_name())
plt.rcParams["axes.unicode_minus"] = False

# =========================
# 포트폴리오 (계좌 구분)
# =========================
portfolio = [
    # IRP
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
# 현재가 조회
# =========================
def get_current_price(code):
    url = f"https://finance.naver.com/item/main.naver?code={code}"
    headers = {"User-Agent": "Mozilla/5.0"}
    res = requests.get(url, headers=headers, timeout=10)
    soup = BeautifulSoup(res.text, "html.parser")
    price = soup.select_one("p.no_today span.blind")
    return int(price.text.replace(",", ""))

# =========================
# 텔레그램
# =========================
def send_telegram(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": text}, timeout=10)

def send_telegram_photo(path, caption=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    with open(path, "rb") as f:
        requests.post(
            url,
            data={"chat_id": CHAT_ID, "caption": caption},
            files={"photo": f},
            timeout=20
        )

# =========================
# 스냅샷
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
# 리포트 실행
# =========================
def run_report():
    prev_snapshot = load_snapshot()
    today_snapshot = {}

    account_buy = {}
    account_now = {}

    lines = []
    lines.append("📊 연금 / ISA 통합 포트폴리오 리포트")
    lines.append(f"🕒 {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append("────────────────────")

    for item in portfolio:
        price = get_current_price(item["code"])
        qty = item["qty"]
        buy = item["buy"]
        acc = item["account"]

        buy_amt = buy * qty
        now_amt = price * qty
        profit = now_amt - buy_amt

        account_buy.setdefault(acc, 0)
        account_now.setdefault(acc, 0)

        account_buy[acc] += buy_amt
        account_now[acc] += now_amt

        key = f"{acc}_{item['code']}"
        today_snapshot[key] = now_amt

        time.sleep(0.4)

    # =========================
    # 📈 계좌별 요약
    # =========================
    lines.append("📈 계좌별 요약")
    total_buy = 0
    total_now = 0

    for acc in account_now:
        buy_amt = account_buy[acc]
        now_amt = account_now[acc]
        profit = now_amt - buy_amt
        rate = profit / buy_amt * 100

        total_buy += buy_amt
        total_now += now_amt

        lines.append(
            f"■ {acc}\n"
            f"총 평가금액: {now_amt:,}원\n"
            f"총 수익금: {profit:+,}원\n"
            f"총 수익률: {rate:+.2f}%"
        )

    total_profit = total_now - total_buy
    total_rate = total_profit / total_buy * 100

    lines.append("────────────────────")
    lines.append(f"💰 전체 평가금액: {total_now:,}원")
    lines.append(f"📊 전체 총 수익금: {total_profit:+,}원")
    lines.append(f"📈 전체 총 수익률: {total_rate:+.2f}%")

    send_telegram("\n".join(lines))

    # =========================
    # 📊 그래프 생성
    # =========================
    plt.figure(figsize=(6,4))
    plt.bar(account_now.keys(), account_now.values())
    plt.title("계좌별 평가금액 비교")
    plt.ylabel("금액 (원)")
    plt.tight_layout()
    plt.savefig(GRAPH_FILE)
    plt.close()

    send_telegram_photo(GRAPH_FILE, caption="📊 계좌별 평가금액 비교")

    save_snapshot(today_snapshot)

# =========================
# 실행
# =========================
if __name__ == "__main__":
    run_report()
