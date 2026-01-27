import requests
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
SNAPSHOT_FILE = f"{DATA_DIR}/snapshot_three_women.json"
GRAPH_FILE = f"{DATA_DIR}/three_women_value.png"

os.makedirs(DATA_DIR, exist_ok=True)

# =========================
# 🔤 한글 폰트 (GitHub Actions)
# =========================
font_path = "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc"
if os.path.exists(font_path):
    font_prop = font_manager.FontProperties(fname=font_path)
    rc("font", family=font_prop.get_name())
plt.rcParams["axes.unicode_minus"] = False

# =========================
# 포트폴리오 (SPYM 통일)
# =========================
portfolio = [
    {"name": "Hyunjoo", "qty": 107, "buy": 62.13},
    {"name": "Seohye",  "qty": 77,  "buy": 71.15},
    {"name": "Wooseon", "qty": 72,  "buy": 71.39},
]

TICKER = "SPYM"

# =========================
# 현재가 / 환율 조회
# =========================
def get_us_price(ticker):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
    res = requests.get(url, timeout=10)
    data = res.json()
    return data["chart"]["result"][0]["meta"]["regularMarketPrice"]

def get_usdkrw():
    url = "https://query1.finance.yahoo.com/v8/finance/chart/KRW=X"
    res = requests.get(url, timeout=10)
    data = res.json()
    return data["chart"]["result"][0]["meta"]["regularMarketPrice"]

# =========================
# 텔레그램 전송
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

    price_usd = get_us_price(TICKER)
    fx = get_usdkrw()

    lines = []
    lines.append("📊 Three Women ETF 리포트 (SPYM)")
    lines.append(f"🕒 {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"💱 환율: {fx:,.2f}원/USD")
    lines.append("")

    total_now = 0
    total_buy = 0

    names = []
    values = []

    for p in portfolio:
        # 🔽 USD → KRW 환산 (핵심 수정)
        buy_amt = p["qty"] * p["buy"] * fx
        now_amt = p["qty"] * price_usd * fx

        key = p["name"]
        prev_amt = prev_snapshot.get(key, now_amt)
        delta = now_amt - prev_amt

        profit = now_amt - buy_amt
        rate = (profit / buy_amt * 100) if buy_amt > 0 else 0

        today_snapshot[key] = now_amt

        total_now += now_amt
        total_buy += buy_amt

        names.append(p["name"])
        values.append(now_amt)

        delta_emoji = "🔺" if delta > 0 else "🔻" if delta < 0 else "➖"

        lines.append(
            f"■ {p['name']} (SPYM)\n"
            f"현재가: ${price_usd:.2f}\n"
            f"수익률: {rate:+.2f}%\n"
            f"평가손익: {profit:+,.0f}원\n"
            f"전일 대비: {delta:+,.0f}원 {delta_emoji}"
        )
        lines.append("- - - - - - - - - -")

    total_profit = total_now - total_buy
    total_rate = (total_profit / total_buy * 100) if total_buy > 0 else 0

    lines.append("📈 [전체 요약]")
    lines.append(f"총 평가금액: {total_now:,.0f}원")
    lines.append(f"전체 수익금: {total_profit:+,.0f}원")
    lines.append(f"전체 수익률: {total_rate:+.2f}%")

    send_telegram("\n".join(lines))

    # =========================
    # 그래프 (원화 기준)
    # =========================
    plt.figure(figsize=(6, 4))
    bars = plt.bar(names, values)
    plt.title("Total Value")
    plt.ylabel("KRW")

    for b in bars:
        h = b.get_height()
        plt.text(
            b.get_x() + b.get_width() / 2,
            h,
            f"{int(h):,}원",
            ha="center",
            va="bottom"
        )

    plt.tight_layout()
    plt.savefig(GRAPH_FILE)
    plt.close()

    send_telegram_photo(GRAPH_FILE, caption="📊 Three Women ETF 평가금액 비교")

    save_snapshot(today_snapshot)

# =========================
# 실행
# =========================
if __name__ == "__main__":
    run_report()
