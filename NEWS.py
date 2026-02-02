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
    "https://rss.cnn.com/rss/edition_business.rss" # 최신 CNN Business (HTTPS 적용)
]

translator = Translator()

def translate_text(text):
    try:
        if not text or text.strip() == "": return text
        result = translator.translate(text, dest='ko')
        return result.text
    except:
        return text

def get_summary(url, is_foreign=False):
    """국내 매체는 본문 분석, 해외 매체(CNN)는 차단 방지를 위해 RSS 요약을 우선 사용합니다."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        r = requests.get(url, timeout=8, headers=headers)
        r.encoding = 'utf-8'
        
        # 접근 차단되었거나 해외 매체인 경우 RSS 요약을 쓸 수 있도록 예외 반환
        if r.status_code != 200 or is_foreign:
            return None

        soup = BeautifulSoup(r.text, "html.parser")
        for s in soup(['script', 'style', 'header', 'footer', 'nav', 'aside', 'form']):
            s.decompose()

        text = soup.get_text(" ", strip=True)
        sentences = re.split(r'(?<=[.!?])\s+', text)
        valid_sentences = [s for s in sentences if 40 < len(s) < 200]
        summary = " ".join(valid_sentences[:2])
        return summary if summary else None
    except:
        return None

def collect_and_send():
    for i, rss_url in enumerate(RSS_LIST):
        feed = feedparser.parse(rss_url)
        current_num = i + 1
        source_names = ["한겨레", "한국경제", "매일경제", "CNN(해외)"]
        source_name = source_names[i]

        message = f"<b>🚀 실시간 주요 뉴스 ({current_num}/4) - {source_name}</b>\n\n"

        for idx, entry in enumerate(feed.entries[:5]):
            title = entry.title
            link = entry.link
            
            # 1. 국내 매체는 본문 추출 시도, CNN(4번째)은 바로 RSS 요약 활용
            is_foreign = (current_num == 4)
            summary = get_summary(link, is_foreign)
            
            # 2. 본문 추출 실패 시 RSS 내부 요약 정보 사용
            if not summary:
                raw_rss_summary = getattr(entry, 'summary', '') or getattr(entry, 'description', '')
                summary = re.sub('<[^<]+?>', '', raw_rss_summary).strip()
            
            if not summary or len(summary) < 5:
                summary = "본문 요약 정보를 가져올 수 없습니다."

            # CNN 또는 영문 제목 번역
            if is_foreign or re.search('[a-zA-Z]{7,}', title):
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
