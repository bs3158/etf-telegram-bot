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
# 텔레그램 (텍스트 + 사진)
# =============================
def send_telegram(text, photo=None):
    # 메시지 전송
    url_msg = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url_msg, data={
        "chat_id": CHAT_ID,
        "text": text,
        "disable_web_page_preview": True
    })
    
    # 그래프 전송
    if photo:
        url_photo = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
        files = {'photo': photo}
        requests.post(url_photo, data={"chat_id": CHAT_ID}, files=files)

# =============================
# 가격 조회
# =============================
def get_price(ticker):
    try:
        df = yf.Ticker(ticker).history(period="3d") # 여유있게 3일치

        if df.empty or len(df) < 2:
            return None, None

        today = float(df["Close"].iloc[-1])
        prev = float(df["Close"].iloc[-2])

        change = round((today - prev) / prev * 100, 2)
        return round(today, 2), change
    except:
        return None, None

# =============================
# 유틸리티
# =============================
def emoji(change):
    if change is None: return "⚪"
    return "🟢" if change > 0 else "🔴"

def fmt(val, unit="", change=None):
    if val is None: return "조회 불가"
    if change is None: return f"{val:,} {unit}"
    return f"{val:,} {unit} ({change:+.2f}% {emoji(change)})"

# =============================
# 그래프 생성
# =============================
def create_chart(labels, values):
    plt.figure(figsize=(10, 6))
    colors = ['skyblue' if v >= 0 else 'salmon' for v in values]
    
    bars = plt.bar(labels, values, color=colors)
    plt.axhline(0, color='black', linewidth=0.8) # 0선
    plt.title("Daily Change Rate (%)", fontsize=15)
    plt.ylabel("Change (%)")
    plt.grid(axis='y', linestyle='--', alpha=0.7)

    # 막대 위에 숫자 표시
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2, yval, f"{yval:+.2f}%", 
                 va='bottom' if yval > 0 else 'top', ha='center', fontsize=10, fontweight='bold')

    # 메모리에 저장
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
    
    gold_usd, gold_ch = get_price("GC=F")      # 금
    silver_usd, silver_ch = get_price("SI=F")    # 은 (추가)
    copper_usd, cu_ch = get_price("HG=F")      # 구리
    oil_usd, oil_ch = get_price("CL=F")        # 유가
    btc_usd, btc_ch = get_price("BTC-USD")     # 비트코인

    # 환산 계산 (금/은)
    def to_krw_don(usd_price):
        if usd_price and usdkrw:
            return (usd_price * usdkrw) / 31.1035 * 3.75
        return None

    gold_krw_don = to_krw_don(gold_usd)
    silver_krw_don = to_krw_don(silver_usd)

    # 금리 (수동)
    us_rate, kr_rate = "4.50%", "3.25%" # 2026년 기준 예시값으로 업데이트

    # 메시지 작성
    message = (
        f"📊 시장 요약 ({now})\n\n"
        f"🇺🇸 미국\nS&P500 : {fmt(sp500, '', sp_ch)}\nNASDAQ : {fmt(nasdaq, '', na_ch)}\n기준금리 : {us_rate}\n\n"
        f"🇰🇷 한국\nKOSPI : {fmt(kospi, '', ko_ch)}\nKOSDAQ : {fmt(kosdaq, '', kq_ch)}\n기준금리 : {kr_rate}\n\n"
        f"💱 환율\nUSD/KRW : {fmt(usdkrw, '원', fx_ch)}\n\n"
        f"🥇 금 시세\n국제 : {fmt(gold_usd, 'USD/oz', gold_ch)}\n한국 : {fmt(round(gold_krw_don,0) if gold_krw_don else None, '원/돈')}\n\n"
        f"🥈 은 시세\n국제 : {fmt(silver_usd, 'USD/oz', silver_ch)}\n한국 : {fmt(round(silver_krw_don,0) if silver_krw_don else None, '원/돈')}\n\n"
        f"🔩 구리 : {fmt(copper_usd, 'USD/lb', cu_ch)}\n"
        f"🛢 유가(WTI) : {fmt(oil_usd, 'USD/bbl', oil_ch)}\n"
        f"₿ 비트코인 : {fmt(btc_usd, 'USD', btc_ch)}"
    )

    # 그래프 데이터 구성 (요청하신 순서)
    chart_labels = ['KOSPI', 'KOSDAQ', 'S&P500', 'NASDAQ', 'Gold', 'Silver', 'Copper', 'Oil', 'BTC']
    chart_values = [v if v is not None else 0 for v in [ko_ch, kq_ch, sp_ch, na_ch, gold_ch, silver_ch, cu_ch, oil_ch, btc_ch]]

    # 그래프 생성 및 전송
    chart_img = create_chart(chart_labels, chart_values)
    send_telegram(message, chart_img)

if __name__ == "__main__":
    main()
