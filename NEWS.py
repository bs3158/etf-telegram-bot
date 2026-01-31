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
        for entry in feed.entries[:7]:
            all_news.append({"title": entry.title, "link": entry.link})

    target_news = all_news[:20]
    
    chunk_size = 5
    for i in range(0, len(target_news), chunk_size):
        chunk = target_news[i:i+chunk_size]
        message = f"<b>🚀 실시간 주요 뉴스 ({i//chunk_size + 1}/4)</b>\n\n"
        
        # 마지막 5개 기사(마지막 묶음)인 경우 번역 수행
        is_last_chunk = (i >= 15)

        for idx, item in enumerate(chunk):
            title = item['title']
            summary = get_summary(item['link'])
            
            # 마지막 묶음이거나 제목에 영어가 포함된 경우 번역
            if is_last_chunk or re.search('[a-zA-Z]', title):
                title = f"[번역] " + translate_text(title)
                summary = translate_text(summary)

            message += f"<b>{idx+1}. {title}</b>\n"
            message += f"📝 {summary}\n"
            message += f"🔗 <a href='{item['link']}'>기사 보기</a>\n\n"
            message += "--------------------------\n\n"
        
        # 텔레그램 전송 함수 호출 (기존과 동일)
        send_to_telegram(message)

def send_to_telegram(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML", "disable_web_page_preview": True}
    requests.post(url, data=payload)

if __name__ == "__main__":
    collect_and_send()
