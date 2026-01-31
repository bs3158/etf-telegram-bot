import os
import requests
import yfinance as yf
from datetime import datetime


BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]


def send_telegram(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    requests.post(url, data={
        "chat_id": CHAT_ID,
        "text": text,
        "disable_web_page_preview": True
    })


def get_close(ticker):
    df = yf.Ticker(ticker).history(period="1d")
    return round(float(df["Close"].iloc[-1]), 2)


def main():

    # 미국
    sp500 = get_close("^GSPC")
    nasdaq = get_close("^IXIC")
    gold_usd = get_close("GC=F")  # ✅ (기존 누락 보완)

    # 한국
    kospi = get_close("^KS11")
    kosdaq = get_close("^KQ11")

    # 환율
    usdkrw = get_close("KRW=X")

    # 기준금리 (수동/고정)
    us_rate = "3.75%"
    kr_rate = "2.50%"

    # ✅ 1돈 가격 계산
    gold_krw_per_don = round(gold_usd * usdkrw * (3.75 / 31.1035), 0)

    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    message = (
        f"📊 시장 요약 ({now})\n\n"
        f"🇺🇸 미국\n"
        f"🟢 S&P500 : {sp500}\n"
        f"🟢 NASDAQ : {nasdaq}\n"
        f"🟡 기준금리(Fed) : {us_rate}\n\n"
        f"🇰🇷 한국\n"
        f"🔵 KOSPI : {kospi}\n"
        f"🔵 KOSDAQ : {kosdaq}\n"
        f"🟡 기준금리(BoK) : {kr_rate}\n\n"
        f"💱 환율\n"
        f"🟣 USD/KRW : {usdkrw}\n\n"
        f"🥇 금 시세\n"
        f"🟠 국제 : {gold_usd} USD/oz\n"
        f"🟡 한국 환산 : 약 {gold_krw_per_don:,.0f}원 / 1돈"
    )

    send_telegram(message)


if __name__ == "__main__":
    main()
