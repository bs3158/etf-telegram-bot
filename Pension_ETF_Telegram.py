import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time
import os
import json
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

# =========================
# 텔레그램 설정
# =========================
BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

DATA_DIR = "data"
SNAPSHOT_FILE = f"{DATA_DIR}/snapshot_pension.json"
GRAPH_FILE = f"{DATA_DIR}/pension_account_compare.png"
FONT_FILE = f"{DATA_DIR}/NanumGothic.ttf"  # 폰트 파일 저장 경로

os.makedirs(DATA_DIR, exist_ok=True)

# =========================
# 🔤 한글 폰트 설정 (자동 다운로드 방식)
# =========================
def set_korean_font():
    # 폰트 파일이 없으면 다운로드 (나눔고딕)
    if not os.path.exists(FONT_FILE):
        print("Downloading NanumGothic font...")
        url = "https://github.com/google/fonts/raw/main/ofl/nanumgothic/NanumGothic-Regular.ttf"
        response = requests.get(url)
        with open(FONT_FILE, "wb") as f:
            f.write(response.content)
    
    # 폰트 로드 및 설정
    font_prop = fm.FontProperties(fname=FONT_FILE)
    plt.rc("font", family=font_prop.get_name())
    plt.rcParams["axes.unicode_minus"] = False # 마이너스 부호 깨짐 방지
    print(f"Font set to: {font_prop.get_name()}")

# =========================
# 포트폴리오 (계좌 구분)
# =========================
portfolio = [
    # IRP
    {"account": "IRP", "name": "ACE 미국 S&P500", "code": "360200", "qty": 41, "buy": 24765},
    {"account": "IRP", "name": "ACE 미국 나스닥100 미국채 혼합", "code": "438100", "qty": 88, "buy": 14621},
    {"account": "IRP", "name": "TIGER 미국 배당 다우존스", "code": "458730", "qty": 84, "buy": 13100},

    # 개인연금 (기존 PENSION -> 개인연금 변경)
    {"account": "개인연금", "name": "TIGER KRX 금현물", "code": "0072R0", "qty": 197, "buy": 12211},
    {"account": "개인연금", "name": "KIWOOM 국고채10년", "code": "148070", "qty": 15, "buy": 113824},
    {"account": "개인연금", "name": "KODEX 200TR", "code": "278530", "qty": 153, "buy": 19754},
    {"account": "개인연금", "name": "TIGER 미국 S&P500", "code": "360750", "qty": 128, "buy": 23556},
    {"account": "개인연금", "name": "ACE 미국달러SOFR금리(합성)", "code": "456880", "qty": 144, "buy": 11863},

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
    if not price:
        raise ValueError(f"현재가 조회 실패: {code}")
    return int(price.text.replace(",", ""))

# =========================
# 텔레그램 전송 함수
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
# 스냅샷 처리
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
    # 폰트 설정 먼저 실행
    set_korean_font()

    prev_snapshot = load_snapshot()
    today_snapshot = {}

    # 1. 모든 종목 현재가 미리 조회
    prices = {}
    for item in portfolio:
        try:
            prices[item["code"]] = get_current_price(item["code"])
        except Exception as e:
            print(f"Error fetching {item['code']}: {e}")
            prices[item["code"]] = 0 
        time.sleep(0.3) 

    accounts_items = {}
    accounts_totals = {} 
    
    global_buy = 0
    global_now = 0
    global_prev = 0

    lines = []
    lines.append("📊 연금 / ISA 통합 포트폴리오 리포트")
    lines.append(f"🕒 {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append("")

    # 2. 데이터 집계
    for item in portfolio:
        acc = item["account"]
        code = item["code"]
        qty = item["qty"]
        buy_price = item["buy"]
        current_price = prices[code]

        snapshot_key = f"{acc}_{code}"

        buy_amt = qty * buy_price
        now_amt = qty * current_price
        prev_amt = prev_snapshot.get(snapshot_key, now_amt)

        today_snapshot[snapshot_key] = now_amt

        if acc not in accounts_items:
            accounts_items[acc] = []
            accounts_totals[acc] = {"buy": 0, "now": 0, "prev": 0}

        item_data = {
            "name": item["name"],
            "price": current_price,
            "qty": qty,
            "buy_amt": buy_amt,
            "now_amt": now_amt,
            "prev_amt": prev_amt,
            "profit": now_amt - buy_amt,
            "rate": (now_amt - buy_amt) / buy_amt * 100 if buy_amt > 0 else 0,
            "delta": now_amt - prev_amt
        }
        accounts_items[acc].append(item_data)

        accounts_totals[acc]["buy"] += buy_amt
        accounts_totals[acc]["now"] += now_amt
        accounts_totals[acc]["prev"] += prev_amt

        global_buy += buy_amt
        global_now += now_amt
        global_prev += prev_amt

    # 3. 메시지 생성
    for acc in accounts_items:
        lines.append(f"📂 [{acc} 계좌]")
        lines.append("────────────────────")
        
        acc_total_now = accounts_totals[acc]["now"]
        
        for item in accounts_items[acc]:
            profit_emoji = "🔺" if item["profit"] > 0 else "🔻" if item["profit"] < 0 else "➖"
            delta_emoji = "🔺" if item["delta"] > 0 else "🔻" if item["delta"] < 0 else "➖"
            
            weight = (item["now_amt"] / acc_total_now * 100) if acc_total_now > 0 else 0

            lines.append(
                f"■ {item['name']}\n"
                f"현재가: {item['price']:,}원\n"
                f"수익률: {item['rate']:+.2f}% {profit_emoji}\n"
                f"평가손익: {item['profit']:+,}원\n"
                f"전일 대비: {item['delta']:+,}원 {delta_emoji}\n"
                f"비중: {weight:.1f}%"
            )
            lines.append("- - - - - - - - - -")
        
        acc_buy = accounts_totals[acc]["buy"]
        acc_now = accounts_totals[acc]["now"]
        acc_prev = accounts_totals[acc]["prev"]
        
        acc_profit = acc_now - acc_buy
        acc_rate = (acc_profit / acc_buy * 100) if acc_buy > 0 else 0
        acc_delta = acc_now - acc_prev
        acc_delta_emoji = "🔺" if acc_delta > 0 else "🔻" if acc_delta < 0 else "➖"

        lines.append(f"🧾 {acc} 요약")
        lines.append(f"총 평가금액: {acc_now:,}원")
        lines.append(f"총 수익금: {acc_profit:+,}원")
        lines.append(f"총 수익률: {acc_rate:+.2f}%")
        lines.append(f"전일 대비 합계: {acc_delta:+,}원 {acc_delta_emoji}")
        lines.append("========================\n")

    global_profit = global_now - global_buy
    global_rate = (global_profit / global_buy * 100) if global_buy > 0 else 0
    global_delta = global_now - global_prev
    global_delta_emoji = "🔺" if global_delta > 0 else "🔻" if global_delta < 0 else "➖"

    lines.append("📈 [전체 포트폴리오 요약]")
    lines.append(f"총 평가금액: {global_now:,}원")
    lines.append(f"전체 수익금: {global_profit:+,}원")
    lines.append(f"전체 수익률: {global_rate:+.2f}%")
    lines.append(f"전일 대비 합계: {global_delta:+,}원 {global_delta_emoji}")

    send_telegram("\n".join(lines))

    # =========================
    # 📊 그래프 생성 (폰트 적용)
    # =========================
    acc_names = list(accounts_totals.keys())
    acc_values = [accounts_totals[k]["now"] for k in acc_names]

    plt.figure(figsize=(6, 4))
    bars = plt.bar(acc_names, acc_values, color=['#ff9999', '#66b3ff', '#99ff99'])
    plt.title("계좌별 평가금액 비교", fontsize=15)
    plt.ylabel("평가금액 (원)")
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    
    # 막대 위에 금액 표시
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2.0, height, f'{int(height):,}', ha='center', va='bottom')

    plt.tight_layout()
    plt.savefig(GRAPH_FILE)
    plt.close()

    send_telegram_photo(GRAPH_FILE, caption="📊 계좌별 평가금액 비교")

    save_snapshot(today_snapshot)

if __name__ == "__main__":
    run_report()
    {"account": "IRP", "name": "ACE 미국 나스닥100 미국채 혼합", "code": "438100", "qty": 88, "buy": 14621},
    {"account": "IRP", "name": "TIGER 미국 배당 다우존스", "code": "458730", "qty": 84, "buy": 13100},

    # 개인연금
    {"account": "개인연금", "name": "TIGER KRX 금현물", "code": "0072R0", "qty": 197, "buy": 12211},
    {"account": "개인연금", "name": "KIWOOM 국고채10년", "code": "148070", "qty": 15, "buy": 113824},
    {"account": "개인연금", "name": "KODEX 200TR", "code": "278530", "qty": 153, "buy": 19754},
    {"account": "개인연금", "name": "TIGER 미국 S&P500", "code": "360750", "qty": 128, "buy": 23556},
    {"account": "개인연금", "name": "ACE 미국달러SOFR금리(합성)", "code": "456880", "qty": 144, "buy": 11863},

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
    if not price:
        raise ValueError(f"현재가 조회 실패: {code}")
    return int(price.text.replace(",", ""))

# =========================
# 텔레그램 전송 함수
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
# 스냅샷 처리
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

    # 1. 모든 종목 현재가 미리 조회 (비중 및 통계 계산용)
    prices = {}
    for item in portfolio:
        try:
            prices[item["code"]] = get_current_price(item["code"])
        except Exception as e:
            print(f"Error fetching {item['code']}: {e}")
            prices[item["code"]] = 0 # 에러 시 0 처리 혹은 이전 값 사용 고려
        time.sleep(0.3) # 차단 방지

    # 2. 계좌별 데이터 정리는 딕셔너리로 관리
    # 구조: accounts[계좌명] = [아이템 리스트]
    accounts_items = {}
    accounts_totals = {} # {계좌명: {buy:0, now:0, prev:0}}
    
    # 글로벌 통계
    global_buy = 0
    global_now = 0
    global_prev = 0

    lines = []
    lines.append("📊 연금 / ISA 통합 포트폴리오 리포트")
    lines.append(f"🕒 {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append("")

    # 데이터 집계
    for item in portfolio:
        acc = item["account"]
        code = item["code"]
        qty = item["qty"]
        buy_price = item["buy"]
        current_price = prices[code]

        # 스냅샷 키: 계좌명_종목코드 (같은 종목이 다른 계좌에 있을 수 있음)
        snapshot_key = f"{acc}_{code}"

        buy_amt = qty * buy_price
        now_amt = qty * current_price
        prev_amt = prev_snapshot.get(snapshot_key, now_amt) # 신규 종목은 전일=당일

        # 오늘 스냅샷 저장
        today_snapshot[snapshot_key] = now_amt

        # 계좌별 분류
        if acc not in accounts_items:
            accounts_items[acc] = []
            accounts_totals[acc] = {"buy": 0, "now": 0, "prev": 0}

        item_data = {
            "name": item["name"],
            "price": current_price,
            "qty": qty,
            "buy_amt": buy_amt,
            "now_amt": now_amt,
            "prev_amt": prev_amt,
            "profit": now_amt - buy_amt,
            "rate": (now_amt - buy_amt) / buy_amt * 100 if buy_amt > 0 else 0,
            "delta": now_amt - prev_amt
        }
        accounts_items[acc].append(item_data)

        # 누적 합산
        accounts_totals[acc]["buy"] += buy_amt
        accounts_totals[acc]["now"] += now_amt
        accounts_totals[acc]["prev"] += prev_amt

        global_buy += buy_amt
        global_now += now_amt
        global_prev += prev_amt

    # 3. 메시지 생성 (계좌별 순회)
    for acc in accounts_items:
        lines.append(f"📂 [{acc} 계좌]")
        lines.append("────────────────────")
        
        acc_total_now = accounts_totals[acc]["now"]
        
        # 개별 종목 출력
        for item in accounts_items[acc]:
            profit_emoji = "🔺" if item["profit"] > 0 else "🔻" if item["profit"] < 0 else "➖"
            delta_emoji = "🔺" if item["delta"] > 0 else "🔻" if item["delta"] < 0 else "➖"
            
            # 계좌 내 비중 계산
            weight = (item["now_amt"] / acc_total_now * 100) if acc_total_now > 0 else 0

            lines.append(
                f"■ {item['name']}\n"
                f"현재가: {item['price']:,}원\n"
                f"수익률: {item['rate']:+.2f}% {profit_emoji}\n"
                f"평가손익: {item['profit']:+,}원\n"
                f"전일 대비: {item['delta']:+,}원 {delta_emoji}\n"
                f"비중: {weight:.1f}%"
            )
            lines.append("- - - - - - - - - -")
        
        # 계좌별 요약 출력
        acc_buy = accounts_totals[acc]["buy"]
        acc_now = accounts_totals[acc]["now"]
        acc_prev = accounts_totals[acc]["prev"]
        
        acc_profit = acc_now - acc_buy
        acc_rate = (acc_profit / acc_buy * 100) if acc_buy > 0 else 0
        acc_delta = acc_now - acc_prev
        acc_delta_emoji = "🔺" if acc_delta > 0 else "🔻" if acc_delta < 0 else "➖"

        lines.append(f"🧾 {acc} 요약")
        lines.append(f"총 평가금액: {acc_now:,}원")
        lines.append(f"총 수익금: {acc_profit:+,}원")
        lines.append(f"총 수익률: {acc_rate:+.2f}%")
        lines.append(f"전일 대비 합계: {acc_delta:+,}원 {acc_delta_emoji}")
        lines.append("========================\n")

    # 4. 전체 통합 요약
    global_profit = global_now - global_buy
    global_rate = (global_profit / global_buy * 100) if global_buy > 0 else 0
    global_delta = global_now - global_prev
    global_delta_emoji = "🔺" if global_delta > 0 else "🔻" if global_delta < 0 else "➖"

    lines.append("📈 [전체 포트폴리오 요약]")
    lines.append(f"총 평가금액: {global_now:,}원")
    lines.append(f"전체 수익금: {global_profit:+,}원")
    lines.append(f"전체 수익률: {global_rate:+.2f}%")
    lines.append(f"전일 대비 합계: {global_delta:+,}원 {global_delta_emoji}")

    # 메시지 전송
    send_telegram("\n".join(lines))

    # 5. 그래프 생성 및 전송
    # 계좌별 평가금액 시각화
    acc_names = list(accounts_totals.keys())
    acc_values = [accounts_totals[k]["now"] for k in acc_names]

    plt.figure(figsize=(6, 4))
    bars = plt.bar(acc_names, acc_values, color=['#ff9999', '#66b3ff', '#99ff99'])
    plt.title("계좌별 평가금액 비교", fontsize=15)
    plt.ylabel("평가금액 (원)")
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    
    # 막대 위에 금액 표시
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2.0, height, f'{int(height):,}', ha='center', va='bottom')

    plt.tight_layout()
    plt.savefig(GRAPH_FILE)
    plt.close()

    send_telegram_photo(GRAPH_FILE, caption="📊 계좌별 평가금액 비교")

    # 6. 스냅샷 저장
    save_snapshot(today_snapshot)

# =========================
# 실행
# =========================
if __name__ == "__main__":
    run_report()


