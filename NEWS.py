import os
import requests
from bs4 import BeautifulSoup
import re
from googletrans import Translator
import feedparser

# 환경 변수
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

# 국내 3사 RSS 및 CNN 웹 주소
RSS_LIST = [
    "https://www.hani.co.kr/rss/",    # 한겨레 경제
    "https://www.hankyung.com/feed/economy",   # 한국경제
    "https://www.mk.co.kr/rss/30000001/"       # 매일경제
]

translator = Translator()

def translate_text(text):
    try:
        if not text or text.strip() == "": return text
        result = translator.translate(text, dest='ko')
        return result.text
    except:
        return text

def get_summary(url):
    """국내 신문사 본문 요약 로직"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
        r = requests.get(url, timeout=8, headers=headers)
        r.encoding = 'utf-8'
        soup = BeautifulSoup(r.text, "html.parser")
        for s in soup(['script', 'style', 'header', 'footer', 'nav', 'aside']):
            s.decompose()
        text = soup.get_text(" ", strip=True)
        sentences = re.split(r'(?<=[.!?])\s+', text)
        valid_sentences = [s for s in sentences if 40 < len(s) < 200]
        return " ".join(valid_sentences[:2]) if valid_sentences else "본문 요약을 가져올 수 없습니다."
    except:
        return "요약을 불러오는 중 오류가 발생했습니다."

def get_realtime_cnn():
    """CNN Business 페이지를 직접 크롤링하여 실시간 뉴스를 가져옵니다."""
    news_data = []
    try:
        url = "https://edition.cnn.com/business"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        
        # CNN의 최신 뉴스 카드/링크 패턴 추출
        cards = soup.select('a[href*="/2026/"]') # 2026년 기사만 필터링 (강력한 실시간 필터)
        
        # 만약 2026년 기사가 아직 적다면 일반 비즈니스 링크 추출
        if not cards:
            cards = soup.select('.container__headline, .container_lead-plus-headlines__headline')

        for card in cards:
            link = card.get('href', '')
            if not link.startswith('http'):
                link = "https://edition.cnn.com" + link
            
            title = card.get_text(strip=True)
            if title and len(title) > 20 and link not in [n['link'] for n in news_data]:
                news_data.append({"title": title, "link": link, "summary": "CNN 실시간 톱 헤드라인 뉴스입니다."})
            
            if len(news_data) >= 5: break
    except Exception as e:
        print(f"CNN 크롤링 에러: {e}")
    return news_data

def collect_and_send():
    # 1~3번 국내 뉴스 처리
    for i, rss_url in enumerate(RSS_LIST):
        feed = feedparser.parse(rss_url)
        source_name = ["한겨레", "한국경제", "매일경제"][i]
        message = f"<b>🚀 실시간 주요 뉴스 ({i+1}/4) - {source_name}</b>\n\n"
        
        for idx, entry in enumerate(feed.entries[:5]):
            summary = get_summary(entry.link)
            message += f"<b>{idx+1}. {entry.title}</b>\n📝 {summary}\n🔗 <a href='{entry.link}'>기사 보기</a>\n\n--------------------------\n\n"
        send_to_telegram(message)

    # 4번 CNN 실시간 크롤링 뉴스 처리
    cnn_news = get_realtime_cnn()
    message = f"<b>🚀 실시간 주요 뉴스 (4/4) - CNN(해외)</b>\n\n"
    
    if not cnn_news:
        message += "⚠️ 현재 실시간 CNN 뉴스를 가져올 수 없습니다."
    else:
        for idx, item in enumerate(cnn_news):
            title = f"[번역] " + translate_text(item['title'])
            summary = translate_text(item['summary'])
            message += f"<b>{idx+1}. {title}</b>\n📝 {summary}\n🔗 <a href='{item['link']}'>기사 보기</a>\n\n--------------------------\n\n"
    
    send_to_telegram(message)

def send_to_telegram(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML", "disable_web_page_preview": True}
    requests.post(url, data=payload)

if __name__ == "__main__":
    collect_and_send()
