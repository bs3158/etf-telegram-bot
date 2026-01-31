import os
import feedparser
import requests
from bs4 import BeautifulSoup
import re

# 환경 변수
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

RSS_LIST = [
    "https://www.hankyung.com/feed/economy",
    "https://www.mk.co.kr/rss/30000001/",
    "https://www.cnbc.com/id/10001147/device/rss/rss.html"
]

def send_telegram(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML", # 가독성을 위해 HTML 모드 사용
        "disable_web_page_preview": True
    }
    requests.post(url, data=payload)

def get_summary(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(url, timeout=5, headers=headers)
        soup = BeautifulSoup(r.text, "html.parser")
        
        # 불필요한 태그 제거
        for s in soup(['script', 'style', 'header', 'footer', 'nav']):
            s.decompose()

        text = soup.get_text(" ", strip=True)
        # 한글/영어 문장 단위로 분리 (간단한 요약 로직)
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        # 본문과 관련 없는 짧은 문구 제외 후 상위 2문장 추출
        valid_sentences = [s for s in sentences if len(s) > 30 and len(s) < 200]
        summary = " ".join(valid_sentences[:2])
        
        return summary if summary else "본문 요약을 가져올 수 없습니다."
    except:
        return "요약을 불러오는 중 오류가 발생했습니다."

def collect_and_send():
    all_news = []
    for rss in RSS_LIST:
        feed = feedparser.parse(rss)
        for entry in feed.entries[:7]: # 각 소스별 상위 기사
            all_news.append({
                "title": entry.title,
                "link": entry.link
            })

    # 총 20개로 제한
    target_news = all_news[:20]
    
    # 5개씩 묶어서 전송 (메시지 길이 제한 및 가독성 고려)
    chunk_size = 5
    for i in range(0, len(target_news), chunk_size):
        chunk = target_news[i:i+chunk_size]
        message = f"<b>🚀 실시간 주요 뉴스 ({i//chunk_size + 1}/4)</b>\n\n"
        
        for idx, item in enumerate(chunk):
            summary = get_summary(item['link'])
            message += f"<b>{idx+1}. {item['title']}</b>\n"
            message += f"📝 {summary}\n"
            message += f"🔗 <a href='{item['link']}'>기사 보기</a>\n\n"
            message += "--------------------------\n\n"
        
        send_telegram(message)

if __name__ == "__main__":
    collect_and_send()
