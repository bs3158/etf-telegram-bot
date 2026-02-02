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
        # HTML 태그 제거 후 번역
        clean_text = re.sub('<[^<]+?>', '', text)
        result = translator.translate(clean_text, dest='ko')
        return result.text
    except:
        return text

def collect_and_send():
    for i, rss_url in enumerate(RSS_LIST):
        feed = feedparser.parse(rss_url)
        current_num = i + 1
        source_names = ["한겨레", "한국경제", "매일경제", "CNN(해외)"]
        source_name = source_names[i]

        message = f"<b>🚀 실시간 주요 뉴스 ({current_num}/4) - {source_name}</b>\n\n"

        # 각 사이트에서 상위 5개 추출
        for idx, entry in enumerate(feed.entries[:5]):
            title = entry.title
            link = entry.link
            
            # 본문에 접속하는 대신 RSS 피드에 포함된 요약(description/summary) 사용
            # CNN은 RSS 피드 안에 이미 짧은 요약문을 제공합니다.
            raw_summary = getattr(entry, 'summary', '') or getattr(entry, 'description', '')
            
            # 불필요한 HTML 태그 및 공백 제거
            summary = re.sub('<[^<]+?>', '', raw_summary).strip()
            if not summary or len(summary) < 10:
                summary = "요약 정보가 제공되지 않는 기사입니다."

            # 4번째 소스(CNN)이거나 제목에 영어가 많으면 번역
            if current_num == 4 or re.search('[a-zA-Z]{7,}', title):
                title = f"[번역] " + translate_text(title)
                summary = translate_text(summary)

            message += f"<b>{idx+1}. {title}</b>\n"
            message += f"📝 {summary}\n"
            message += f"🔗 <a href='{link}'>기사 보기</a>\n\n"
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
