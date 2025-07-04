import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests
import datetime
import pytz
from google.oauth2 import service_account
from googleapiclient.discovery import build
import os
from decimal import Decimal

# Авторизация
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)
sheet = client.open_by_key("1SjT740pFA7zuZMgBYf5aT0IQCC-cv6pMsQpEXYgQSmU").sheet1

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
credentials = service_account.Credentials.from_service_account_file("credentials.json", scopes=SCOPES)
service = build("sheets", "v4", credentials=credentials)

# Telegram
def send_telegram_message(text):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        return
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    try:
        requests.post(url, data=payload, timeout=10)
    except:
        pass

# Дата
def get_today_moldova():
    tz = pytz.timezone('Europe/Chisinau')
    now = datetime.datetime.now(tz)
    return now.strftime("%d.%m.%Y")

# BTC курс
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

# Сложность и хешрейт
def get_difficulty_and_hashrate():
    try:
        difficulty = requests.get("https://blockchain.info/q/getdifficulty", timeout=10).text
        hashrate = float(requests.get("https://blockchain.info/q/hashrate", timeout=10).text)
        return format(Decimal(difficulty), 'f'), str(int(hashrate))
    except:
        return "N/A", "N/A"

# Основные данные
today = get_today_moldova()
prices = [p for p in [get_coindesk_price(), get_coingecko_price()] if p]
btc_avg = round(sum(prices) / len(prices), 2) if prices else "N/A"
difficulty, hashrate = get_difficulty_and_hashrate()

# Получение начальной строки
all_rows = sheet.get_all_values()
start_row = len(all_rows) + 2
r = start_row

# Вставка данных
rows = [
    ["Дата", "Средний курс BTC", "Сложность", "Общий хешрейт сети, Th", "Доля привлечённого хешрейта, %"],
    [today, btc_avg, difficulty, hashrate, 0.04],

    ["Кол-во майнеров", "Стоковый хешрейт, Th", "Привлечённый хешрейт, Th", "Распределение", "Хешрейт к распределению"],
    [1000, 150000, "", 0.028, ""],  # Важно: процент как число!

    ["Средний хеш на майнер", "Прирост хешрейта, Th", "-", "Партнёр", "Разработчик"],
    [150, 22500, "-", 0.01, 0.018],  # Партнёр и разработчик в виде чисел

    ["Коэфф. прироста", "Суммарный хешрейт, Th", "-", "Партнёр хешрейт", "Разработчик хешрейт"],
    ["15%", "", "-", "", ""],

    ["Полезный хешрейт, Th", "Доход 30 дней,BTC(Партнёр)", "Доход 30 дней,BTC(Разработчик)"],
    ["", "", ""],

    ["", "Доход 30 дней,USDT(Партнёр)", "Доход 30 дней,USDT(Разработчик)"],
    ["", "", ""],
]

for i, row in enumerate(rows):
    sheet.insert_row(row, index=r + i)

# Формулы
sheet.update_acell(f"C{r+3}", f"=B{r+3}+B{r+5}")               # Привлечённый хешрейт
sheet.update_acell(f"E{r+3}", f"=C{r+3}*D{r+3}")               # Хешрейт к распределению
sheet.update_acell(f"B{r+7}", f"=B{r+3}+B{r+5}")               # Суммарный хешрейт
sheet.update_acell(f"D{r+7}", f"=E{r+3}*D{r+5}")               # Партнёр хешрейт
sheet.update_acell(f"E{r+7}", f"=E{r+3}*E{r+5}")               # Разработчик хешрейт
sheet.update_acell(f"A{r+9}", f"=B{r+7}*0.9736")               # Полезный хешрейт

# BTC доход
sheet.update_acell(f"B{r+9}", f"=3.125*D{r+7}*1E12/(C{r+1}*2^32)")  # BTC партнёр
sheet.update_acell(f"C{r+9}", f"=3.125*E{r+7}*1E12/(C{r+1}*2^32)")  # BTC разработчик

# USDT доход
sheet.update_acell(f"B{r+11}", f"=B{r+9}*B{r+1}")
sheet.update_acell(f"C{r+11}", f"=C{r+9}*B{r+1}")

# Автоформат D{r+3} как процент (распределение)
service.spreadsheets().batchUpdate(
    spreadsheetId="1SjT740pFA7zuZMgBYf5aT0IQCC-cv6pMsQpEXYgQSmU",
    body={
        "requests": [
            {
                "repeatCell": {
                    "range": {
                        "sheetId": 0,
                        "startRowIndex": r + 2,
                        "endRowIndex": r + 3,
                        "startColumnIndex": 3,
                        "endColumnIndex": 4,
                    },
                    "cell": {
                        "userEnteredFormat": {
                            "numberFormat": {
                                "type": "PERCENT",
                                "pattern": "0.00%"
                            }
                        }
                    },
                    "fields": "userEnteredFormat.numberFormat"
                }
            }
        ]
    }
).execute()

# Telegram
send_telegram_message(
    f"✅ Таблица обновлена: {today}\n"
    f"Средний курс BTC (USD): {btc_avg}\n"
    f"Сложность: {difficulty}\n"
    f"Хешрейт: {hashrate}\n"
    f"Ссылка: https://docs.google.com/spreadsheets/d/1SjT740pFA7zuZMgBYf5aT0IQCC-cv6pMsQpEXYgQSmU/edit?usp=sharing"
)
