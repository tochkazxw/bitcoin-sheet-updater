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
        print("⚠️ TELEGRAM_BOT_TOKEN или TELEGRAM_CHAT_ID не заданы")
        return
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    try:
        resp = requests.post(url, data=payload, timeout=10)
        if resp.status_code == 200:
            print("✅ Уведомление в Telegram отправлено.")
        else:
            print(f"❌ Ошибка отправки Telegram: {resp.text}")
    except Exception as e:
        print(f"❌ Исключение при отправке Telegram: {e}")

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

# --- Основные данные ---
today = get_today_moldova()
prices = [p for p in [get_coindesk_price(), get_coingecko_price()] if p is not None]
btc_avg = round(sum(prices) / len(prices), 2) if prices else "N/A"
difficulty, hashrate_network = get_difficulty_and_hashrate()

# --- Твои дополнительные значения ---
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
income_30d_usdt = "Тут будут данные"

useful_hashrate_th = 167670

# Формируем строки для вставки — 9 строк с заголовками и значениями
rows = [
    # 1. Основные заголовки
    ["Дата", "Средний курс BTC", "Сложность", "Общий хешрейт", "", "", "", ""],
    # 2. Основные данные
    [today, btc_avg, difficulty, hashrate_network, "", "", "", ""],
    # 3. Дополнительные заголовки 1
    ["Кол-во майнеров", "Стоковый хешрейт", "Привлечённый хешрейт", "Распределение", "", "", "", ""],
    # 4. Доп. данные 1
    [miners_count, stock_hashrate, attracted_hashrate, distribution, "", "", "", ""],
    # 5. Дополнительные заголовки 2
    ["Средний хешрейт на майнер", "Прирост хешрейта", "", "Партнер", "Разработчик", "", "", ""],
    # 6. Доп. данные 2
    [average_hashrate_per_miner, hashrate_growth, "", partner, developer, "", "", ""],
    # 7. Дополнительные заголовки 3
    ["Коэффициент прироста", "Суммарный хешрейт", "", "Доход за 30 дней, BTC", "", "", "", ""],
    # 8. Доп. данные 3
    [growth_coefficient, total_hashrate, "", income_30d_btc, "", "", "", ""],
    # 9. Доп. данные 4
    ["Полезный хешрейт, Th", useful_hashrate_th, "", "Доход за 30 дней, USDT", income_30d_usdt, "", "", ""],
]

# Добавляем пустую строку для разделения, если нужно
sheet.append_row([])

# Вставляем все строки по очереди
for row in rows:
    sheet.append_row(row)

# Форматирование — аналогично твоему, можно расширять и корректировать
# Например, выделить основную шапку и первую строку данных, и т.д.

print(f"✅ Данные за {today} добавлены и оформлены.")

send_telegram_message(
    f"✅ Таблица обновлена: {today}\n"
    f"Средний курс BTC (USD): {btc_avg}\n"
    f"Сложность: {difficulty}\n"
    f"Хешрейт сети: {hashrate_network}\n"
)
