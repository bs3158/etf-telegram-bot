import requests
import matplotlib.pyplot as plt
import os
from datetime import datetime

# =====================
# 기본 설정
# =====================
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

TICKER = "SPYM"

PEOPLE = {
    "Hyunjoo": {"qty": 107, "buy_price": 62.13},
    "Seohye": {"qty": 77, "buy_price": 71.15},
    "Wooseon": {"qty": 72, "buy_price": 71.39},
}

GRAPH_FILE = "data/three_women_total_value.png"


# =====================
# 가격 / 환율 조회
# =====================
def get_us_price(ticker):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
    res = requests.get(url, timeout=10)
    data = res.json()
    return data["chart"]["result"][0]["meta"]["regularMarketPrice"]


def get_usd_krw():
    url = "https://api.exchangerate.host/latest?base=USD&symbols=KRW"
    res = requests.get(url, timeout=10)
    data = res.json()
    return data["rates"]["KRW"]


# =====================
# 텔레그램 전송
# =====================
def send_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": text})


def send_photo(path):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    with open(path, "rb") as f:
        requests.post(url, data={"chat_id": CHAT_ID}, files={"photo": f})


# =====================
# 메인 로직
# =====================
def run_report():
    price_usd = get_us_price(TICKER)
    usd_krw = get_usd_krw()

    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    message = f"📊 Three Women ETF 리포트\n🕒 {now}\n\n"

    total_value_usd = 0
    values_for_graph = []
    names_for_graph = []

    for name, info in PEOPLE.items():
        qty = info["qty"]
        buy_price = info["buy_price"]

        value_usd = price_usd * qty
        cost_usd = buy_price * qty
        profit_usd = value_usd - cost_usd
        profit_rate = profit_usd / cost_usd * 100

        # ⚠️ 전일 대비 (기존 로직 그대로, 없으면 0)
        today_diff_usd = 0

        total_value_usd += value_usd

        # =====================
        # ✅ 출력용 원화 변환 (여기만 수정)
        # =====================
        price_krw = price_usd * usd_krw
        value_krw = value_usd * usd_krw
        profit_krw = profit_usd * usd_krw
        today_diff_krw = today_diff_usd * usd_krw

        message += (
            f"■ {name}\n"
            f"현재가: {price_krw:,.0f}원\n"
            f"수익률: {profit_rate:.2f}%\n"
            f"평가손익: {profit_krw:+,.0f}원\n"
            f"전일 대비: {today_diff_krw:+,.0f}원\n"
            f"────────────────────\n"
        )

        values_for_graph.append(value_krw)
        names_for_graph.append(name)

    total_value_krw = total_value_usd * usd_krw

    message += (
        f"\n📈 전체 요약\n"
        f"총 평가금액: {total_value_krw:,.0f}원\n"
        f"\n💱 적용 환율: 1 USD = {usd_krw:,.2f} KRW"
    )

    # =====================
    # 그래프 (기존 구조 유지, 원화 값 사용)
    # =====================
    plt.figure(figsize=(6, 4))
    plt.bar(names_for_graph, values_for_graph)
    plt.title("Total Value")
    plt.ylabel("KRW")
    plt.tight_layout()
    plt.savefig(GRAPH_FILE)
    plt.close()

    # =====================
    # 전송
    # =====================
    send_message(message)
    send_photo(GRAPH_FILE)


if __name__ == "__main__":
    run_report()
