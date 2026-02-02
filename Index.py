import os
import requests
import yfinance as yf
import matplotlib.pyplot as plt
from datetime import datetime
from zoneinfo import ZoneInfo
import io

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

# =============================
# 텔레그램 전송
# =============================
def send_telegram(text, photo=None):
    url_msg = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url_msg, data={
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    })
    
    if photo:
        url_photo = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
        files = {'photo': photo}
        requests.post(url_photo, data={"chat_id": CHAT_ID}, files=files)

# =============================
# 가격 조회
# =============================
def get_price(ticker):
    try:
        df = yf.Ticker(ticker).history(period="3d")
        if df.empty or len(df) < 2:
            return None, None
        today = float(df["Close"].iloc[-1])
        prev = float(df["Close"].iloc[-2])
        change = round((today - prev) / prev * 100, 2)
        return round(today, 2), change
    except:
        return None, None

# =============================
# ⭐ 이모지 통일 (상승 ⬆️ / 하락 ⬇️ / 보합 -)
# =============================
def get_indicator(change):
    if change is None: return "-"
    if change > 0: return "⬆️" # 상승: 빨간색 계열 위쪽 화살표
    if change < 0: return "⬇️" # 하락: 파란색 계열 아래쪽 화살표
    return "-"

def fmt(val, unit="", change=None):
    if val is None: return "조회 불가"
    # 소수점 2자리까지 표시 (금액 성격에 따라 조정 가능)
    formatted_val = f"{val:,.2f}" if val < 1000 else f"{val:,.0f}"
    
    if change is None: return f"<b>{formatted_val} {unit}</b>"
    
    indicator = get_indicator(change)
    return f"<b>{formatted_val} {unit}</b> ({change:+.2f}% {indicator})"

# =============================
# 그래프 생성
# =============================
def create_chart(labels, values):
    plt.figure(figsize=(10, 6))
    # 상승 빨강(#ff4d4d), 하락 파랑(#4d94ff)
    colors = ['#ff4d4d' if v > 0 else '#4d94ff' if v < 0 else '#808080' for v in values]
    
    bars = plt.bar(labels, values, color=colors)
    plt.axhline(0, color='black', linewidth=0.8)
    plt.title("Market Change Rate (%)", fontsize=15, fontweight='bold')
    plt.ylabel("Change (%)")
    plt.grid(axis='y', linestyle='--', alpha=0.5)

    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2, yval, f"{yval:+.2f}%", 
                 va='bottom' if yval >= 0 else 'top', ha='center', fontsize=10, fontweight='bold')

    img_buf = io.BytesIO()
    plt.savefig(img_buf, format='png', bbox_inches='tight')
    img_buf.seek(0)
    plt.close()
    return img_buf

# =============================
# MAIN
# =============================
def main():
    now = datetime.now(ZoneInfo("Asia/Seoul")).strftime("%Y-%m-%d %H:%M")

    # 데이터 수집
    sp500, sp_ch = get_price("^GSPC")
    nasdaq, na_ch = get_price("^IXIC")
    kospi, ko_ch = get_price("^KS11")
    kosdaq, kq_ch = get_price("^KQ11")
    usdkrw, fx_ch = get_price("KRW=X")
    gold_usd, gold_ch = get_price("GC=F")
    silver_usd, silver_ch = get_price("SI=F")
    copper_usd, cu_ch = get_price("HG=F")
    oil_usd, oil_ch = get_price("CL=F")
    btc_usd, btc_ch = get_price("BTC-USD")

    # 환산 계산
    rate = usdkrw if usdkrw else 1450.0
    gold_krw_don = (gold_usd * rate / 31.1035 * 3.75) if gold_usd else None
    silver_krw_don = (silver_usd * rate / 31.1035 * 3.75) if silver_usd else None

    # 메시지 작성
    message = (
        f"📊 <b>시장 요약 ({now})</b>\n\n"
        f"🇺🇸 <b>미국</b>\n"
        f"S&P500 : {fmt(sp500, '', sp_ch)}\n"
        f"NASDAQ : {fmt(nasdaq, '', na_ch)}\n"
        f"기준금리 : 4.50%\n\n"
        f"🇰🇷 <b>한국</b>\n"
        f"KOSPI : {fmt(kospi, '', ko_ch)}\n"
        f"KOSDAQ : {fmt(kosdaq, '', kq_ch)}\n"
        f"기준금리 : 3.25%\n\n"
        f"💱 <b>환율</b>\n"
        f"USD/KRW : {fmt(usdkrw, '원', fx_ch)}\n\n"
        f"🥇 <b>금 시세</b>\n"
        f"국제 : {fmt(gold_usd, 'USD/oz', gold_ch)}\n"
        f"한국 : {fmt(gold_krw_don, '원/돈')}\n\n"
        f"🥈 <b>은 시세</b>\n"
        f"국제 : {fmt(silver_usd, 'USD/oz', silver_ch)}\n"
        f"한국 : {fmt(silver_krw_don, '원/돈')}\n\n"
        f"🔩 구리 : {fmt(copper_usd, 'USD/lb', cu_ch)}\n"
        f"🛢 유가(WTI) : {fmt(oil_usd, 'USD/bbl', oil_ch)}\n"
        f"₿ 비트코인 : {fmt(btc_usd, 'USD', btc_ch)}"
    )

    # 그래프 데이터 구성
    labels = ['KOSPI', 'KOSDAQ', 'S&P500', 'NASDAQ', 'Gold', 'Silver', 'Copper', 'Oil', 'BTC']
    values = [v if v is not None else 0 for v in [ko_ch, kq_ch, sp_ch, na_ch, gold_ch, silver_ch, cu_ch, oil_ch, btc_ch]]

    chart_img = create_chart(labels, values)
    send_telegram(message, chart_img)

if __name__ == "__main__":
    main()
