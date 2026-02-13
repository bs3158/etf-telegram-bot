import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time
import os
import matplotlib.pyplot as plt

# =====================================================
# 텔레그램 설정
# =====================================================
BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

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

# =====================================================
# 공통 유틸
# =====================================================
def arrow(val):
    if val > 0:
        return "⬆️"
    elif val < 0:
        return "⬇️"
    return "➖"

def get_kr_price(code):
    url = f"https://finance.naver.com/item/main.naver?code={code}"
    r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
    soup = BeautifulSoup(r.text, "html.parser")
    
    tag = soup.select_one("p.no_today span.blind")
    if not tag:
        return 0

    return int(soup.select_one("p.no_today span.blind").text.replace(",", ""))

def get_us_price(ticker):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
    try:
        r = requests.get(
            url,
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=10
        )
        data = r.json()
        return data["chart"]["result"][0]["meta"]["regularMarketPrice"]
    except Exception as e:
        print(f"[WARN] 미국 주가 조회 실패: {ticker} ({e})")
        return 0


def get_fx():
    url = "https://query1.finance.yahoo.com/v8/finance/chart/KRW=X"
    try:
        r = requests.get(
            url,
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=10
        )
        data = r.json()
        return data["chart"]["result"][0]["meta"]["regularMarketPrice"]
    except Exception as e:
        print(f"[WARN] 환율 조회 실패 (KRW=X): {e}")
        return 0

# =====================================================
# 가격 / 환율 조회
# =====================================================
def get_price(ticker):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
    r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
    return r.json()["chart"]["result"][0]["meta"]["regularMarketPrice"]

def get_usdkrw():
    url = "https://query1.finance.yahoo.com/v8/finance/chart/KRW=X"
    r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
    return r.json()["chart"]["result"][0]["meta"]["regularMarketPrice"]


# =====================================================
# 1️⃣ 김종학 ETF
# =====================================================
def report_jonghak():
    principal = 41_180_360
    portfolio = [
        ("TIGER KRX 금현물", "0072R0", 878, 9932),
        ("KODEX 200TR", "278530", 575, 15176),
        ("TIGER 미국 S&P500", "360750", 413, 21355),
        ("KODEX 200 타겟 위클리 커버드콜", "498400", 1029, 17068),
    ]

    lines = [
        "📊 김종학 ETF 리포트",
        f"🕒 {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        ""
    ]

    total_now = 0

    for name, code, qty, buy in portfolio:
        price = get_kr_price(code)
        now = price * qty
        buy_amt = buy * qty
        profit = now - buy_amt
        rate = profit / buy_amt * 100

        total_now += now

        lines.append(
            f"■ {name}\n"
            f"현재가: {price:,} 원\n"
            f"평가금액: {now:,} 원\n"
            f"수익률: {rate:+.2f}% {arrow(rate)}\n"
            f"평가손익: {profit:+,} 원 {arrow(profit)}"
        )
        lines.append("────────────────")

    total_profit = total_now - principal
    total_rate = total_profit / principal * 100

    lines += [
        "",
        "📈 전체 요약",
        f"총 투자원금: {principal:,} 원",
        f"총 평가금액: {total_now:,} 원",
        f"전체 수익금: {total_profit:+,} 원 {arrow(total_profit)}",
        f"전체 수익률: {total_rate:+.2f}% {arrow(total_rate)}",
    ]

    send_msg("\n".join(lines))

# =====================================================
# 2️⃣ Three Women ETF
# =====================================================
def report_three_women():
    portfolio = [
        ("Hyunjoo", 107, 6_731_607),
        ("Seohye", 77, 5_581_502),
        ("Wooseon", 72, 4_927_559),
    ]

    price = get_us_price("SPYM")
    fx = get_fx()

    lines = [
        "👩‍👩‍👧 Three Women ETF 리포트",
        f"🕒 {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        ""
    ]

    names, values = [], []
    total_principal = total_now = 0

    for name, qty, principal in portfolio:
        now = price * qty * fx
        profit = now - principal
        rate = profit / principal * 100

        names.append(name)
        values.append(now)
        total_principal += principal
        total_now += now

        lines.append(
            f"■ {name}\n"
            f"현재가: {price * fx:.2f} 원\n"
            f"평가금액: {now:,.0f} 원\n"
            f"수익률: {rate:+.2f}% {arrow(rate)}\n"
            f"평가손익: {profit:+,.0f} 원 {arrow(profit)}"
        )
        lines.append("────────────────")

    total_profit = total_now - total_principal
    total_rate = total_profit / total_principal * 100

    lines += [
        "",
        "📈 전체 요약",
        f"총 투자원금: {total_principal:,} 원",
        f"총 평가금액: {total_now:,.0f} 원",
        f"전체 수익금: {total_profit:+,.0f} 원 {arrow(total_profit)}",
        f"전체 수익률: {total_rate:+.2f}% {arrow(total_rate)}",
    ]
    
    lines.append(f"💱 USD/KRW 환율: {fx:,.2f}원")

    send_msg("\n".join(lines))

    plt.figure(figsize=(6,4))
    bars = plt.bar(names, values)
    plt.title("Total Value")
    plt.ylabel("won")
    for b in bars:
        plt.text(b.get_x()+b.get_width()/2, b.get_height(), f"{int(b.get_height()):,}",
                 ha="center", va="bottom")
    plt.tight_layout()
    plt.savefig("three_women.png")
    plt.close()
    send_photo("three_women.png", "📊 Three Women ETF Total Value")

# =====================================================
# 3️⃣ 연금 ETF
# =====================================================
def report_pension():
    portfolio = [
        ("IRP", "ACE 미국 나스닥100 미국채 혼합 50 액티브", "438100", 88, 14621),
        ("IRP", "TIGER 미국 S&P500", "360750", 50, 24485),
        ("IRP", "KODEX 200 TR", "278530", 36, 28325),        

        ("Non Tax Pension", "TIGER KRX 금현물", "0072R0", 197, 12211),
        ("Non Tax Pension", "KODEX 200TR", "278530", 155, 29532),
        ("Non Tax Pension", "TIGER 미국 S&P500", "360750", 128, 23556),
        ("Non Tax Pension", "TIGER 미국 나스닥100", "133690", 17, 158065),

        ("ISA", "KODEX 미국 배당 커버드콜 액티브", "441640", 57, 12865),

        ("Personal Account", "KODEX 200타겟 위클리 커버드콜", "498400", 29, 17435),
        ("Personal Account", "KODEX 금융 고배당 Top10 타겟 위클리 커버드콜", "498410", 33, 14960),
    ]

    lines = [
        "🧓 연금 ETF 리포트",
        f"🕒 {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        ""
    ]

    accounts = {}
    totals = {}

    # -------------------------
    # 데이터 수집
    # -------------------------
    for acc, name, code, qty, buy in portfolio:
        price = get_kr_price(code)
        now = price * qty
        buy_amt = buy * qty
        profit = now - buy_amt
        rate = profit / buy_amt * 100

        accounts.setdefault(acc, [])
        totals.setdefault(acc, {"buy": 0, "now": 0})

        accounts[acc].append({
            "name": name,
            "price": price,
            "now": now,
            "profit": profit,
            "rate": rate
        })

        totals[acc]["buy"] += buy_amt
        totals[acc]["now"] += now

    # -------------------------
    # 출력 (계좌별)
    # -------------------------
    graph_labels = []
    graph_values = []

    for acc in ["IRP", "Non Tax Pension", "ISA", "Personal Account"]:
        lines.append(f"📂 [{acc} 계좌]")
        lines.append("────────────────")

        for item in accounts.get(acc, []):
            lines.append(
                f"■ {item['name']}\n"
                f"현재가: {item['price']:,} 원\n"
                f"평가금액: {item['now']:,} 원\n"
                f"수익률: {item['rate']:+.2f}% {arrow(item['rate'])}\n"
                f"평가손익: {item['profit']:+,} 원 {arrow(item['profit'])}"
            )
            lines.append("- - - - -")

        acc_buy = totals[acc]["buy"]
        acc_now = totals[acc]["now"]
        acc_profit = acc_now - acc_buy
        acc_rate = acc_profit / acc_buy * 100 if acc_buy else 0

        lines.extend([
            f"🧾 {acc} 요약",
            f"총 투자원금: {acc_buy:,} 원",
            f"총 평가금액: {acc_now:,} 원",
            f"총 수익금: {acc_profit:+,} 원 {arrow(acc_profit)}",
            f"총 수익률: {acc_rate:+.2f}% {arrow(acc_rate)}",
            ""
        ])

        graph_labels.append(acc)
        graph_values.append(acc_now)

    # -------------------------
    # 전체 요약
    # -------------------------
    total_buy = sum(v["buy"] for v in totals.values())
    total_now = sum(v["now"] for v in totals.values())
    total_profit = total_now - total_buy
    total_rate = total_profit / total_buy * 100 if total_buy else 0

    lines.extend([
        "📈 전체 요약",
        f"총 투자원금: {total_buy:,} 원",
        f"총 평가금액: {total_now:,} 원",
        f"전체 수익금: {total_profit:+,} 원 {arrow(total_profit)}",
        f"전체 수익률: {total_rate:+.2f}% {arrow(total_rate)}",
    ])

    send_msg("\n".join(lines))

    # -------------------------
    # 그래프 (계좌별 평가금액)
    # -------------------------
    plt.figure(figsize=(6, 4))
    bars = plt.bar(graph_labels, graph_values)
    plt.title("Total Value")
    plt.ylabel("won")

    for b in bars:
        plt.text(
            b.get_x() + b.get_width() / 2,
            b.get_height(),
            f"{int(b.get_height()):,}",
            ha="center",
            va="bottom"
        )

    plt.tight_layout()
    plt.savefig("pension.png")
    plt.close()

    send_photo("pension.png", "📊 연금 계좌별 총 평가금액")


# =====================================================
# 4️⃣ 우리사주
# =====================================================
def report_woorisaju():
    portfolio = [
        ("현대차", "005380", 239, 205_789),
        ("현대차우", "005385", 20, 198_908),
    ]

    lines = [
        "🏢 우리사주 리포트",
        f"🕒 {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        ""
    ]

    total_principal = total_now = 0

    for name, code, qty, buy in portfolio:
        price = get_kr_price(code)
        now = price * qty
        buy_amt = buy * qty
        profit = now - buy_amt
        rate = profit / buy_amt * 100

        total_principal += buy_amt
        total_now += now

        lines.append(
            f"■ {name}\n"
            f"현재가: {price:,} 원\n"
            f"평가금액: {now:,} 원\n"
            f"수익률: {rate:+.2f}% {arrow(rate)}\n"
            f"평가손익: {profit:+,} 원 {arrow(profit)}"
        )
        lines.append("────────────────")

    total_profit = total_now - total_principal
    total_rate = total_profit / total_principal * 100

    lines += [
        "",
        "📈 전체 요약",
        f"총 투자원금: {total_principal:,} 원",
        f"총 평가금액: {total_now:,} 원",
        f"전체 수익금: {total_profit:+,} 원 {arrow(total_profit)}",
        f"전체 수익률: {total_rate:+.2f}% {arrow(total_rate)}",
    ]

    send_msg("\n".join(lines))

# =====================================================
# 실행
# =====================================================
if __name__ == "__main__":
    report_jonghak()
    report_three_women()
    report_pension()
    report_woorisaju()
