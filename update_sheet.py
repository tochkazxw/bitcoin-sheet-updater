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

# Авторизация Google Sheets API
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
credentials = service_account.Credentials.from_service_account_file("credentials.json", scopes=SCOPES)
service = build("sheets", "v4", credentials=credentials)

# Функция отправки Telegram-уведомления
def send_telegram_message(text):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        print("⚠️ Не заданы TELEGRAM_BOT_TOKEN или TELEGRAM_CHAT_ID.")
        return
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
        r = requests.post(url, data=payload, timeout=10)
        if r.status_code == 200:
            print("✅ Уведомление отправлено в Telegram.")
        else:
            print(f"❌ Ошибка отправки Telegram: {r.text}")
    except Exception as e:
        print(f"❌ Telegram исключение: {e}")

# Получение даты в часовом поясе Молдовы
def get_today_moldova():
    tz = pytz.timezone('Europe/Chisinau')
    return datetime.datetime.now(tz).strftime("%d.%m.%Y")

# Расширенная функция получения курса BTC из нескольких источников
def get_btc_price():
    sources = [
        {
            "name": "CoinGecko",
            "url": "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd",
            "parser": lambda r: float(r.json()["bitcoin"]["usd"])
        },
        {
            "name": "CoinDesk",
            "url": "https://api.coindesk.com/v1/bpi/currentprice.json",
            "parser": lambda r: float(r.json()["bpi"]["USD"]["rate_float"])
        },
        {
            "name": "Binance",
            "url": "https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT",
            "parser": lambda r: float(r.json()["price"])
        },
        {
            "name": "Kraken",
            "url": "https://api.kraken.com/0/public/Ticker?pair=XBTUSD",
            "parser": lambda r: float(r.json()["result"]["XXBTZUSD"]["c"][0])
        }
    ]
    
    for source in sources:
        try:
            response = requests.get(source["url"], timeout=10)
            response.raise_for_status()
            price = source["parser"](response)
            print(f"Цена BTC от {source['name']}: {price}")
            return price
        except Exception as e:
            print(f"Ошибка получения курса от {source['name']}: {e}")
    
    print("Не удалось получить курс BTC с всех источников.")
    return None

# Получение сложности и хешрейта из blockchain.info
def get_difficulty_and_hashrate():
    try:
        diff = requests.get("https://blockchain.info/q/getdifficulty", timeout=10).text.strip()
        hashrate = requests.get("https://blockchain.info/q/hashrate", timeout=10).text.strip()
        return diff, hashrate
    except Exception as e:
        print(f"Ошибка получения сложности и хешрейта: {e}")
        return "N/A", "N/A"

try:
    today = get_today_moldova()
    btc_price = get_btc_price()
    if btc_price is None:
        btc_price = "N/A"
    difficulty, hashrate = get_difficulty_and_hashrate()

    # Примерные хешрейты для расчётов
    stock_hashrate = 150000
    attracted_hashrate = 172500
    total_hashrate = stock_hashrate + attracted_hashrate
    attracted_share_percent = round(attracted_hashrate / total_hashrate * 100, 2)

    values = [
        ["Дата", "Средний курс BTC", "Сложность", "Общий хешрейт", "Доля привлеченного хешрейта, %"],
        [today, btc_price, difficulty, total_hashrate, attracted_share_percent],

        ["Кол-во майнеров", "Стоковый хешрейт", "Привлечённый хешрейт", "Распределение", "Хешрейт к распределению"],
        [1000, stock_hashrate, attracted_hashrate, "2.80%", 4830],

        ["Средний хешрейт на майнер", "Прирост хешрейта", "", "Партнер", "Разработчик"],
        [150, 22500, "", "1%", "1.8%"],

        ["Коэфф. прироста", "Суммарный хешрейт", "", 1725, 3105],
        ["15%", 172500, "Доход за 30 дней, BTC", 0.02573522, 0.04632340],

        ["Полезный хешрейт, Th", 167670, "Доход за 30 дней, USDT", 2702.2, 4863.96]
    ]

    sheet.append_rows(values, value_input_option="USER_ENTERED")

    send_telegram_message(
        f"✅ Таблица обновлена: {today}\n"
        f"Средний курс BTC: {btc_price}\n"
        f"Сложность: {difficulty}\n"
        f"Хешрейт: {total_hashrate} Th/s\n"
        f"<a href='https://docs.google.com/spreadsheets/d/1SjT740pFA7zuZMgBYf5aT0IQCC-cv6pMsQpEXYgQSmU/edit'>Ссылка на таблицу</a>"
    )
    print("✅ Обновление завершено.")

except Exception as e:
    print(f"❌ Ошибка: {e}")
    send_telegram_message(f"❌ Ошибка при обновлении таблицы: {e}")
