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
# 가격 조회 (현재 + 전일)
# =========================
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


# =========================
# 포맷 + 이모지
# =========================
def fmt(info):
    if info is None:
        return "조회불가"

    price, pct = info

    if pct > 0:
        icon = "🔴▲"
    elif pct < 0:
        icon = "🔵▼"
    else:
        icon = "⚪"

    return f"{price:,} ({pct:+.2f}%) {icon}"


# =========================
# 장 시간
# =========================
def is_korea_open():
    now = datetime.now(KST)
    return now.weekday() < 5 and 9 <= now.hour < 15


def is_us_open():
    now = datetime.now(NY)
    return now.weekday() < 5 and 9 <= now.hour < 16


# =========================
# MAIN
# =========================
def main():

    kr_live = is_korea_open()
    us_live = is_us_open()

    # ===== 지수 =====
    sp500 = get_price_info("^GSPC", us_live)
    nasdaq = get_price_info("^IXIC", us_live)
    kospi = get_price_info("^KS11", kr_live)
    kosdaq = get_price_info("^KQ11", kr_live)

    # ===== 환율 =====
    usdkrw = get_price_info("KRW=X", True)

    # ===== 금 =====
    gold = get_price_info("GC=F", True)

    gold_don = "조회불가"
    if gold and usdkrw:
        gold_usd, _ = gold
        usd, _ = usdkrw

        krw_oz = gold_usd * usd
        gold_don = f"{round(krw_oz/8.294):,} 원/돈"

    krx_gold = get_price_info("132030.KS", kr_live)
    krx_gold_don = "조회불가"
    if krx_gold:
        krx_gold_don = f"{round(krx_gold[0]/8.294):,} 원/돈"

    # ===== 추가 자산 =====
    copper = get_price_info("HG=F", True)
    oil = get_price_info("CL=F", True)          # WTI
    btc = get_price_info("BTC-USD", True)       # 비트코인

    # 금리 (수동)
    us_rate = "3.75%"
    kr_rate = "2.50%"

    now = datetime.now(KST).strftime("%Y-%m-%d %H:%M")

    message = (
        f"📊 시장 요약 ({now})\n\n"

        f"🇺🇸 미국\n"
        f"S&P500 : {fmt(sp500)}\n"
        f"NASDAQ : {fmt(nasdaq)}\n"
        f"기준금리(Fed) : {us_rate}\n\n"

        f"🇰🇷 한국\n"
        f"KOSPI : {fmt(kospi)}\n"
        f"KOSDAQ : {fmt(kosdaq)}\n"
        f"기준금리(BoK) : {kr_rate}\n\n"

        f"💱 환율\n"
        f"USD/KRW : {fmt(usdkrw)}\n\n"

        f"🥇 금\n"
        f"국제 : {fmt(gold)}\n"
        f"1돈 환산 : {gold_don}\n"
        f"한국(KRX) : {krx_gold_don}\n\n"

        f"🔶 원자재\n"
        f"구리 : {fmt(copper)}\n"
        f"유가(WTI) : {fmt(oil)}\n\n"

        f"🪙 암호화폐\n"
        f"Bitcoin : {fmt(btc)}"
    )

    send_telegram(message)


if __name__ == "__main__":
    main()