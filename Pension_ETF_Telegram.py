import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time
import os
import json
import matplotlib.pyplot as plt
from matplotlib import font_manager, rcParams

# =========================
# 텔레그램 설정
# =========================
BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

# =========================
# 한글 폰트 설정 (GitHub Actions 대응)
# =========================
def setup_korean_font():
    font_path = "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc"
    if os.path.exists(font_path):
        font_name = font_manager.FontProperties(fname=font_path).get_name()
        rcParams["font.family"] = font_name
        rcParams["axes.unicode_minus"] = False

# =========================
# 포트폴리오
# =========================
portfolio = [
    # IRP
    {"name": "ACE 미국 S&P500", "code": "360200", "qty": 41, "buy": 24765, "account": "IRP"},
    {"name": "ACE 미국 나스닥100 미국채 혼합", "code": "438100", "qty": 88, "buy": 14621, "account": "IRP"},
    {"name": "TIGER 미국 배당 다우존스", "code": "458730", "qty": 84, "buy": 13100, "account": "IRP"},

    # 개인연금
    {"name": "TIGER KRX 금현물", "code": "0072R0", "qty": 197, "buy": 12211, "account": "PENSION"},
    {"name": "KIWOOM 국고채10년", "code": "148070", "qty": 15, "buy": 113824, "account": "PENSION"},
    {"name": "KODEX 200TR", "code": "278530", "qty": 153, "buy": 19754, "account": "PENSION"},
    {"name": "TIGER 미국 S&P500", "code": "360750", "qty": 128, "buy": 23556, "account": "PENSION"},
    {"name": "ACE 미국달러SOFR금리", "code": "456880", "qty": 144, "buy": 11863, "account": "PENSION"},

    # ISA
    {"name": "TIGER 미국 S&P500", "code": "360750", "qty": 6, "buy": 25045, "account": "ISA"},
    {"name": "TIGER 미국나스닥100", "code": "133690", "qty": 2, "buy": 164130, "account": "ISA"},
    {"name": "TIGER 200", "code": "102110", "qty": 3, "buy": 70510, "account": "ISA"},
]

SNAPSHOT_PATH = "data/snapshot_pension.json"

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
# 텔레그램 전송
# =========================
def send_telegram(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": text}, timeout=10)

# =========================
# 리포트 실행
# =========================
def run_report():
    os.makedirs("data", exist_ok=True)

    prev = {}
    if os.path.exists(SNAPSHOT_PATH):
        with open(SNAPSHOT_PATH, "r") as f:
            prev = json.load(f)

    account_sum = {}
    total_now = 0
    total_prev = 0
    snapshot = {}

    lines = []
    lines.append("📊 연금/ISA 통합 포트폴리오 리포트")
    lines.append(f"🕒 {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append("────────────────────")

    for item in portfolio:
        price = get_current_price(item["code"])
        now_amt = price * item["qty"]
        key = f"{item['account']}_{item['code']}"

        prev_amt = prev.get(key, now_amt)
        diff = now_amt - prev_amt

        account_sum.setdefault(item["account"], {"now": 0, "diff": 0})
        account_sum[item["account"]]["now"] += now_amt
        account_sum[item["account"]]["diff"] += diff

        total_now += now_amt
        total_prev += prev_amt

        snapshot[key] = now_amt
        time.sleep(0.3)

    # 계좌별 요약
    for acc, v in account_sum.items():
        lines.append(f"■ {acc}")
        lines.append(f"평가금액: {v['now']:,}원")
        lines.append(f"전일 대비: {v['diff']:+,}원")
        lines.append("")

    # 전체 요약
    lines.append("📈 전체 요약")
    lines.append(f"총 평가금액: {total_now:,}원")
    lines.append(f"전일 대비 합계: {total_now - total_prev:+,}원")

    send_telegram("\n".join(lines))

    # 스냅샷 저장
    with open(SNAPSHOT_PATH, "w") as f:
        json.dump(snapshot, f, ensure_ascii=False, indent=2)

    # 그래프
    setup_korean_font()
    plt.figure()
    plt.bar(account_sum.keys(), [v["diff"] for v in account_sum.values()])
    plt.title("계좌별 전일 대비 수익 비교")
    plt.ylabel("수익금 (원)")
    plt.tight_layout()
    plt.savefig("data/pension_compare.png")
    plt.close()

if __name__ == "__main__":
    run_report()
