import os
import feedparser
import requests
from bs4 import BeautifulSoup
import re

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

# =========================
# RSS
# =========================
RSS_LIST = [
    "https://www.hankyung.com/feed/economy",
    "https://www.mk.co.kr/rss/30000001/",
    "https://feeds.reuters.com/reuters/businessNews",
    "https://www.cnbc.com/id/10001147/device/rss/rss.html"
]

# =========================
# 텔레그램
# =========================
def send_telegram(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    MAX = 4000   # 안전 마진

    for i in range(0, len(text), MAX):
        part = text[i:i+MAX]

        res = requests.post(url, data={
            "chat_id": CHAT_ID,
            "text": part,
            "disable_web_page_preview": True
        })

        print("Telegram:", res.status_code)

# =========================
# 기사 본문 추출
# =========================
def get_article(url):
    try:
        r = requests.get(url, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")

        text = soup.get_text(" ", strip=True)

        # 문장 분리 후 앞 3문장만 (요약 효과)
        sentences = re.split(r'[.!?。]', text)

        summary = ". ".join(sentences[:3])

        return summary[:400]

    except:
        return ""


# =========================
# 뉴스 수집
# =========================
def collect_news(limit=20):
    news = []

    for rss in RSS_LIST:
        feed = feedparser.parse(rss)

        for entry in feed.entries[:limit]:
            title = entry.title
            link = entry.link

            body = get_article(link)

            news.append(f"• {title}\n{body}\n{link}")

    return news[:limit]


# =========================
# 메세지 분할 전송
# =========================
def send_news(news):

    chunk = 10

    for i in range(0, len(news), chunk):
        part = news[i:i+chunk]

        msg = f"📰 오늘의 경제 뉴스 요약 ({i//chunk+1}/{(len(news)-1)//chunk+1})\n\n"
        msg += "\n\n".join(part)

        send_telegram(msg)


# =========================
# MAIN
# =========================
def main():
    news = collect_news(20)
    send_news(news)


if __name__ == "__main__":
    main()
