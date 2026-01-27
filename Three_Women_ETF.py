import requests
from datetime import datetime
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
SNAPSHOT_FILE = f"{DATA_DIR}/snapshot_three_women.json"
GRAPH_FILE = f"{DATA_DIR}/three_women_etf.png"
os.makedirs(DATA_DIR, exist_ok=True)

# =========================
# 🔤 폰트 설정
# =========================
font_path = "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc"
if os.path.exists(font_path):
    font_prop = font_manager.FontProperties(fname=font_path)
    rc("font", family=font_prop.get_name())
    plt.rcParams["axes.unicode_minus"] = False

# =========================
# 포트폴리오
# =========================
portfolio = [
    {"name": "Hyunjoo", "ticker": "SPYM", "qty": 107, "buy": 62.13},
    {"name": "Seohye",  "ticker": "SPYM", "qty": 77,  "buy": 71.15},
    {"name": "Wooseon", "ticker": "SPYM", "qty": 72,  "buy": 71.39},
]

# =========================
# 가격 / 환율 조회
# =========================
def get_price(ticker):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
    r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
    return r.json()["chart"]["result"][0]["meta"]["regularMarketPrice"]

def get_usdkrw():
    url = "https://query1.finance.yahoo.com/v8/finance/chart/KRW=X"
    r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
    return r.json()["chart"]["result"][0]["meta"]["regularMarketPrice"]

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
# 텔레그램
# =========================
def send_msg(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": text}, timeout=10)

def send_photo(path, caption):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    with open(path, "rb") as f:
        requests.post(
            url,
            data={"chat_id": CHAT_ID, "caption": caption},
            files={"photo": f},
            timeout=20
        )

# =========================
# 실행
# =========================
def run_report():
    prev = load_snapshot()
    today = {}

    price = get_price("SPYM")
    fx = get_usdkrw()

    lines = [
        "👩‍👩‍👧 Three Women ETF 리포트",
        f"🕒 {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        ""
    ]

    names, values = [], []

    for p in portfolio:
        buy_amt_usd = p["qty"] * p["buy"]
        now_amt_usd = p["qty"] * price
        prev_amt_usd = prev.get(p["name"], now_amt_usd)

        buy_amt = buy_amt_usd * fx
        now_amt = now_amt_usd * fx
        prev_amt = prev_amt_usd * fx

        profit = now_amt - buy_amt
        rate = profit / buy_amt * 100
        delta = now_amt - prev_amt

        rate_emoji = "🔺" if rate > 0 else "🔻" if rate < 0 else "➖"
        delta_emoji = "🔺" if delta > 0 else "🔻" if delta < 0 else "➖"

        today[p["name"]] = now_amt_usd
        names.append(p["name"])
        values.append(now_amt)

        lines.append(
            f"■ {p['name']} (SPYM)\n"
            f"현재가: {(price * fx):,.0f}원\n"
            f"수익률: {rate:+.2f}% {rate_emoji}\n"
            f"평가손익: {profit:+,.0f}원\n"
            f"전일 대비: {delta:+,.0f}원 {delta_emoji}"
        )
        lines.append("- - - - -")

    lines.append(f"💱 USD/KRW 환율: {fx:,.2f}원")
    send_msg("\n".join(lines))

    # =========================
    # 그래프
    # =========================
    plt.figure(figsize=(6, 4))
    bars = plt.bar(names, values)
    plt.title("Total Value")
    plt.ylabel("KRW")

    for b in bars:
        plt.text(
            b.get_x() + b.get_width() / 2,
            b.get_height(),
            f"{b.get_height():,.0f}원",
            ha="center",
            va="bottom"
        )

    plt.tight_layout()
    plt.savefig(GRAPH_FILE)
    plt.close()

    send_photo(GRAPH_FILE, "📊 Three Women ETF Total Value")
    save_snapshot(today)

if __name__ == "__main__":
    run_report()
