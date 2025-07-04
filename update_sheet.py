import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests
import datetime
import pytz
import os

# Авторизация gspread
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)
sheet = client.open_by_key("1SjT740pFA7zuZMgBYf5aT0IQCC-cv6pMsQpEXYgQSmU").worksheet("Sheet1")

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

# Проверяем и записываем заголовки, если их нет
def ensure_headers(sheet):
    headers = [
        "Дата", "Средний курс BTC", "Сложность", "Общий хешрейт", "Доля привлеченного хешрейта, %",
        "Кол-во майнеров", "Стоковый хешрейт", "Привлечённый хешрейт", "Распределение", "Хешрейт к распределению",
        "Средний хеш на майнер", "Прирост хешрейта", "-", "Партнер", "Разработчик",
        "Коэфф. прироста", "Суммарный хешрейт", "-", "Партнер", "Разработчик",
        "Доход за 30 дней, BTC", "Доход за 30 дней, USDT", "Полезный хешрейт, Th"
    ]
    first_row = sheet.row_values(1)
    if not first_row or len(first_row) < 5 or first_row[0] != "Дата":
        sheet.insert_row(headers, 1)

# Основные переменные
today = get_today_moldova()
prices = [p for p in [get_coindesk_price(), get_coingecko_price()] if p is not None]
btc_avg = round(sum(prices) / len(prices), 2) if prices else "N/A"
difficulty, hashrate = get_difficulty_and_hashrate()

# Дополнительные значения
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
earnings_30days_btc = ""  # можно заполнить реальными значениями
earnings_30days_usdt = "" # можно заполнить реальными значениями
useful_hashrate = 167670
share_attracted_hashrate = "0.04"

# Убедимся, что заголовки есть
ensure_headers(sheet)

# Формируем строку для добавления (пример сгруппировал данные в одну строку — можно менять по желанию)
row_to_append = [
    today,
    str(btc_avg),
    difficulty,
    hashrate,
    share_attracted_hashrate,
    miners,
    stock_hashrate,
    attracted_hashrate,
    distribution,
    hashrate_distribution_ratio,
    avg_hashrate_per_miner,
    hashrate_growth,
    "-",
    partner_share,
    developer_share,
    growth_coefficient,
    total_hashrate,
    "-",
    partner_hashrate,
    developer_hashrate,
    earnings_30days_btc,
    earnings_30days_usdt,
    useful_hashrate
]

sheet.append_row(row_to_append)

# Отправляем уведомление в Telegram
send_telegram_message(
    f"✅ Таблица обновлена: {today}\n"
    f"Средний курс BTC (USD): {btc_avg}\n"
    f"Сложность: {difficulty}\n"
    f"Хешрейт: {hashrate}\n"
    f"Ссылка на таблицу: https://docs.google.com/spreadsheets/d/1SjT740pFA7zuZMgBYf5aT0IQCC-cv6pMsQpEXYgQSmU/edit?usp=sharing"
)
