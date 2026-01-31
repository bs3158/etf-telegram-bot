import requests
import feedparser
from bs4 import BeautifulSoup
from transformers import pipeline
import textwrap
import re   # ⭐⭐⭐ 이 줄 추가


#########################################
# 텔레그램 설정
#########################################

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]


#########################################
# RSS (한국 + 미국 경제 뉴스)
#########################################

RSS_URLS = [
    "https://www.hankyung.com/feed/economy",
    "https://rss.nytimes.com/services/xml/rss/nyt/Economy.xml",
    "https://feeds.reuters.com/reuters/businessNews"
]


#########################################
# AI 요약 모델 (무료 로컬)
#########################################

summarizer = pipeline(
    "summarization",
    model="sshleifer/distilbart-cnn-6-6"   # ⭐ 빠른 경량 모델 (추천)
)


#########################################
# 텍스트 정리 (한글 깨짐 방지 ⭐)
#########################################

def clean_text(text):
    text = BeautifulSoup(text, "html.parser").get_text()
    text = text.replace("\n", " ")
    text = " ".join(text.split())
    return text


#########################################
# 기사 본문 수집
#########################################

def get_article_text(url):
    try:
        r = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(r.text, "html.parser")

        paragraphs = soup.find_all("p")
        text = " ".join(p.get_text() for p in paragraphs)

        return clean_text(text)

    except:
        return ""


#########################################
# 요약 함수 (경고 제거 + 자동 길이 ⭐⭐⭐)
#########################################

def summarize(text):

    text = clean_text(text)

    # 한글 → 앞부분만 (요약 안함)
    if re.search('[가-힣]', text):
        return textwrap.shorten(text, width=180)

    # 영어 → AI 요약
    text = text[:1000]

    words = len(text.split())

    # ⭐ 입력 길이에 맞춰 자동 조절
    max_len = int(words * 0.6)
    min_len = int(words * 0.3)

    max_len = max(20, min(max_len, 80))
    min_len = max(10, min(min_len, 40))

    result = summarizer(
        text,
        max_length=max_len,
        min_length=min_len,
        do_sample=False,
        truncation=True
    )

    return result[0]["summary_text"]






#########################################
# 뉴스 수집 (넉넉히 30개 → 실패 대비)
#########################################

def collect_news():

    results = []

    for url in RSS_URLS:
        feed = feedparser.parse(url)

        for entry in feed.entries[:25]:   # ⭐ 25개 수집

            article = get_article_text(entry.link)

            if len(article) < 100:
                continue

            summary = summarize(article)

            results.append({
                "title": clean_text(entry.title),
                "summary": summary,
                "link": entry.link
            })

    return results[:20]   # ⭐ 최종 20개


#########################################
# 메시지 생성
#########################################

def build_message(news, part_no):

    msg = f"📰 오늘의 경제 뉴스 요약 ({part_no}/2)\n\n"

    for i, n in enumerate(news, 1):
        msg += (
            f"{i}. {n['title']}\n"
            f"{n['summary']}\n"
            f"{n['link']}\n\n"
        )

    return msg


#########################################
# 텔레그램 전송
#########################################

def send_telegram(text):

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    requests.post(url, data={
        "chat_id": CHAT_ID,
        "text": text
    })


#########################################
# 메인 실행
#########################################

def main():

    news = collect_news()

    if not news:
        send_telegram("뉴스 수집 실패")
        return

    # ⭐ 10개씩 분할
    first = news[:10]
    second = news[10:20]

    send_telegram(build_message(first, 1))
    send_telegram(build_message(second, 2))


if __name__ == "__main__":
    main()
