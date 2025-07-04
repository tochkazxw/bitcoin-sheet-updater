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

# Входные данные вручную (пример)
miners_count = 1000
stock_hashrate = 150000
attracted_hashrate = 172500
distribution = "2.80%"
average_hashrate_per_miner = 150
hashrate_growth = 22500
partner = "1%"
developer = "1.8%"
growth_coefficient = "15%"
total_hashrate = 172500
income_30d_btc = "Тут будут данные"
useful_hashrate_th = 167670
income_30d_usdt = "Тут будут данные"

# Получаем данные с интернета
today = get_today_moldova()
prices = [p for p in [get_coindesk_price(), get_coingecko_price()] if p is not None]
btc_avg = round(sum(prices) / len(prices), 2) if prices else "N/A"
difficulty, hashrate_network = get_difficulty_and_hashrate()

# Составляем строки для добавления
rows = [
    ["Дата", "Средний курс BTC", "Сложность", "Общий хешрейт", "", "", "", ""],
    [miners_count, stock_hashrate, attracted_hashrate, distribution, "", "", "", ""],
    ["Средний хешрейт на майнер", "Прирост хешрейта", "", "Партнер", "Разработчик", "", "", ""],
    [average_hashrate_per_miner, hashrate_growth, "", partner, developer, "", "", ""],
    ["Коэффициент прироста", "Суммарный хешрейт", "", "Доход за 30 дней, BTC", "", "", "", ""],
    [growth_coefficient, total_hashrate, "", income_30d_btc, "", "", "", ""],
    ["Полезный хешрейт, Th", useful_hashrate_th, "", "Доход за 30 дней, USDT", income_30d_usdt, "", "", ""],
    [today, btc_avg, difficulty, hashrate_network, "", "", "", ""],
]

# Добавляем пустую строку для отступа
sheet.append_row([])

# Добавляем все строки подряд
for row in rows:
    sheet.append_row(row)

# Получаем количество строк после добавления
row_count = len(sheet.get_all_values())
header_row_index = row_count - len(rows)

# Пример форматирования заголовков и ключевых данных
requests_body = {
    "requests": [
        # Форматирование первой строки заголовков
        {
            "repeatCell": {
                "range": {
                    "sheetId": sheet_id,
                    "startRowIndex": header_row_index,
                    "endRowIndex": header_row_index + 1,
                    "startColumnIndex": 0,
                    "endColumnIndex": 4,
                },
                "cell": {
                    "userEnteredFormat": {
                        "backgroundColor": {"red": 0.2, "green": 0.4, "blue": 0.8},
                        "textFormat": {"foregroundColor": {"red": 1, "green": 1, "blue": 1}, "bold": True},
                        "horizontalAlignment": "CENTER"
                    }
                },
                "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"
            }
        },
        # Форматирование последней строки (с датой и ключевыми цифрами)
        {
            "repeatCell": {
                "range": {
                    "sheetId": sheet_id,
                    "startRowIndex": row_count - 1,
                    "endRowIndex": row_count,
                    "startColumnIndex": 0,
                    "endColumnIndex": 4,
                },
                "cell": {
                    "userEnteredFormat": {
                        "backgroundColor": {"red": 0.85, "green": 1.0, "blue": 0.85},
                        "textFormat": {"foregroundColor": {"red": 0, "green": 0, "blue": 0}},
                        "horizontalAlignment": "CENTER"
                    }
                },
                "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"
            }
        },
    ]
}

service.spreadsheets().batchUpdate(
    spreadsheetId="1SjT740pFA7zuZMgBYf5aT0IQCC-cv6pMsQpEXYgQSmU",
    body=requests_body
).execute()

print(f"✅ Данные за {today} добавлены и оформлены.")
