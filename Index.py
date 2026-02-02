import os
import requests
import yfinance as yf
from datetime import datetime
import pytz


BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

KST = pytz.timezone("Asia/Seoul")
NY = pytz.timezone("America/New_York")


# =========================
# 텔레그램
# =========================
def send_telegram(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={
        "chat_id": CHAT_ID,
        "text": text,
        "disable_web_page_preview": True
    })


# =========================
# 안전 가격 조회 (핵심 수정)
# =========================
def get_price(ticker, realtime=False):
    try:
        t = yf.Ticker(ticker)

        if realtime:
            df = t.history(period="1d", interval="1m")
        else:
            df = t.history(period="1d")

        if df.empty:
            return None

        return round(float(df["Close"].iloc[-1]), 2)

    except:
        return None


# =========================
# 장 시간 체크
# =========================
def is_korea_open():
    now = datetime.now(KST)
    return now.weekday() < 5 and 9 <= now.hour < 15


def is_us_open():
    now = datetime.now(NY)
    return now.weekday() < 5 and 9 <= now.hour < 16


# =========================
# 포맷 안전 함수 (핵심 추가)
# =========================
def fmt(v):
    if v is None:
        return "전날 휴장이나 공휴일로 인하여 조회할 수 없습니다."
    return f"{v:,}"


# =========================
# MAIN
# =========================
def main():

    kr_live = is_korea_open()
    us_live = is_us_open()

    sp500 = get_price("^GSPC", us_live)
    nasdaq = get_price("^IXIC", us_live)
    kospi = get_price("^KS11", kr_live)
    kosdaq = get_price("^KQ11", kr_live)
    usdkrw = get_price("KRW=X", True)
    gold_usd = get_price("GC=F", True)

    us_rate = "3.75%"
    kr_rate = "2.50%"

    gold_krw_don = None
    if gold_usd and usdkrw:
        oz_to_don = 31.1035 / 3.75
        gold_krw_don = round(gold_usd * usdkrw / oz_to_don, 0)

    now = datetime.now(KST).strftime("%Y-%m-%d %H:%M")

    message = (
        f"📊 시장 요약 ({now})\n\n"

        f"🇺🇸 미국\n"
        f"S&P500 : {fmt(sp500)} 🔵\n"
        f"NASDAQ : {fmt(nasdaq)} 🔵\n"
        f"기준금리(Fed) : {us_rate}\n\n"

        f"🇰🇷 한국\n"
        f"KOSPI : {fmt(kospi)} 🔴\n"
        f"KOSDAQ : {fmt(kosdaq)} 🔴\n"
        f"기준금리(BoK) : {kr_rate}\n\n"

        f"💱 환율\n"
        f"USD/KRW : {fmt(usdkrw)}\n\n"

        f"🥇 금 시세\n"
        f"국제 : {fmt(gold_usd)} USD/oz\n"
        f"한국(1돈) : {fmt(gold_krw_don)} 원"
    )

    send_telegram(message)


if __name__ == "__main__":
    main()