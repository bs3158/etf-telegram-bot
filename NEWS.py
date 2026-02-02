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
    "http://rss.cnn.com/rss/edition_business.rss" # CNN 최신 비즈니스 RSS
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
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        r = requests.get(url, timeout=8, headers=headers)
        r.encoding = 'utf-8'
        soup = BeautifulSoup(r.text, "html.parser")

        for s in soup(['script', 'style', 'header', 'footer', 'nav', 'aside']):
            s.decompose()

        text = soup.get_text(" ", strip=True)
        sentences = re.split(r'(?<=[.!?])\s+', text)
        valid_sentences = [s for s in sentences if 40 < len(s) < 200]
        summary = " ".join(valid_sentences[:2])
        return summary if summary else "본문 요약을 가져올 수 없습니다."
    except:
        return "요약을 불러오는 중 오류가 발생했습니다."

def collect_and_send():
    all_chunks = []

    for rss_url in RSS_LIST:
        feed = feedparser.parse(rss_url)
        source_news = []
        for entry in feed.entries[:5]:
            # --- CNN 구형 링크(money.cnn.com)를 신형 링크로 강제 변환 ---
            link = entry.link
            if "money.cnn.com" in link:
                # money.cnn.com/2017/... 형식을 edition.cnn.com/business/... 형식으로 추정 변환
                # 하지만 가장 확실한 방법은 RSS에서 주는 원본 링크를 그대로 신뢰하되 도메인만 교체 시도
                link = link.replace("money.cnn.com", "edition.cnn.com/business")
            
            rss_summary = getattr(entry, 'summary', '') or getattr(entry, 'description', '')
            source_news.append({
                "title": entry.title,
                "link": link,
                "rss_summary": rss_summary
            })
        all_chunks.append(source_news)

    for i, chunk in enumerate(all_chunks):
        current_num = i + 1
        source_name = ["한겨레", "한국경제", "매일경제", "CNN(해외)"][i]

        message = f"<b>🚀 실시간 주요 뉴스 ({current_num}/4) - {source_name}</b>\n\n"

        for idx, item in enumerate(chunk):
            title = item['title']
            
            # CNN은 RSS 요약 사용, 국내 매체는 본문 크롤링 요약 사용
            if current_num == 4:
                summary = re.sub('<[^<]+?>', '', item['rss_summary']).strip()
                if not summary: summary = "최신 세부정보는 기사 링크를 참조하세요."
            else:
                summary = get_summary(item['link'])

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
    requests.post(url, data=payload)

if __name__ == "__main__":
    collect_and_send()
