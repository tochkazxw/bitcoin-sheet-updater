import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests
import datetime
import pytz
from googleapiclient.discovery import build
from google.oauth2 import service_account
import os

# Авторизация gspread
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)
sheet = client.open_by_key("1SjT740pFA7zuZMgBYf5aT0IQCC-cv6pMsQpEXYgQSmU").sheet1
sheet_id = sheet._properties['sheetId']

# Авторизация Google Sheets API для форматирования
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
credentials = service_account.Credentials.from_service_account_file("credentials.json", scopes=SCOPES)
service = build("sheets", "v4", credentials=credentials)

# Telegram уведомление
def send_telegram_message(text):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        print("⚠️ Не заданы TELEGRAM_BOT_TOKEN или TELEGRAM_CHAT_ID в переменных окружения.")
        return
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }
    try:
        resp = requests.post(url, data=payload, timeout=10)
        if resp.status_code == 200:
            print("✅ Уведомление в Telegram отправлено.")
        else:
            print(f"❌ Ошибка отправки уведомления в Telegram: {resp.text}")
    except Exception as e:
        print(f"❌ Исключение при отправке Telegram уведомления: {e}")

# Время Молдовы
def get_today_moldova():
    tz = pytz.timezone('Europe/Chisinau')
    now = datetime.datetime.now(tz)
    return now.strftime("%d.%m.%Y")

# API: курс, сложность, хешрейт
def get_coindesk_price():
    try:
        r = requests.get("https://api.coindesk.com/v1/bpi/currentprice.json", timeout=10)
        return float(r.json()["bpi"]["USD"]["rate_float"])
    except:
        return None

def get_coingecko_price():
    try:
        r = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd", timeout=10)
        return float(r.json()["bitcoin"]["usd"])
    except:
        return None

def get_difficulty_and_hashrate():
    try:
        diff = float(requests.get("https://blockchain.info/q/getdifficulty", timeout=10).text)
        hashrate = float(requests.get("https://blockchain.info/q/hashrate", timeout=10).text)
        return f"{diff:.2E}", str(int(hashrate))
    except:
        return "N/A", "N/A"

# ====== ДАННЫЕ ======
today = get_today_moldova()
prices = [p for p in [get_coindesk_price(), get_coingecko_price()] if p is not None]
btc_avg = round(sum(prices) / len(prices), 2) if prices else "N/A"
difficulty, hashrate = get_difficulty_and_hashrate()

# Тестовые данные
miners = 1000
stock_hashrate = 150_000
attracted_hashrate = 172_500
distribution = "2.80%"
share = round((attracted_hashrate / int(hashrate)) * 100, 2) if hashrate != "N/A" else "N/A"
avg_hashrate_per_miner = round(attracted_hashrate / miners, 2)
growth = attracted_hashrate - stock_hashrate
partner = "PartnerX"
hashrate_to_distribution = f"{attracted_hashrate / 2.80:.2f}"

# ===== ЗАГОЛОВКИ И ДАННЫЕ =====
labels = [
    "Дата",
    "Количество майнеров",
    "Средний курс BTC (USD)",
    "Стоковый хешрейт, Th",
    "Сложность",
    "Привлеченный Хешрейт, Th",
    "Общий хешрейт сети, Th",
    "Распределение",
    "Доля привлеченного хешрейта, %",
    "Средний хешрейт на майнер",
    "Прирост хешрейта",
    "Партнер",
    "Хешрейт к распределению"
]

data = [
    today,
    miners,
    btc_avg,
    stock_hashrate,
    difficulty,
    attracted_hashrate,
    hashrate,
    distribution,
    share,
    avg_hashrate_per_miner,
    growth,
    partner,
    hashrate_to_distribution
]

# ===== ДОБАВЛЯЕМ В ТАБЛИЦУ =====
sheet.append_rows([[], labels, data])

row_count = len(sheet.get_all_values())
header_row_index = row_count - 2
data_row_index = row_count - 1

# ===== ФОРМАТИРОВАНИЕ =====
requests_body = {
    "requests": [
        {
            "repeatCell": {
                "range": {
                    "sheetId": sheet_id,
                    "startRowIndex": header_row_index,
                    "endRowIndex": header_row_index + 1,
                    "startColumnIndex": 0,
                    "endColumnIndex": len(labels)
                },
                "cell": {
                    "userEnteredFormat": {
                        "backgroundColor": {"red": 0.2, "green": 0.4, "blue": 0.8},
                        "textFormat": {"foregroundColor": {"red": 0, "green": 0, "blue": 0}, "bold": True}
                    }
                },
                "fields": "userEnteredFormat(backgroundColor,textFormat)"
            }
        },
        {
            "repeatCell": {
                "range": {
                    "sheetId": sheet_id,
                    "startRowIndex": data_row_index,
                    "endRowIndex": data_row_index + 1,
                    "startColumnIndex": 0,
                    "endColumnIndex": len(data)
                },
                "cell": {
                    "userEnteredFormat": {
                        "backgroundColor": {"red": 0.85, "green": 1.0, "blue": 0.85},
                        "textFormat": {"foregroundColor": {"red": 0, "green": 0, "blue": 0}}
                    }
                },
                "fields": "userEnteredFormat(backgroundColor,textFormat)"
            }
        },
        {
            "updateBorders": {
                "range": {
                    "sheetId": sheet_id,
                    "startRowIndex": header_row_index,
                    "endRowIndex": data_row_index + 1,
                    "startColumnIndex": 0,
                    "endColumnIndex": len(data)
                },
                "top": {"style": "SOLID", "width": 1, "color": {"red": 0, "green": 0, "blue": 0}},
                "bottom": {"style": "SOLID", "width": 1, "color": {"red": 0, "green": 0, "blue": 0}},
                "left": {"style": "SOLID", "width": 1, "color": {"red": 0, "green": 0, "blue": 0}},
                "right": {"style": "SOLID", "width": 1, "color": {"red": 0, "green": 0, "blue": 0}},
                "innerHorizontal": {"style": "SOLID", "width": 1, "color": {"red": 0, "green": 0, "blue": 0}},
                "innerVertical": {"style": "SOLID", "width": 1, "color": {"red": 0, "green": 0, "blue": 0}}
            }
        }
    ]
}

service.spreadsheets().batchUpdate(
    spreadsheetId="1SjT740pFA7zuZMgBYf5aT0IQCC-cv6pMsQpEXYgQSmU",
    body=requests_body
).execute()

print(f"✅ Данные за {today} добавлены и оформлены.")

# Telegram уведомление
send_telegram_message(
    f"✅ Таблица обновлена: {today}\n"
    f"Средний курс BTC (USD): {btc_avg}\n"
    f"Сложность: {difficulty}\n"
    f"Хешрейт: {hashrate}\n"
    f"Ссылка: https://docs.google.com/spreadsheets/d/1SjT740pFA7zuZMgBYf5aT0IQCC-cv6pMsQpEXYgQSmU/edit"
)
