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
# 🔤 한글 폰트 설정
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
    {"account": "IRP", "name": "ACE 미국 S&P500", "code": "360200", "qty": 41, "buy": 24765},
    {"account": "IRP", "name": "ACE 미국 나스닥100 미국채 혼합", "code": "438100", "qty": 88, "buy": 14621},
    {"account": "IRP", "name": "TIGER 미국 배당 다우존스", "code": "458730", "qty": 84, "buy": 13100},

    {"account": "Pension", "name": "TIGER KRX 금현물", "code": "0072R0", "qty": 197, "buy": 12211},
    {"account": "Pension", "name": "KIWOOM 국고채10년", "code": "148070", "qty": 15, "buy": 113824},
    {"account": "Pension", "name": "KODEX 200TR", "code": "278530", "qty": 153, "buy": 19754},
    {"account": "Pension", "name": "TIGER 미국 S&P500", "code": "360750", "qty": 128, "buy": 23556},
    {"account": "Pension", "name": "ACE 미국달러SOFR금리(합성)", "code": "456880", "qty": 144, "buy": 11863},

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
    if not price:
        raise ValueError(code)
    return int(price.text.replace(",", ""))

# =========================
# 텔레그램
# =========================
def send_msg(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": text})

def send_photo(path, caption):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    with open(path, "rb") as f:
        requests.post(url, data={"chat_id": CHAT_ID, "caption": caption}, files={"photo": f})

# =========================
# 스냅샷
# =========================
def load_snapshot():
    if not os.path.exists(SNAPSHOT_FILE):
        return {}
    return json.load(open(SNAPSHOT_FILE, "r", encoding="utf-8"))

def save_snapshot(data):
    json.dump(data, open(SNAPSHOT_FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

# =========================
# 실행
# =========================
def run_report():
    prev = load_snapshot()
    today = {}
    prices = {}

    for p in portfolio:
        try:
            prices[p["code"]] = get_current_price(p["code"])
        except:
            prices[p["code"]] = 0
        time.sleep(0.3)

    accounts = {}
    totals = {}
    g_buy = g_now = g_prev = 0

    lines = [
        "📊 연금 / ISA 통합 포트폴리오 리포트",
        f"🕒 {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        ""
    ]

    for p in portfolio:
        acc = p["account"]
        code = p["code"]
        qty = p["qty"]
        buy_amt = qty * p["buy"]
        now_amt = qty * prices[code]
        key = f"{acc}_{code}"
        prev_amt = prev.get(key, now_amt)

        today[key] = now_amt

        accounts.setdefault(acc, [])
        totals.setdefault(acc, {"buy": 0, "now": 0, "prev": 0})

        accounts[acc].append({
            "name": p["name"],
            "price": prices[code],
            "qty": qty,
            "buy": buy_amt,
            "now": now_amt,
            "profit": now_amt - buy_amt,
            "rate": (now_amt - buy_amt) / buy_amt * 100 if buy_amt else 0,
            "delta": now_amt - prev_amt
        })

        totals[acc]["buy"] += buy_amt
        totals[acc]["now"] += now_amt
        totals[acc]["prev"] += prev_amt

        g_buy += buy_amt
        g_now += now_amt
        g_prev += prev_amt

    # =========================
    # 출력
    # =========================
    for acc in accounts:
        lines.append(f"📂 [{acc} 계좌]")
        lines.append("────────────────────")

        acc_now = totals[acc]["now"]

        for i in accounts[acc]:
            weight = i["now"] / acc_now * 100 if acc_now else 0

            rate_emoji = "🔺" if i["rate"] > 0 else "🔻" if i["rate"] < 0 else "➖"
            delta_emoji = "🔺" if i["delta"] > 0 else "🔻" if i["delta"] < 0 else "➖"

            lines.append(
                f"■ {i['name']}\n"
                f"현재가: {i['price']:,}원\n"
                f"수익률: {i['rate']:+.2f}% {rate_emoji}\n"
                f"평가손익: {i['profit']:+,}원\n"
                f"전일 대비: {i['delta']:+,}원 {delta_emoji}\n"
                f"비중: {weight:.1f}%"
            )
            lines.append("- - - - -")

        acc_profit = totals[acc]["now"] - totals[acc]["buy"]
        acc_rate = acc_profit / totals[acc]["buy"] * 100 if totals[acc]["buy"] else 0
        acc_delta = totals[acc]["now"] - totals[acc]["prev"]

        acc_rate_emoji = "🔺" if acc_rate > 0 else "🔻" if acc_rate < 0 else "➖"
        acc_delta_emoji = "🔺" if acc_delta > 0 else "🔻" if acc_delta < 0 else "➖"

        lines += [
            f"🧾 {acc} 요약",
            f"총 평가금액: {totals[acc]['now']:,}원",
            f"총 수익금: {acc_profit:+,}원",
            f"총 수익률: {acc_rate:+.2f}% {acc_rate_emoji}",
            f"전일 대비: {acc_delta:+,}원 {acc_delta_emoji}",
            "========================\n"
        ]

    g_profit = g_now - g_buy
    g_rate = g_profit / g_buy * 100 if g_buy else 0
    g_delta = g_now - g_prev

    g_rate_emoji = "🔺" if g_rate > 0 else "🔻" if g_rate < 0 else "➖"
    g_delta_emoji = "🔺" if g_delta > 0 else "🔻" if g_delta < 0 else "➖"

    lines += [
        "📈 [전체 포트폴리오 요약]",
        f"전체 평가금액: {g_now:,}원",
        f"전체 총 수익금: {g_profit:+,}원",
        f"전체 총 수익률: {g_rate:+.2f}% {g_rate_emoji}",
        f"전일 대비 합계: {g_delta:+,}원 {g_delta_emoji}"
    ]

    send_msg("\n".join(lines))

    # =========================
    # 그래프
    # =========================
    plt.figure(figsize=(6, 4))
    plt.bar(totals.keys(), [v["now"] for v in totals.values()])
    plt.title("Total Value by Accounts")
    plt.tight_layout()
    plt.savefig(GRAPH_FILE)
    plt.close()

    send_photo(GRAPH_FILE, "📊 계좌별 평가금액 비교")
    save_snapshot(today)

if __name__ == "__main__":
    run_report()
