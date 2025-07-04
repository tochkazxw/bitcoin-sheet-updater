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

def send_telegram_message(text):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        print("⚠️ Не заданы TELEGRAM_BOT_TOKEN или TELEGRAM_CHAT_ID.")
        return
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    try:
        resp = requests.post(url, data=payload, timeout=10)
        if resp.status_code == 200:
            print("✅ Уведомление в Telegram отправлено.")
        else:
            print(f"❌ Ошибка отправки уведомления в Telegram: {resp.text}")
    except Exception as e:
        print(f"❌ Исключение при отправке Telegram уведомления: {e}")

def get_today_moldova():
    tz = pytz.timezone('Europe/Chisinau')
    now = datetime.datetime.now(tz)
    return now.strftime("%d.%m.%Y")

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

# Основные переменные и расчёты
today = get_today_moldova()
prices = [p for p in [get_coindesk_price(), get_coingecko_price()] if p is not None]
btc_avg = round(sum(prices) / len(prices), 2) if prices else "N/A"
difficulty, hashrate = get_difficulty_and_hashrate()

num_miners = 1000
stock_hashrate = 150000
attracted_hashrate = 172500
distribution = "2.80%"
try:
    hashrate_float = float(hashrate)
    attracted_percent = round((attracted_hashrate / hashrate_float) * 100, 2)
except:
    attracted_percent = "N/A"

avg_hashrate_per_miner = 150
hashrate_growth = 22500
partner_share = "1%"
developer_share = "1.8%"
partner_hashrate = 1725
developer_hashrate = 3105
growth_coefficient = "15%"
total_hashrate = 172500
useful_hashrate = 167670

# Формируем строки для записи, каждая пара — заголовки + данные
rows_to_append = [
    ["Дата", "Средний курс BTC", "Сложность", "Общий хешрейт", "Доля привлеченного хешрейта, %"],
    [today, btc_avg, difficulty, hashrate, attracted_percent],

    ["Кол-во майнеров", "Стоковый хешрейт", "Привлечённый хешрейт", "Распределение", "Хешрейт к распределению"],
    [num_miners, stock_hashrate, attracted_hashrate, distribution, 4830],

    ["Средний хеш на майнер", "Прирост хешрейта", "-", "Партнер", "Разработчик"],
    [avg_hashrate_per_miner, hashrate_growth, "-", partner_share, developer_share],

    ["Коэфф. прироста", "Суммарный хешрейт", "-", partner_hashrate, developer_hashrate],
    [growth_coefficient, total_hashrate, "-", 1725, 3105],

    ["Доход за 30 дней, BTC", "=(30*86400*3,125*E22*1000000000000)/(D17*4294967296)", "=(30*86400*3,125*F22*1000000000000)/(D17*4294967296)"],
    
    ["Полезный хешрейт, Th", useful_hashrate, "Доход за 30 дней, USDT", "=E23*C17", "=F23*C17"]
]

# Опционально, можешь очистить лист перед добавлением (если нужно)
# sheet.clear()

# Запишем строки подряд, начиная с первой пустой строки
first_empty_row = len(sheet.get_all_values()) + 1
sheet.insert_rows(rows_to_append, row=first_empty_row)

print(f"✅ Таблица обновлена ({today}) с нужной структурой.")

send_telegram_message(
    f"✅ Таблица обновлена: {today}\n"
    f"Средний курс BTC: {btc_avg}\n"
    f"Сложность: {difficulty}\n"
    f"Хешрейт: {hashrate}\n"
    f"Доля привлеченного хешрейта: {attracted_percent}%\n"
    f"Ссылка на таблицу: https://docs.google.com/spreadsheets/d/1SjT740pFA7zuZMgBYf5aT0IQCC-cv6pMsQpEXYgQSmU/edit?usp=sharing"
)
