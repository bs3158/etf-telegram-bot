import os
import requests
import yfinance as yf
import pytz
from datetime import datetime, time


# =============================
# Telegram
# =============================
BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]


def send_telegram(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    res = requests.post(url, data={
        "chat_id": CHAT_ID,
        "text": text,
        "disable_web_page_preview": True
    })

    print(res.status_code, res.text)


# =============================
# Timezone (DST 자동 적용)
# =============================
KST = pytz.timezone("Asia/Seoul")
NY = pytz.timezone("America/New_York")


# =============================
# 시장 시간 판단
# =============================
def is_korea_open(now):
    return time(9, 0) <= now.time() <= time(15, 30)


def is_us_open():
    now = datetime.now(NY)
    return time(9, 30) <= now.time() <= time(16, 0)


# =============================
# 가격 조회 (실시간 + 종가 + 휴장 처리)
# =============================
def get_price(ticker, market="KR"):

    try:
        now_kst = datetime.now(KST)

        if market == "KR":
            if is_korea_open(now_kst):
                df = yf.Ticker(ticker).history(period="1d", interval="1m")
            else:
                df = yf.Ticker(ticker).history(period="1d")

        else:  # US
            if is_us_open():
                df = yf.Ticker(ticker).history(period="1d", interval="1m")
            else:
                df = yf.Ticker(ticker).history(period="1d")

        if df.empty or df["Close"].dropna().empty:
            return None

        return round(float(df["Close"].iloc[-1]), 2)

    except:
        return None


# =============================
# None 처리
# =============================
def safe(v):
    if v is None:
        return "❌ 전날 휴장이나 공휴일로 인하여 조회할 수 없습니다."
    return v


# =============================
# 메인
# =============================
def main():

    # 🇺🇸 미국
    sp500 = get_price("^GSPC", "US")
    nasdaq = get_price("^IXIC", "US")
    gold_usd = get_price("GC=F", "US")

    # 🇰🇷 한국
    kospi = get_price("^KS11", "KR")
    kosdaq = get_price("^KQ11", "KR")

    # 환율
    usdkrw = get_price("KRW=X", "US")

    # 기준금리 (직접 수정 가능)
    us_rate = "3.75%"
    kr_rate = "2.50%"

    # =============================
    # 금 1돈 계산
    # =============================
    if gold_usd and usdkrw:
        gold_krw_oz = gold_usd * usdkrw
        gold_per_don = gold_krw_oz * (3.75 / 31.1035)
        gold_per_don = round(gold_per_don)
    else:
        gold_per_don = None

    now = datetime.now(KST).strftime("%Y-%m-%d %H:%M")

    message = (
        f"📊 시장 요약 ({now})\n\n"

        f"🇺🇸 미국\n"
        f"🟢 S&P500 : {safe(sp500)}\n"
        f"🟢 NASDAQ : {safe(nasdaq)}\n"
        f"🏦 기준금리(Fed) : {us_rate}\n\n"

        f"🇰🇷 한국\n"
        f"🔵 KOSPI : {safe(kospi)}\n"
        f"🔵 KOSDAQ : {safe(kosdaq)}\n"
        f"🏦 기준금리(BoK) : {kr_rate}\n\n"

        f"💱 환율\n"
        f"💵 USD/KRW : {safe(usdkrw)}\n\n"

        f"🥇 금 시세\n"
        f"🌍 국제 : {safe(gold_usd)} USD/oz\n"
        f"🇰🇷 한국(1돈) : {safe(gold_per_don):,} KRW"
    )

    send_telegram(message)


if __name__ == "__main__":
    main()