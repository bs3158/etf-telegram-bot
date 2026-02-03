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
    if change > 0: return "⬆️"
    if change < 0: return "⬇️"
    return "-"

def fmt(val, unit="", change=None):
    if val is None: return "조회 불가"
    formatted_val = f"{val:,.2f}" if val < 1000 else f"{val:,.0f}"
    if change is None: return f"<b>{formatted_val} {unit}</b>"
    indicator = get_indicator(change)
    return f"<b>{formatted_val} {unit}</b> ({change:+.2f}% {indicator})"

# =============================
# 그래프 생성 (가격 표시 추가)
# =============================
def create_chart(labels, values, prices):
    plt.figure(figsize=(12, 7))
    colors = ['#ff4d4d' if v > 0 else '#4d94ff' if v < 0 else '#808080' for v in values]
    
    bars = plt.bar(labels, values, color=colors)
    plt.axhline(0, color='black', linewidth=0.8)
    plt.title("Market Change Rate (%) & Current Price", fontsize=15, fontweight='bold')
    plt.ylabel("Change (%)")
    plt.grid(axis='y', linestyle='--', alpha=0.5)

    # 막대 위/아래에 정보 표시
    for bar, val, price in zip(bars, values, prices):
        yval = bar.get_height()
        
        # 1. 증감률(%) 표시 (막대 끝 부분)
        plt.text(bar.get_x() + bar.get_width()/2, yval, f"{val:+.2f}%", 
                 va='bottom' if yval >= 0 else 'top', ha='center', 
                 fontsize=10, fontweight='bold')
        
        # 2. 현재 가격 표시 (막대 중간 또는 0선 근처)
        # 텍스트가 겹치지 않도록 yval의 위치에 따라 높낮이 조절
        price_y_pos = yval / 2 if abs(yval) > 2 else (1.5 if yval >= 0 else -1.5)
        plt.text(bar.get_x() + bar.get_width()/2, price_y_pos, f"{price}", 
                 va='center', ha='center', fontsize=9, 
                 fontweight='bold', color='black',
                 bbox=dict(facecolor='white', alpha=0.6, edgecolor='none', pad=1))

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

    # 그래프 데이터 구성 (가격 포맷팅 포함)
    labels = ['KOSPI', 'KOSDAQ', 'S&P500', 'NASDAQ', 'Gold', 'Silver', 'Copper', 'Oil', 'BTC']
    
    # 증감률 데이터
    values = [v if v is not None else 0 for v in [ko_ch, kq_ch, sp_ch, na_ch, gold_ch, silver_ch, cu_ch, oil_ch, btc_ch]]
    
    # 표시할 가격 데이터 (단위 포함)
    chart_prices = [
        f"{kospi:,.0f}" if kospi else "0",
        f"{kosdaq:,.0f}" if kosdaq else "0",
        f"{sp500:,.0f}" if sp500 else "0",
        f"{nasdaq:,.0f}" if nasdaq else "0",
        f"{gold_krw_don:,.0f}원/돈" if gold_krw_don else "0",
        f"{silver_krw_don:,.0f}원/돈" if silver_krw_don else "0",
        f"{copper_usd:,.2f}USD/lb" if copper_usd else "0",
        f"{oil_usd:,.2f}USD/bbl" if oil_usd else "0",
        f"${btc_usd:,.0f}" if btc_usd else "0"
    ]

    chart_img = create_chart(labels, values, chart_prices)
    send_telegram(message, chart_img)

if __name__ == "__main__":
    main()
