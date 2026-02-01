import yfinance as yf
import pandas as pd
import requests
from bs4 import BeautifulSoup
import telegram
import asyncio
import os
import sys

# --- 환경 변수 설정 (GitHub Secrets 사용 권장) ---
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
INPUT_FILE = "input.xlsx"

async def send_telegram_msg(text):
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    await bot.send_message(chat_id=CHAT_ID, text=text, parse_mode='HTML')

def get_exchange_rate():
    try:
        rate = yf.Ticker("USDKRW=X").fast_info.last_price
        return rate if rate else 1350.0
    except:
        return 1350.0

def fetch_price(code, current_rate):
    # 1. 네이버 시도 (국내)
    try:
        url = f"https://finance.naver.com/item/main.naver?code={code}"
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=3)
        soup = BeautifulSoup(res.text, "html.parser")
        tag = soup.select_one("p.no_today span.blind")
        if tag: return int(tag.text.replace(",", "")), "KRW"
    except: pass
    
    # 2. 야후 시도 (해외)
    try:
        p = yf.Ticker(code).fast_info.last_price
        if p: return p * current_rate, f"USD (${p:.2f})"
    except: pass
    return None, None

async def main():
    try:
        # 1. 엑셀 파일 존재 여부 확인
        if not os.path.exists(INPUT_FILE):
            print(f"Error: {INPUT_FILE} 파일을 찾을 수 없습니다.")
            return

        # 2. 엑셀 데이터 읽기
        df = pd.read_excel(INPUT_FILE)
        
        # 비어있는 행 제거 및 종목 수 파악
        df = df.dropna(subset=['Symbol', 'Weight'])
        total_budget = df['Total_Budget'].iloc[0]
        
        # 3. 비중 합계 검증
        total_weight = df['Weight'].sum()
        if abs(total_weight - 100) > 0.01:
            msg = f"⚠️ <b>투자 비중 오류</b>\n현재 입력된 비중의 합이 <b>{total_weight}%</b>입니다.\n합계를 100%로 맞춰서 다시 입력해주세요."
            await send_telegram_msg(msg)
            return

        # 4. 환율 및 시세 계산 시작
        rate = get_exchange_rate()
        report = [f"<b>📊 수동 실행 매수 리포트</b>"]
        report.append(f"기준 환율: {rate:,.2f}원 (종목 수: {len(df)}개)\n" + "="*25)

        for _, row in df.iterrows():
            code = str(row['Symbol']).strip().upper()
            weight = float(row['Weight'])
            
            price_krw, label = fetch_price(code, rate)
            
            if price_krw:
                budget = total_budget * (weight / 100)
                qty = int(budget // price_krw)
                report.append(f"📍 <b>{code}</b> ({weight}%)")
                report.append(f"  • 현재가: {label}")
                report.append(f"  • 매수 수량: <b>{qty}주</b>")
                report.append("-" * 20)
            else:
                report.append(f"❌ {code}: 시세 조회 실패")

        # 5. 결과 전송
        await send_telegram_msg("\n".join(report))
        print("Telegram 리포트 전송 완료")

    except Exception as e:
        await send_telegram_msg(f"⚠️ 시스템 오류 발생: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
