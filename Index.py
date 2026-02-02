import os
import requests
import yfinance as yf
from datetime import datetime

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]


# =============================
# 텔레그램 전송
# =============================
def send_telegram(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    requests.post(url, data={
        "chat_id": CHAT_ID,
        "text": text,
        "disable_web_page_preview": True
    })


# =============================
# 안전 가격 조회 (핵심 안정화)
# =============================
def get_close(ticker):
    try:
        df = yf.Ticker(ticker).history(period="1d")

        if df.empty or df["Close"].dropna().empty:
            return None  # ⭐ 조회 실패

        return round(float(df["Close"].iloc[-1]), 2)

    except:
        return None


# =============================
# 값 표시용 포맷
# =============================
def fmt(value):
    if value is None:
        return "전날 휴장이나 공휴일로 인하여 조회할 수 없습니다."
    return f"{value:,}"


# =============================
# MAIN
# =============================
def main():

    # ========= 미국 =========
    sp500 = get_close("^GSPC")
    nasdaq = get_close("^IXIC")

    # ========= 한국 =========
    kospi = get_close("^KS11")
    kosdaq = get_close("^KQ11")

    # ========= 환율 =========
    usdkrw = get_close("KRW=X")

    # ========= 금 =========
    gold_usd = get_close("GC=F")  # 국제 금 (USD/oz)

    # ========= 기준금리 (수동 입력) =========
    us_rate = "3.75%"
    kr_rate = "2.50%"

    # ========= 금 계산 =========
    if gold_usd is None or usdkrw is None:
        gold_us_text = "전날 휴장이나 공휴일로 인하여 조회할 수 없습니다."
        gold_kr_text = "전날 휴장이나 공휴일로 인하여 조회할 수 없습니다."
    else:
        gold_krw_oz = gold_usd * usdkrw

        # ⭐ 1돈 = 3.75g / 1oz = 31.1035g
        gold_per_don = round(gold_krw_oz * (3.75 / 31.1035))

        gold_us_text = f"{gold_usd:,} USD/oz"
        gold_kr_text = f"{gold_per_don:,} 원/돈"

    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    # =============================
    # 메시지 생성
    # =============================
    message = (
        f"📊 시장 요약 ({now})\n\n"

        f"🇺🇸 미국\n"
        f"🟢 S&P500 : {fmt(sp500)}\n"
        f"🔵 NASDAQ : {fmt(nasdaq)}\n"
        f"🏦 기준금리(Fed) : {us_rate}\n\n"

        f"🇰🇷 한국\n"
        f"🟡 KOSPI : {fmt(kospi)}\n"
        f"🟣 KOSDAQ : {fmt(kosdaq)}\n"
        f"🏦 기준금리(BoK) : {kr_rate}\n\n"

        f"💱 환율\n"
        f"USD/KRW : {fmt(usdkrw)}\n\n"

        f"🥇 금 시세\n"
        f"🌍 국제 : {gold_us_text}\n"
        f"🇰🇷 한국(1돈) : {gold_kr_text}"
    )

    send_telegram(message)


if __name__ == "__main__":
    main()