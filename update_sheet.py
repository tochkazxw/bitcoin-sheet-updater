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

# Функция отправки сообщения в Telegram
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

# Получить текущую дату в Молдове (дд.мм.гггг)
def get_today_moldova():
    tz = pytz.timezone('Europe/Chisinau')
    now = datetime.datetime.now(tz)
    return now.strftime("%d.%m.%Y")

# Получение курса с Coindesk
def get_coindesk_price():
    try:
        r = requests.get("https://api.coindesk.com/v1/bpi/currentprice.json", timeout=10)
        return float(r.json()["bpi"]["USD"]["rate_float"])
    except:
        return None

# Получение курса с Coingecko
def get_coingecko_price():
    try:
        r = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd", timeout=10)
        return float(r.json()["bitcoin"]["usd"])
    except:
        return None

# Получение сложности и хешрейта с blockchain.info
def get_difficulty_and_hashrate():
    try:
        diff = float(requests.get("https://blockchain.info/q/getdifficulty", timeout=10).text)
        hashrate = float(requests.get("https://blockchain.info/q/hashrate", timeout=10).text)
        return f"{diff:.2E}", str(int(hashrate))
    except:
        return "N/A", "N/A"

# Основная логика

today = get_today_moldova()
prices = [p for p in [get_coindesk_price(), get_coingecko_price()] if p is not None]
btc_avg = round(sum(prices) / len(prices), 2) if prices else "N/A"
difficulty, hashrate = get_difficulty_and_hashrate()

# Заголовок таблицы
headers = ["Параметры сети", "Курс", "Сложность", "Общий хешрейт сети, Th"]
# Данные для вставки
data_row = [today, str(btc_avg), difficulty, hashrate]

# Проверяем, есть ли уже заголовок в первой строке (чтобы не дублировать)
first_row = sheet.row_values(1)
if first_row != headers:
    sheet.insert_row(headers, index=1)
    print("📝 Заголовок добавлен.")

# Добавляем данные в конец таблицы (после последней заполненной строки)
sheet.append_row(data_row)

# Получаем общее количество строк для форматирования
row_count = len(sheet.get_all_values())
start = row_count - 1  # индекс строки с новыми данными (append_row добавляет в конец)
end = row_count        # следующий индекс

# Запрос на оформление (цвета и границы)
requests_body = {
    "requests": [
        {
            "repeatCell": {
                "range": {
                    "sheetId": sheet_id,
                    "startRowIndex": start,
                    "endRowIndex": start + 1,
                    "startColumnIndex": 0,
                    "endColumnIndex": 4
                },
                "cell": {
                    "userEnteredFormat": {
                        "backgroundColor": {"red": 0.85, "green": 1.0, "blue": 0.85}
                    }
                },
                "fields": "userEnteredFormat(backgroundColor)"
            }
        },
        {
            "updateBorders": {
                "range": {
                    "sheetId": sheet_id,
                    "startRowIndex": start,
                    "endRowIndex": start + 1,
                    "startColumnIndex": 0,
                    "endColumnIndex": 4
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

# Применяем оформление к новой строке с данными
service.spreadsheets().batchUpdate(spreadsheetId=sheet.spreadsheet.id, body=requests_body).execute()
print(f"✅ Данные за {today} добавлены и оформлены.")

# Отправляем уведомление в Telegram
send_telegram_message(f"✅ Таблица обновлена: {today}, Курс BTC: {btc_avg}, Сложность: {difficulty}, Хешрейт: {hashrate}")
