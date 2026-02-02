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
    "http://rss.cnn.com/rss/edition_business.rss" # CNN Business (영어) 로 변경
]

translator = Translator()

def translate_text(text):
    try:
        result = translator.translate(text, dest='ko')
        return result.text
    except:
        return text

def get_summary(url):
    try:
        # 한겨레 등 언론사 차단 방지를 위한 브라우저 헤더
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        r = requests.get(url, timeout=8, headers=headers)
        r.encoding = 'utf-8'
        soup = BeautifulSoup(r.text, "html.parser")

        for s in soup(['script', 'style', 'header', 'footer', 'nav', 'aside']):
            s.decompose()

        text = soup.get_text(" ", strip=True)
        sentences = re.split(r'(?<=[.!?])\s+', text)
        # 본문 핵심 문장 필터링
        valid_sentences = [s for s in sentences if len(s) > 40 and len(s) < 200]
        summary = " ".join(valid_sentences[:2])
        return summary if summary else "본문 요약을 가져올 수 없습니다."
    except:
        return "요약을 불러오는 중 오류가 발생했습니다."

def collect_and_send():
    all_chunks = []

    for rss_url in RSS_LIST:
        feed = feedparser.parse(rss_url)
        # 각 사이트(소스)에서 정확히 상위 5개만 추출
        source_news = []
        for entry in feed.entries[:5]:
            source_news.append({
                "title": entry.title,
                "link": entry.link
            })
        all_chunks.append(source_news)

    # 4개의 사이트 결과물을 각각 메시지 한 통(5개 기사)씩 보냄
    for i, chunk in enumerate(all_chunks):
        current_num = i + 1
        source_name = ["한겨레", "한국경제", "매일경제", "CNN(해외)"][i] # 명칭 변경

        message = f"<b>🚀 실시간 주요 뉴스 ({current_num}/4) - {source_name}</b>\n\n"

        for idx, item in enumerate(chunk):
            title = item['title']
            summary = get_summary(item['link'])

            # 4번째 소스(CNN)이거나 제목에 영어가 많으면 번역
            if current_num == 4 or re.search('[a-zA-Z]{5,}', title):
                title = f"[번역] " + translate_text(title)
                summary = translate_text(summary)

            message += f"<b>{idx+1}. {title}</b>\n"
            message += f"📝 {summary}\n"
            message += f"🔗 <a href='{item['link']}'>기사 보기</a>\n\n"
            message += "--------------------------\n\n"

        # 각 사이트별로 메시지 전송
        send_to_telegram(message)

def send_to_telegram(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    requests.post(url, data=payload)

if __name__ == "__main__":
    collect_and_send()
