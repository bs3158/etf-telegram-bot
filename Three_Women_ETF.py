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
SNAPSHOT_FILE = f"{DATA_DIR}/snapshot_spym.json"
GRAPH_FILE = f"{DATA_DIR}/spym_accounts.png"

os.makedirs(DATA_DIR, exist_ok=True)

# =========================
# 폰트 설정 (그래프 영문 → 깨짐 없음)
# =========================
plt.rcParams["axes.unicode_minus"] = False

# =========================
# 계좌 정보
# =========================
accounts = [
    {"name": "Hyunjoo", "qty": 107, "buy": 62.13},
    {"name": "Seohye", "qty": 77, "buy": 71.15},
    {"name": "Wooseon", "qty": 72, "buy": 71.39},
]

TICKER = "SPYM"

# =========================
# 미국 ETF 현재가 조회 (Yahoo Finance)
# =========================
def get_us_price(ticker):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
    res = requests.get(url, timeout=10)
    data = res.json()
    return float(data["chart"]["result"][0]["meta"]["regularMarketPrice"])

# =========================
# 환율 조회 (USD → KRW)
# =========================
def get_usdkrw():
    url = "https://finance.naver.com/marketindex/exchangeDetail.naver?marketindexCd=FX_USDKRW"
    headers = {"User-Agent": "Mozilla/5.0"}
    res = requests.get(url, headers=headers, timeout=10)
    soup = BeautifulSoup(res.text, "html.parser")
    price = soup.select_one("p.no_today span.blind")
    return float(price.text.replace(",", ""))

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
    with open(SNAPSHOT_FILE, "r") as f:
        return json.load(f)

def save_snapshot(data):
    with open(SNAPSHOT_FILE, "w") as f:
        json.dump(data, f, indent=2)

# =========================
# 리포트 실행
# =========================
def run_report():
    prev = load_snapshot()
    today = {}

    usd_price = get_us_price(TICKER)
    usdkrw = get_usdkrw()

    lines = []
    lines.append("📊 SPYM 미국 ETF 계좌별 리포트")
    lines.append(f"🕒 {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"💱 환율: 1 USD = {usdkrw:,.2f} KRW")
    lines.append("────────────────────")

    graph_names = []
    graph_values = []

    for acc in accounts:
        name = acc["name"]
        qty = acc["qty"]
        buy = acc["buy"]

        buy_amt = qty * buy * usdkrw
        now_amt = qty * usd_price * usdkrw
        profit = now_amt - buy_amt
        rate = profit / buy_amt * 100

        prev_amt = prev.get(name, now_amt)
        delta = now_amt - prev_amt

        today[name] = now_amt

        emoji = "🔺" if profit > 0 else "🔻" if profit < 0 else "➖"

        lines.append(
            f"■ {name}\n"
            f"현재가: {usd_price:.2f} USD\n"
            f"수익률: {rate:+.2f}% {emoji}\n"
            f"평가손익: {profit:+,.0f}원\n"
            f"전일 대비: {delta:+,.0f}원"
        )
        lines.append("────────────────────")

        graph_names.append(name)
        graph_values.append(now_amt)

    send_telegram("\n".join(lines))

    # =========================
    # 그래프
    # =========================
    plt.figure(figsize=(6,4))
    bars = plt.bar(graph_names, graph_values)
    plt.title("SPYM Account Value (KRW)")
    plt.ylabel("KRW")

    for bar in bars:
        h = bar.get_height()
        plt.text(bar.get_x()+bar.get_width()/2, h, f"{int(h):,}", ha="center", va="bottom")

    plt.tight_layout()
    plt.savefig(GRAPH_FILE)
    plt.close()

    send_telegram_photo(GRAPH_FILE, caption="📊 SPYM 계좌별 평가금액")

    save_snapshot(today)

# =========================
# 실행
# =========================
if __name__ == "__main__":
    run_report()
