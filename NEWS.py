import os
import feedparser
import requests
from bs4 import BeautifulSoup
import re
from googletrans import Translator

# 환경 변수
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

# 4개의 사이트 설정
RSS_LIST = [
    "https://www.hani.co.kr/rss/",    # 한겨레 경제
    "https://www.hankyung.com/feed/economy",   # 한국경제
    "https://www.mk.co.kr/rss/30000001/",      # 매일경제
    "http://rss.cnn.com/rss/edition_business.rss" # 최신 CNN Business RSS
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
    try:
        # CNN 및 국내 언론사 차단 방지를 위한 브라우저 헤더 강화
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
        }
        r = requests.get(url, timeout=10, headers=headers)
        r.encoding = 'utf-8'
        
        if r.status_code != 200:
            return "본문 요약을 가져올 수 없습니다. (접근 권한 제한)"

        soup = BeautifulSoup(r.text, "html.parser")

        # 불필요한 태그 제거
        for s in soup(['script', 'style', 'header', 'footer', 'nav', 'aside', 'form']):
            s.decompose()

        # CNN 전용 본문 추출 시도 (클래스명이 다를 수 있어 일반 텍스트 추출 병행)
        content = soup.find('div', {'class': 'article__content'}) or soup.find('section', {'class': 'layout__wrapper'})
        if content:
            text = content.get_text(" ", strip=True)
        else:
            text = soup.get_text(" ", strip=True)

        sentences = re.split(r'(?<=[.!?])\s+', text)
        # 본문 핵심 문장 필터링 (너무 짧거나 길지 않은 문장)
        valid_sentences = [s for s in sentences if 50 < len(s) < 250]
        
        summary = " ".join(valid_sentences[:2])
        return summary if summary else "본문 내용을 분석할 수 없습니다."
    except:
        return "요약을 불러오는 중 오류가 발생했습니다."

def collect_and_send():
    all_chunks = []

    for rss_url in RSS_LIST:
        feed = feedparser.parse(rss_url)
        source_news = []
        # 각 사이트에서 상위 5개 추출
        for entry in feed.entries[:5]:
            source_news.append({
                "title": entry.title,
                "link": entry.link
            })
        all_chunks.append(source_news)

    for i, chunk in enumerate(all_chunks):
        current_num = i + 1
        source_name = ["한겨레", "한국경제", "매일경제", "CNN(해외)"][i]

        message = f"<b>🚀 실시간 주요 뉴스 ({current_num}/4) - {source_name}</b>\n\n"

        for idx, item in enumerate(chunk):
            title = item['title']
            summary = get_summary(item['link'])

            # 4번째 소스(CNN)이거나 제목에 영어가 많으면 번역
            if current_num == 4 or re.search('[a-zA-Z]{7,}', title):
                title = f"[번역] " + translate_text(title)
                summary = translate_text(summary)

            message += f"<b>{idx+1}. {title}</b>\n"
            message += f"📝 {summary}\n"
            message += f"🔗 <a href='{item['link']}'>기사 보기</a>\n\n"
            message += "--------------------------\n\n"

        send_to_telegram(message)

def send_to_telegram(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    try:
        requests.post(url, data=payload, timeout=10)
    except:
        pass

if __name__ == "__main__":
    collect_and_send()
