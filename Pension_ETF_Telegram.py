import os
import json
import requests
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

# =========================
# 기본 설정
# =========================
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

SNAPSHOT_FILE = f"{DATA_DIR}/pension_snapshot.json"
GRAPH_FILE = f"{DATA_DIR}/pension_graph.png"

ETF_LIST = {
    "TIGER미국S&P500": 35000000,
    "KODEX미국나스닥100": 28000000,
    "KODEX미국배당성장": 19000000,
}

# =========================
# 한글 폰트 설정 (GitHub Actions)
# =========================
FONT_PATH = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"

if os.path.exists(FONT_PATH):
    font_prop = fm.FontProperties(fname=FONT_PATH)
    plt.rcParams["font.family"] = font_prop.get_name()
else:
    print("⚠️ NotoSansCJK 폰트 없음")

plt.rcParams["axes.unicode_minus"] = False

# =========================
# 텔레그램 전송
# =========================
def send_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": text})

def send_photo(photo_path, caption=""):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    with open(photo_path, "rb") as f:
        requests.post(
            url,
            data={"chat_id": CHAT_ID, "caption": caption},
            files={"photo": f},
        )

# =========================
# 스냅샷 로드/저장
# =========================
def load_snapshot():
    if not os.path.exists(SNAPSHOT_FILE):
        return []
    with open(SNAPSHOT_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_snapshot(data):
    with open(SNAPSHOT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# =========================
# 메인 로직
# =========================
def run():
    today = datetime.now().strftime("%Y-%m-%d")

    total_value = sum(ETF_LIST.values())

    snapshots = load_snapshot()
    snapshots.append({
        "date": today,
        "value": total_value
    })
    save_snapshot(snapshots)

    # ===== 그래프 =====
    dates = [s["date"] for s in snapshots]
    values = [s["value"] / 1_000_000 for s in snapshots]

    plt.figure(figsize=(8, 4))
    plt.plot(dates, values, marker="o")
    plt.title("개인연금 평가금액 추이 (백만원)")
    plt.xticks(rotation=45)
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(GRAPH_FILE)
    plt.close()

    # ===== 텔레그램 =====
    msg = (
        "📌 개인연금 ETF 현황\n\n"
        f"총 평가금액: {total_value:,.0f} 원"
    )
    send_message(msg)
    send_photo(GRAPH_FILE, "📈 개인연금 평가금액 추이")

if __name__ == "__main__":
    run()
