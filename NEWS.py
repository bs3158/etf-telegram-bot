import os
import feedparser
import requests
from bs4 import BeautifulSoup
import re
from googletrans import Translator # 번역 라이브러리 추가

# 환경 변수
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

RSS_LIST = [
    "https://www.hankyung.com/feed/economy",
    "https://www.mk.co.kr/rss/30000001/",
    "https://www.cnbc.com/id/10001147/device/rss/rss.html" # 영어 소스
]

translator = Translator()

def translate_text(text):
    try:
        # 텍스트가 영어인지 확인 후 한국어로 번역
        result = translator.translate(text, dest='ko')
        return result.text
    except:
        return text # 오류 발생 시 원문 반환

def get_summary(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(url, timeout=5, headers=headers)
        soup = BeautifulSoup(r.text, "html.parser")
        for s in soup(['script', 'style', 'header', 'footer', 'nav']):
            s.decompose()
        text = soup.get_text(" ", strip=True)
        sentences = re.split(r'(?<=[.!?])\s+', text)
        valid_sentences = [s for s in sentences if len(s) > 30 and len(s) < 200]
        summary = " ".join(valid_sentences[:2])
        return summary if summary else "본문을 가져올 수 없습니다."
    except:
        return "요약을 불러오는 중 오류가 발생했습니다."

def collect_and_send():
    all_news = []
    for rss in RSS_LIST:
        feed = feedparser.parse(rss)
        # 소스당 기사를 충분히 가져온 뒤 나중에 20개로 자릅니다.
        for entry in feed.entries[:10]: 
            all_news.append({"title": entry.title, "link": entry.link})

    # 총 20개로 제한하되, 수집된 게 20개보다 적을 상황도 대비합니다.
    target_news = all_news[:20]
    total_articles = len(target_news)
    
    # 5개씩 묶을 때 총 몇 개의 메시지가 생성될지 미리 계산
    chunk_size = 5
    # total_chunks 계산: (전체 개수 + 4) // 5 방식 (올림 처리)
    total_chunks = (total_articles + chunk_size - 1) // chunk_size

    for i in range(0, total_articles, chunk_size):
        chunk = target_news[i:i+chunk_size]
        current_chunk_num = (i // chunk_size) + 1
        
        # 상단 표기: [현재 번호 / 전체 번호]
        message = f"<b>🚀 실시간 주요 뉴스 ({current_chunk_num}/{total_chunks})</b>\n\n"
        
        for idx, item in enumerate(chunk):
            title = item['title']
            summary = get_summary(item['link'])
            
            # 영문 뉴스 자동 감지 및 번역 (기존 로직 유지)
            if re.search('[a-zA-Z]{5,}', title): # 알파벳 5자 이상 연속 시 영어로 간주
                title = f"[번역] " + translate_text(title)
                summary = translate_text(summary)

            message += f"<b>{idx+1}. {title}</b>\n"
            message += f"📝 {summary}\n"
            message += f"🔗 <a href='{item['link']}'>기사 보기</a>\n\n"
            message += "--------------------------\n\n"
        
        send_to_telegram(message)

def send_to_telegram(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML", "disable_web_page_preview": True}
    requests.post(url, data=payload)

if __name__ == "__main__":
    collect_and_send()
