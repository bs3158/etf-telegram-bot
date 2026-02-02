import os
import requests
import yfinance as yf
import pytz
from datetime import datetime
from bs4 import BeautifulSoup

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

KST = pytz.timezone("Asia/Seoul")
NY = pytz.timezone("America/New_York")


# ===========================
# 텔레그램 메시지 전송
# ===========================
def send_telegram(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={
        "chat_id": CHAT_ID,
        "text": text,
        "disable_web_page_preview": True
    })


# ===========================
# yfinance 기반 시세 조회
# ===========================
def get_price_info(ticker, realtime=False):
    try:
        t = yf.Ticker(ticker)

        if realtime:
            df = t.history(period="2d", interval="1m")
        else:
            df = t.history(period="2d")

        if len(df) < 2:
            return None

        now = float(df["Close"].iloc[-1])
        prev = float(df["Close"].iloc[-2])

        change = now - prev
        pct = (change / prev) * 100

        return round(now, 2), round(pct, 2)

    except:
        return None


# ===========================
# 한국금거래소 금 현물 시세 크롤링
# ===========================
def get_krx_gold_price():
    try:
        # 아래는 예시 HTML 타겟 (수정 필요할 수 있음)
        url = "https://gold.or.kr/market/index.jsp"
        res = requests.get(url, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")

        # 실제 구조에 맞게 선택자 수정 필요
        price_el = soup.select_one(".tbl_type1 .tc:nth-child(2)")
        if price_el:
            price_gram = int(price_el.get_text(strip=True).replace(",", ""))
            # 1돈 = 3.75g
            price_don = round(price_gram * 3.75)
            return price_gram, price_don
        return None
    except:
        return None


# ===========================
# 상승/하락 텍스트
# ===========================
def fmt(info, usdkrw=None, unit=""):
    if info is None:
        return "조회 불가"
    price, pct = info

    if usdkrw:
        price_krw = round(price * usdkrw)
        price_str = f"{price:,} {unit} (≈ {price_krw:,} KRW)"
    else:
        price_str = f"{price:,} {unit}"

    if pct > 0:
        icon = "🔴▲"
    elif pct < 0:
        icon = "🔵▼"
    else:
        icon = "⚪"

    return f"{price_str} ({pct:+.2f}%) {icon}"


# ===========================
# 시장 시간 판단
# ===========================
def is_korea_open():
    now = datetime.now(KST)
    return now.weekday() < 5 and 9 <= now.hour < 15


def is_us_open():
    now = datetime.now(NY)
    return now.weekday() < 5 and 9 <= now.hour < 16


# ===========================
# MAIN
# ===========================
def main():

    kr_live = is_korea_open()
    us_live = is_us_open()

    # ========== 지수 ==========
    sp500 = get_price_info("^GSPC", us_live)
    nasdaq = get_price_info("^IXIC", us_live)
    kospi = get_price_info("^KS11", kr_live)
    kosdaq = get_price_info("^KQ11", kr_live)

    # ========== 환율 ==========
    usdkrw = get_price_info("KRW=X", True)
    usdkrw_val = usdkrw[0] if usdkrw else None

    # ========== 금 국제 ==========
    gold_intl = get_price_info("GC=F", True)

    # 1돈 환산 (국제)
    if gold_intl and usdkrw_val:
        gold_don_krw = round(gold_intl[0] * usdkrw_val / 8.294)
    else:
        gold_don_krw = None

    # ========== 한국 금현물 ==========
    krx_gold = get_krx_gold_price()  # (gram, don)

    # ========== 원자재 ==========
    copper = get_price_info("HG=F", True)  # USD/lb
    oil = get_price_info("CL=F", True)     # USD/bbl

    # ========== 암호화폐 ==========
    btc = get_price_info("BTC-USD", True)  # USD

    now = datetime.now(KST).strftime("%Y-%m-%d %H:%M")

    message = f"📊 시장 요약 ({now})\n\n"

    # 지수
    message += "📈 지수\n"
    message += f"S&P500: {fmt(sp500)}\n"
    message += f"NASDAQ: {fmt(nasdaq)}\n"
    message += f"KOSPI: {fmt(kospi)}\n"
    message += f"KOSDAQ: {fmt(kosdaq)}\n\n"

    # 환율
    message += "💱 환율\n"
    message += f"USD/KRW: {fmt(usdkrw)}\n\n"

    # 금
    message += "🥇 금\n"
    message += f"국제 금: {fmt(gold_intl, usdkrw_val, 'USD/oz')}\n"
    message += f"국제 금(1돈 환산): {gold_don_krw:,} KRW/돈\n" if gold_don_krw else "국제 금(1돈 환산): 조회 불가\n"

    if krx_gold:
        gram, don_price = krx_gold
        message += f"한국 금현물: {gram:,} KRW/g (약 {don_price:,} KRW/돈)\n"
    else:
        message += "한국 금현물: 조회 불가\n"

    message += "\n"

    # 구리, 유가, 비트코인
    message += "🔶 원자재/암호화폐\n"
    message += f"구리 (Copper): {fmt(copper, usdkrw_val, 'USD/lb')}\n"
    message += f"유가 (WTI): {fmt(oil, usdkrw_val, 'USD/bbl')}\n"
    message += f"비트코인 (BTC): {fmt(btc, usdkrw_val, 'USD')}\n"

    send_telegram(message)


if __name__ == "__main__":
    main()