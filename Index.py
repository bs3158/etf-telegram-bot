import os
import requests
import yfinance as yf
from datetime import datetime
from zoneinfo import ZoneInfo

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]


# =============================
# 텔레그램
# =============================
def send_telegram(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    requests.post(url, data={
        "chat_id": CHAT_ID,
        "text": text,
        "disable_web_page_preview": True
    })


# =============================
# 가격 조회 (실시간/종가 자동)
# =============================
def get_price(ticker):
    try:
        df = yf.Ticker(ticker).history(period="2d", interval="1d")

        if df.empty:
            return None, None

        today = float(df["Close"].iloc[-1])
        prev = float(df["Close"].iloc[-2]) if len(df) > 1 else today

        change = round((today - prev) / prev * 100, 2)

        return round(today, 2), change

    except:
        return None, None


# =============================
# 이모지
# =============================
def emoji(change):
    if change is None:
        return "⚪"
    return "🟢" if change > 0 else "🔴"


# =============================
# 안전 출력
# =============================
def fmt(val, unit="", change=None):
    if val is None:
        return "전날 휴장이나 공휴일로 인하여 조회할 수 없습니다."

    if change is None:
        return f"{val:,} {unit}"

    return f"{val:,} {unit} ({change:+.2f}% {emoji(change)})"


# =============================
# MAIN
# =============================
def main():

    now = datetime.now(ZoneInfo("Asia/Seoul")).strftime("%Y-%m-%d %H:%M")

    # 미국
    sp500, sp_ch = get_price("^GSPC")
    nasdaq, na_ch = get_price("^IXIC")

    # 한국
    kospi, ko_ch = get_price("^KS11")
    kosdaq, kq_ch = get_price("^KQ11")

    # 환율
    usdkrw, fx_ch = get_price("KRW=X")

    # 원자재 / 자산
    gold_usd, gold_ch = get_price("GC=F")      # 금
    copper_usd, cu_ch = get_price("HG=F")      # 구리
    oil_usd, oil_ch = get_price("CL=F")        # 유가
    btc_usd, btc_ch = get_price("BTC-USD")     # 비트코인

    # =============================
    # 환산 계산
    # =============================
    if gold_usd and usdkrw:
        gold_krw_oz = gold_usd * usdkrw
        gold_krw_don = gold_krw_oz / 31.1035 * 3.75  # 1돈
    else:
        gold_krw_don = None

    copper_krw = copper_usd * usdkrw if copper_usd and usdkrw else None
    oil_krw = oil_usd * usdkrw if oil_usd and usdkrw else None
    btc_krw = btc_usd * usdkrw if btc_usd and usdkrw else None

    # =============================
    # 기준금리 (수동)
    # =============================
    us_rate = "3.75%"
    kr_rate = "2.50%"

    # =============================
    # 메시지
    # =============================
    message = (
        f"📊 시장 요약 ({now})\n\n"

        f"🇺🇸 미국\n"
        f"S&P500 : {fmt(sp500, '', sp_ch)}\n"
        f"NASDAQ : {fmt(nasdaq, '', na_ch)}\n"
        f"기준금리(Fed) : {us_rate}\n\n"

        f"🇰🇷 한국\n"
        f"KOSPI : {fmt(kospi, '', ko_ch)}\n"
        f"KOSDAQ : {fmt(kosdaq, '', kq_ch)}\n"
        f"기준금리(BoK) : {kr_rate}\n\n"

        f"💱 환율\n"
        f"USD/KRW : {fmt(usdkrw, '원', fx_ch)}\n\n"

        f"🥇 금 시세\n"
        f"국제 : {fmt(gold_usd, 'USD/oz', gold_ch)}\n"
        f"한국 환산 : {fmt(round(gold_krw_don,0) if gold_krw_don else None, '원/돈')}\n\n"

        f"🔩 구리 : {fmt(copper_usd, 'USD/lb', cu_ch)} | {fmt(round(copper_krw,0) if copper_krw else None, '원/lb')}\n"
        f"🛢 유가(WTI) : {fmt(oil_usd, 'USD/bbl', oil_ch)} | {fmt(round(oil_krw,0) if oil_krw else None, '원/bbl')}\n"
        f"₿ 비트코인 : {fmt(btc_usd, 'USD', btc_ch)} | {fmt(round(btc_krw,0) if btc_krw else None, '원')}"
    )

    send_telegram(message)


if __name__ == "__main__":
    main()