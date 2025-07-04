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

# Авторизация Google Sheets API для форматирования и формул
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
credentials = service_account.Credentials.from_service_account_file("credentials.json", scopes=SCOPES)
service = build("sheets", "v4", credentials=credentials)
spreadsheet_id = "1SjT740pFA7zuZMgBYf5aT0IQCC-cv6pMsQpEXYgQSmU"

# Получить текущую дату в Молдове (дд.мм.гггг)
def get_today_moldova():
    tz = pytz.timezone('Europe/Chisinau')
    now = datetime.datetime.now(tz)
    return now.strftime("%d.%m.%Y")

# Получение курсов с Coindesk и Coingecko
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

# Получение сложности и хешрейта с blockchain.info
def get_difficulty_and_hashrate():
    try:
        diff = float(requests.get("https://blockchain.info/q/getdifficulty", timeout=10).text)
        hashrate = float(requests.get("https://blockchain.info/q/hashrate", timeout=10).text)
        return f"{diff:.2E}", int(hashrate)
    except:
        return "N/A", "N/A"

# Основные данные
today = get_today_moldova()
prices = [p for p in [get_coindesk_price(), get_coingecko_price()] if p is not None]
btc_avg = round(sum(prices) / len(prices), 2) if prices else "N/A"
difficulty, hashrate = get_difficulty_and_hashrate()

# Статичные данные
miners = 1000
stock_hashrate = 150000
attracted_hashrate = 172500
distribution = "2.80%"
hashrate_distribution_ratio = 4830
avg_hashrate_per_miner = 150
hashrate_growth = 22500
partner_share = "1%"
developer_share = "1.8%"
partner_hashrate = 1725
developer_hashrate = 3105
growth_coefficient = "15%"
total_hashrate = 172500
useful_hashrate = 167670
share_attracted_hashrate = "0.04"

# Чистим лист перед вставкой
sheet.clear()

# Вставляем данные без формул
rows = [
    ["Дата", "Средний курс BTC", "Сложность", "Общий хешрейт", "Доля привлеченного хешрейта, %"],
    [today, btc_avg, difficulty, total_hashrate, share_attracted_hashrate],
    ["Кол-во майнеров", "Стоковый хешрейт", "Привлечённый хешрейт", "Распределение", "Хешрейт к распределению"],
    [miners, stock_hashrate, attracted_hashrate, distribution, hashrate_distribution_ratio],
    ["Средний хеш на майнер", "Прирост хешрейта", "-", "Партнер", "Разработчик"],
    [avg_hashrate_per_miner, hashrate_growth, "-", partner_share, developer_share],
    ["Коэфф. прироста", "Суммарный хешрейт", "-", partner_hashrate, developer_hashrate],
    [growth_coefficient, total_hashrate, "Доход за 30 дней, BTC", "-", "-"],
    ["Полезный хешрейт, Th", useful_hashrate, "Доход за 30 дней, USDT", "-", "-"]
]

for row in rows:
    sheet.append_row(row)

# Вставляем формулы через Google Sheets API в нужные ячейки
# Адреса ячеек (1-based): 
# C8 = Доход за 30 дней, BTC (ряд 8, столбец C)
# C9 = Доход за 30 дней, USDT (ряд 9, столбец C)

formula_30days_btc = "=(30*86400*3.125*E9*1000000000000)/(D5*4294967296)"
formula_30days_usdt = "=E10*C5"

batch_update_body = {
    "valueInputOption": "USER_ENTERED",
    "data": [
        {
            "range": "Sheet1!C8",
            "values": [[formula_30days_btc]],
        },
        {
            "range": "Sheet1!C9",
            "values": [[formula_30days_usdt]],
        },
    ],
}

service.spreadsheets().values().batchUpdate(
    spreadsheetId=spreadsheet_id,
    body=batch_update_body
).execute()

print("✅ Таблица обновлена с данными и формулами.")
