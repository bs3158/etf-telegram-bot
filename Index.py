import yfinance as yf
import pandas as pd
import requests
from bs4 import BeautifulSoup
import telegram
import asyncio
import os
import sys

# --- 환경 변수 설정 ---
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
INPUT_FILE = "input.txt"

async def send_telegram_msg(text):
    bot = telegram.Bot(token=BOT_TOKEN)
    await bot.send_message(chat_id=CHAT_ID, text=text, parse_mode='HTML')

def get_exchange_rate():
    try:
        # 환율은 유동성이 좋아 1d로 충분함
        rate = yf.Ticker("USDKRW=X").fast_info.last_price
        return rate if rate else 1350.0
    except:
        return 1350.0

def fetch_price(code, current_rate):
    # 1. 국내 시도 (네이버 금융)
    try:
        url = f"https://finance.naver.com/item/main.naver?code={code}"
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=3)
        soup = BeautifulSoup(res.text, "html.parser")
        
        name_tag = soup.select_one(".wrap_company h2 a")
        price_tag = soup.select_one("p.no_today span.blind")
        
        if name_tag and price_tag:
            name = name_tag.text
            price = int(price_tag.text.replace(",", ""))
            return name, price, f"₩{price:,.0f}"
    except: pass
    
    # 2. 해외 시도 (야후 파이낸스)
    try:
        ticker = yf.Ticker(code)
        # 1일치 데이터를 가져와서 비어있는지 확인
        df = ticker.history(period="1d")
        
        if df.empty:
            return None, None, "CLOSED" # 휴장 상태 표시
            
        name = ticker.info.get('longName') or ticker.info.get('shortName') or code
        p = df["Close"].iloc[-1]
        p_krw = p * current_rate
        return name, p_krw, f"${p:,.2f} (₩{p_krw:,.0f})"
    except: pass
    
    return None, None, None

async def main():
    try:
        if not os.path.exists(INPUT_FILE):
            print(f"Error: {INPUT_FILE} 파일을 찾을 수 없습니다.")
            return

        with open(INPUT_FILE, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]
        
        if not lines: return

        total_budget = float(lines[0])
        stock_data = []
        total_weight = 0.0
        for line in lines[1:]:
            parts = line.split(",")
            if len(parts) == 2:
                symbol = parts[0].strip().upper()
                weight = float(parts[1].strip())
                stock_data.append({"Symbol": symbol, "Weight": weight})
                total_weight += weight
        
        if abs(total_weight - 100) > 0.01:
            msg = f"<b>⚠️ 비중 오류: {total_weight}%</b>\n100%로 수정해 주세요."
            await send_telegram_msg(msg)
            return

        rate = get_exchange_rate()
        total_remaining_cash = 0 
        
        report = [
            f"<b>📝 자산 배분 매수 리포트</b>",
            f"<code>────────────────────</code>",
            f"💵 <b>기준 환율:</b> {rate:,.2f} 원",
            f"📦 <b>대상 종목:</b> {len(stock_data)} 개",
            f"💰 <b>총 투자금:</b> {total_budget:,.0f} 원",
            f"<code>────────────────────</code>\n"
        ]

        for item in stock_data:
            code = item["Symbol"]
            weight = item["Weight"]
            name, price_krw, label = fetch_price(code, rate)
            
            if label == "CLOSED":
                report.append(f"<b>🔹 {code}</b> ({weight}%)")
                report.append(f"  └ ⚠️ 전날 휴장이나 공휴일로 인하여 조회할 수 없습니다.\n")
            elif price_krw:
                budget = total_budget * (weight / 100)
                qty = int(budget // price_krw)
                spent = qty * price_krw
                remaining = budget - spent
                total_remaining_cash += remaining
                
                report.append(f"<b>🔹 {name}</b> (<code>{code}</code>)")
                report.append(f"  ├ 비중: <b>{weight}%</b>")
                report.append(f"  ├ 현재가: <code>{label}</code>")
                report.append(f"  └ <b>매수 수량: {qty} 주</b>")
                report.append(f"  └ 남은잔액: {remaining:,.0f} 원")
                report.append("") 
            else:
                report.append(f"❌ <b>{code}</b>: 시세 조회 실패\n")

        report.append(f"<code>────────────────────</code>")
        report.append(f"☕ <b>최종 예상 예수금: {total_remaining_cash:,.0f} 원</b>")
        report.append(f"✅ 계산이 완료되었습니다.")

        await send_telegram_msg("\n".join(report))
        print("Telegram 리포트 전송 완료")
        
    except Exception as e:
        await send_telegram_msg(f"⚠️ 시스템 오류: <code>{str(e)}</code>")

if __name__ == "__main__":
    asyncio.run(main())
