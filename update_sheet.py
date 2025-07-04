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
        print("⚠️ Не заданы TELEGRAM_BOT_TOKEN или TELEGRAM_CHAT_ID в переменных окружения.")
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

# Основные данные и константы
today = get_today_moldova()
prices = [p for p in [get_coindesk_price(), get_coingecko_price()] if p is not None]
btc_avg = round(sum(prices) / len(prices), 2) if prices else "N/A"
difficulty, hashrate = get_difficulty_and_hashrate()

num_miners = 1000
stock_hashrate = 150000
attracted_hashrate = 172500
distribution = "2.80%"
hashrate_distribution_ratio = 4830
avg_hashrate_per_miner = 150
hashrate_growth = 22500
partner_share = "1.00%"
developer_share = "1.80%"
partner_hashrate = 1725
developer_hashrate = 3105
growth_coefficient = "15%"
total_hashrate = 172500
useful_hashrate = 167670

# Для примера значения доходов — их можно заменить на реальные вычисления
partner_earnings_btc = 0.02573522
developer_earnings_btc = 0.04632340
partner_earnings_usdt = 2702.20
developer_earnings_usdt = 4863.96

# Формируем таблицу в виде списка списков
rows = [
    # Блок 1
    ["Дата", "Средний курс BTC", "Сложность", "Общий хешрейт сети, Th", "Доля привлечённого хешрейта, %"],
    [today, btc_avg, difficulty, hashrate, round((attracted_hashrate / float(hashrate)) * 100, 2) if hashrate != "N/A" else "N/A"],

    # Блок 2
    ["Кол-во майнеров", "Стоковый хешрейт, Th", "Привлечённый хешрейт, Th", "Распределение", "Хешрейт к распределению"],
    [num_miners, stock_hashrate, attracted_hashrate, distribution, hashrate_distribution_ratio],

    # Блок 3
    ["Средний хеш на майнер", "Прирост хешрейта, Th", "-", "Партнёр", "Разработчик"],
    [avg_hashrate_per_miner, hashrate_growth, "-", partner_share, developer_share],

    # Блок 4
    ["Коэфф. прироста", "Суммарный хешрейт, Th", "-", "Партнёр хешрейт", "Разработчик хешрейт"],
    [growth_coefficient, total_hashrate, "-", partner_hashrate, developer_hashrate],

    # Блок 5
    ["Полезный хешрейт, Th", "Доход за 30 дней, BTC (Партнёр)", "Доход за 30 дней, BTC (Разработчик)"],
    [useful_hashrate, partner_earnings_btc, developer_earnings_btc],

    # Блок 6
    ["Полезный хешрейт, Th", "Доход за 30 дней, USDT (Партнёр)", "Доход за 30 дней, USDT (Разработчик)"],
    [useful_hashrate, partner_earnings_usdt, developer_earnings_usdt]
]

# Добавляем данные в таблицу (без удаления старых данных)
for row in rows:
    sheet.append_row(row)

print(f"✅ Данные за {today} добавлены.")

send_telegram_message(
    f"✅ Таблица обновлена: {today}\n"
    f"Средний курс BTC (USD): {btc_avg}\n"
    f"Сложность: {difficulty}\n"
    f"Общий хешрейт сети: {hashrate}\n"
    f"Ссылка на таблицу: https://docs.google.com/spreadsheets/d/1SjT740pFA7zuZMgBYf5aT0IQCC-cv6pMsQpEXYgQSmU/edit?usp=sharing"
)
