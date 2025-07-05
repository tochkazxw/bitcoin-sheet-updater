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

# Telegram уведомление
def send_telegram_message(text):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        print("⚠️ TELEGRAM_BOT_TOKEN или TELEGRAM_CHAT_ID не заданы.")
        return
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
        r = requests.post(url, data=payload, timeout=10)
        if r.status_code == 200:
            print("✅ Telegram отправлен.")
        else:
            print(f"❌ Ошибка Telegram: {r.text}")
    except Exception as e:
        print(f"❌ Telegram исключение: {e}")

# Текущая дата (Молдова)
def get_today_moldova():
    tz = pytz.timezone('Europe/Chisinau')
    return datetime.datetime.now(tz).strftime("%d.%m.%Y")

# Курсы BTC
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

# Получение сложности и общего хешрейта
def get_difficulty_and_hashrate():
    try:
        diff = float(requests.get("https://blockchain.info/q/getdifficulty", timeout=10).text)
        hashrate = float(requests.get("https://blockchain.info/q/hashrate", timeout=10).text)
        return round(diff, 2), round(hashrate)  # hashrate в GH/s
    except:
        return "N/A", "N/A"

# Основная логика
try:
    today = get_today_moldova()
    prices = [p for p in [get_coindesk_price(), get_coingecko_price()] if p is not None]
    btc_avg = round(sum(prices) / len(prices), 2) if prices else "N/A"
    difficulty, hashrate = get_difficulty_and_hashrate()  # hashrate в GH/s

    if hashrate == "N/A":
        raise ValueError("Не удалось получить общий хешрейт")

    # Приведем GH/s к TH/s
    network_hashrate_ths = hashrate / 1000  # TH/s

    # Хардкодные данные
    stock_hashrate = 150000  # TH/s
    attracted_hashrate = 172500  # TH/s
    total_hashrate = stock_hashrate + attracted_hashrate
    attracted_percent_of_network = round(attracted_hashrate / network_hashrate_ths * 100, 2)

    # Данные для вставки
    new_rows = [
        ["Дата", "Средний курс BTC", "Сложность", "Общий хешрейт (из сети)", "Доля привлеченного хешрейта, %"],
        [str(today), str(btc_avg), str(difficulty), str(round(network_hashrate_ths)), str(attracted_percent_of_network)],

        ["Кол-во майнеров", "Стоковый хешрейт", "Привлечённый хешрейт", "Распределение", "Хешрейт к распределению"],
        ["1000", str(stock_hashrate), str(attracted_hashrate), "2.80%", "4830"],

        ["Средний хешрейт на майнер", "Прирост хешрейта", "", "Партнер", "Разработчик"],
        ["150", "22500", "", "1%", "1.8%"],

        ["Коэфф. прироста", "Суммарный хешрейт", "", "Доход за 30 дней, BTC", "Доход за 30 дней, BTC"],
        ["15%", str(total_hashrate), "", "0.02573522", "0.04632340"],

        ["Полезный хешрейт, Th", "167670", "Доход за 30 дней, USDT", "2702.20", "4863.96"]
    ]

    # Вставляем строки в конец таблицы
    for row in new_rows:
        sheet.append_row(row, value_input_option="USER_ENTERED")

    # Telegram уведомление
    send_telegram_message(
        f"✅ Таблица обновлена: {today}\n"
        f"Средний курс BTC: {btc_avg}\n"
        f"Сложность: {difficulty}\n"
        f"Хешрейт сети: {round(network_hashrate_ths)} TH/s\n"
        f"<a href='https://docs.google.com/spreadsheets/d/1SjT740pFA7zuZMgBYf5aT0IQCC-cv6pMsQpEXYgQSmU/edit'>Открыть таблицу</a>"
    )

    print("✅ Данные добавлены в конец таблицы.")

except Exception as e:
    print(f"❌ Ошибка: {e}")
    send_telegram_message(f"❌ Ошибка при обновлении таблицы: {e}")
