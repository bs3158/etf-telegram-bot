import requests
import random
from collections import Counter
import os

# ==============================
# 환경변수 (GitHub Secrets)
# ==============================
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

JSON_URL = "https://smok95.github.io/lotto/results/all.json"


# ==============================
# 로또 데이터 수집
# ==============================
def fetch_all_data():
    res = requests.get(JSON_URL, timeout=15)
    return res.json()


# ==============================
# 최다 등장 6개 번호 추출
# ==============================
def get_top6(draws, exclude=None):
    if exclude is None:
        exclude = set()

    # Counter
    cnt = Counter()
    for d in draws:
        for n in d["numbers"]:
            if n not in exclude:
                cnt[n] += 1

    return [n for n, _ in cnt.most_common(6)]


# ==============================
# 텔레그램 보내기
# ==============================
def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message
    }
    requests.post(url, data=payload)


# ==============================
# 메인 로직
# ==============================
def main():
    data = fetch_all_data()

    # 최신 회차 번호를 draw_no로 구함
    latest_round = max(d["draw_no"] for d in data)
    next_round = latest_round + 1



    # ——————————————
    # 1) 최근 30회
    # ——————————————
    recent_30 = data[-30:]
    recent_top6 = sorted(get_top6(recent_30))

    # ——————————————
    # 2) 전체 (최근30 제외)
    # ——————————————
    # 전체 등장 횟수 추출
    all_top6 = get_top6(data)

    # 최근 번호 제외
    overall_top6 = sorted(get_top6(data, exclude=set(recent_top6)))

    # ——————————————
    # 3) 랜덤 6개
    # ——————————————
    random6 = sorted(random.sample(range(1, 46), 6))

    # ——————————————
    # 메시지 생성
    # ——————————————
    msg = f"""
🎯 제{next_round} 회차 당첨 예상 추천 번호

🔥 최근 30회 HOT
{' '.join(map(str, recent_top6))}

📈 전체 장기 강세 (HOT 제외)
{' '.join(map(str, overall_top6))}

🎲 랜덤
{' '.join(map(str, random6))}

※ 과거 데이터 기반 참고용 번호입니다
"""

    send_telegram(msg)


# ==============================
if __name__ == "__main__":
    main()
