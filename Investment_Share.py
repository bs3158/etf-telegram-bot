import yfinance as yf
import pandas as pd
import requests
from bs4 import BeautifulSoup
import telegram
import asyncio
import os
import sys

# --- 환경 변수 설정 (GitHub Secrets 사용 권장) ---
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
INPUT_FILE = "input.xlsx"

async def send_telegram_msg(text):
    bot = telegram.Bot(token=BOT_TOKEN)
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
        
        name_tag = soup.select_one(".wrap_company h2 a")
        price_tag = soup.select_one("p.no_today span.blind")
        
        if name_tag and price_tag:
            name = name_tag.text
            price = int(price_tag.text.replace(",", ""))
            return name, price, "KRW"
    except: pass
    
    # 2. 야후 시도 (해외)
    try:
        ticker = yf.Ticker(code)
        name = ticker.info.get('longName') or ticker.info.get('shortName') or code
        p = ticker.fast_info.last_price
        
        if p: return name, p * current_rate, f"USD (${p:.2f})"
    except: pass
    return None, None, None

async def main():
    try:
        # 1. 엑셀 파일 존재 여부 확인
        if not os.path.exists(INPUT_FILE):
            print(f"Error: {INPUT_FILE} 파일을 찾을 수 없습니다.")
            return

        # 2. 엑셀 데이터 읽기
        df = pd.read_excel(INPUT_FILE)
        df = df.dropna(subset=['Symbol', 'Weight'])
        total_budget = df['Total_Budget'].iloc[0]
        
        # 3. 비중 합계 검증
        total_weight = df['Weight'].sum()
        if abs(total_weight - 100) > 0.01:
            msg = (
                f"<b>⚠️ 투자 비중 설정 오류</b>\n\n"
                f"현재 입력된 비중 합계: <b>{total_weight}%</b>\n"
                f"정확히 <b>100%</b>가 되도록 수정 후 다시 실행해 주세요."
            )
            await send_telegram_msg(msg)
            return

        # 4. 환율 및 시세 계산 시작
        rate = get_exchange_rate()
        total_remaining_cash = 0 # 최종 남은 예수금 합계
        
        report = [
            f"<b>📝 자산 배분 매수 리포트</b>",
            f"<code>────────────────────</code>",
            f"💵 <b>기준 환율:</b> {rate:,.2f} 원",
            f"📦 <b>대상 종목:</b> {len(df)} 개",
            f"💰 <b>총 투자금:</b> {total_budget:,.0f} 원",
            f"<code>────────────────────</code>\n"
        ]

        for _, row in df.iterrows():
            code = str(row['Symbol']).strip().upper()
            weight = float(row['Weight'])
            
            name, price_krw, label = fetch_price(code, rate)
            
            if price_krw:
                budget = total_budget * (weight / 100)
                qty = int(budget // price_krw)
                spent = qty * price_krw
                remaining = budget - spent # 해당 종목 할당금 중 남은 금액
                total_remaining_cash += remaining # 전체 예수금에 합산
                
                report.append(f"<b>🔹 {name}</b> (<code>{code}</code>)")
                report.append(f"  └ 비중: <b>{weight}%</b> (할당: {budget:,.0f}원)")
                report.append(f"  └ 현재가: <code>{label}</code>")
                report.append(f"  └ <b>매수 수량: {qty} 주</b>")
                report.append(f"  └ 남은잔액: {remaining:,.0f} 원")
                report.append("") 
            else:
                report.append(f"❌ <b>{code}</b>: 시세 조회 실패\n")

        # 최하단에 합계 정보 추가
        report.append(f"<code>────────────────────</code>")
        report.append(f"☕ <b>최종 예상 예수금: {total_remaining_cash:,.0f} 원</b>")
        report.append(f"✅ 모든 계산이 완료되었습니다.")

        # 5. 결과 전송
        await send_telegram_msg("\n".join(report))
        print("Telegram 리포트 전송 완료")

    except Exception as e:
        await send_telegram_msg(f"⚠️ <b>시스템 오류 발생</b>\n<code>{str(e)}</code>")

if __name__ == "__main__":
    asyncio.run(main())
