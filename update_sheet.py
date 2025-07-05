import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests
import datetime
import pytz
import os

# Авторизация
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)
sheet = client.open_by_key("1SjT740pFA7zuZMgBYf5aT0IQCC-cv6pMsQpEXYgQSmU").sheet1

# Функция Telegram (как у тебя)
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

# Получение даты в Молдове
def get_today_moldova():
    tz = pytz.timezone('Europe/Chisinau')
    return datetime.datetime.now(tz).strftime("%d.%m.%Y")

# Получение курса BTC с CoinDesk и CoinGecko
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

# Получение сложности
def get_difficulty():
    try:
        diff = float(requests.get("https://blockchain.info/q/getdifficulty", timeout=10).text)
        return round(diff, 2)
    except:
        return "N/A"

# Получение общего хешрейта с blockchain.info (Th/s)
def get_hashrate():
    try:
        hashrate = float(requests.get("https://blockchain.info/q/hashrate", timeout=10).text)
        # возвращаем в Th/s (дано в H/s), делим на 1e12
        return round(hashrate / 1e12, 2)
    except:
        return "N/A"

try:
    today = get_today_moldova()
    prices = [p for p in [get_coindesk_price(), get_coingecko_price()] if p is not None]
    btc_avg = round(sum(prices) / len(prices), 2) if prices else "N/A"
    difficulty = get_difficulty()
    total_hashrate = get_hashrate()  # теперь хешрейт из сети!

    # Твои данные без изменений
    stock_hashrate = 150000
    attracted_hashrate = 172500
    attracted_share_percent = round(attracted_hashrate / (stock_hashrate + attracted_hashrate) * 100, 2)

    new_rows = [
        ["Дата", "Средний курс BTC", "Сложность", "Общий хешрейт", "Доля привлеченного хешрейта, %"],
        [today, btc_avg, difficulty, total_hashrate, attracted_share_percent],

        ["Кол-во майнеров", "Стоковый хешрейт", "Привлечённый хешрейт", "Распределение", "Хешрейт к распределению"],
        [1000, stock_hashrate, attracted_hashrate, "2.80%", 4830],

        ["Средний хешрейт на майнер", "Прирост хешрейта", "", "Партнер", "Разработчик"],
        [150, 22500, "", "1%", "1.8%"],

        ["Коэфф. прироста", "Суммарный хешрейт", "", 1725, 3105],
        ["15%", 172500, "Доход за 30 дней, BTC", 0.02573522, 0.04632340],

        ["Полезный хешрейт, Th", 167670, "Доход за 30 дней, USDT", 2702.2, 4863.96]
    ]

    # Ищем первую пустую строку для вставки
    next_row = len(sheet.get_all_values()) + 1
    start_cell = f"A{next_row}"

    # Вставляем новые данные начиная с колонки A и первой пустой строки
    sheet.update(start_cell, new_rows, value_input_option="USER_ENTERED")

    send_telegram_message(
        f"✅ Таблица обновлена: {today}\n"
        f"Средний курс BTC: {btc_avg}\n"
        f"Сложность: {difficulty}\n"
        f"Хешрейт: {total_hashrate} Th/s\n"
        f"<a href='https://docs.google.com/spreadsheets/d/1SjT740pFA7zuZMgBYf5aT0IQCC-cv6pMsQpEXYgQSmU/edit'>Ссылка на таблицу</a>"
    )

    print("✅ Обновление завершено.")

except Exception as e:
    print(f"❌ Ошибка: {e}")
    send_telegram_message(f"❌ Ошибка при обновлении таблицы: {e}")
