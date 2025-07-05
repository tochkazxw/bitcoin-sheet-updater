import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests
import datetime
import pytz
from googleapiclient.discovery import build
from google.oauth2 import service_account
import os

# Авторизация
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)
sheet = client.open_by_key("1SjT740pFA7zuZMgBYf5aT0IQCC-cv6pMsQpEXYgQSmU").sheet1

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
credentials = service_account.Credentials.from_service_account_file("credentials.json", scopes=SCOPES)
service = build("sheets", "v4", credentials=credentials)

# Telegram уведомление
def send_telegram_message(text):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        print("⚠️ TELEGRAM_BOT_TOKEN или CHAT_ID не указаны")
        return
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
        requests.post(url, data=payload, timeout=10)
    except Exception as e:
        print(f"Ошибка Telegram: {e}")

# Получить дату
def get_today_moldova():
    tz = pytz.timezone('Europe/Chisinau')
    return datetime.datetime.now(tz).strftime("%d.%m.%Y")

# Получить цену BTC
def get_btc_price():
    try:
        r1 = requests.get("https://api.coindesk.com/v1/bpi/currentprice.json", timeout=10)
        r2 = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd", timeout=10)
        prices = [float(r1.json()["bpi"]["USD"]["rate_float"]), float(r2.json()["bitcoin"]["usd"])]
        return round(sum(prices) / len(prices), 2)
    except:
        return "N/A"

# Получить хешрейт и сложность (в полных цифрах)
def get_difficulty_and_hashrate():
    try:
        diff = int(float(requests.get("https://blockchain.info/q/getdifficulty", timeout=10).text))
        hashrate_raw = float(requests.get("https://blockchain.info/q/hashrate", timeout=10).text)
        hashrate_th = int(hashrate_raw)  # в Th
        return diff, hashrate_th
    except:
        return "N/A", "N/A"

# Найти последнюю строку с данными
def find_last_filled_row():
    data = sheet.get_all_values()
    return len(data)

# Получить количество майнеров из последней таблицы
def get_previous_miners():
    data = sheet.get_all_values()
    for i in range(len(data) - 1, -1, -1):
        if "Кол-во майнеров" in data[i]:
            try:
                return int(data[i + 1][0])
            except:
                break
    return 1000  # по умолчанию

# Основной блок
try:
    today = get_today_moldova()
    btc_price = get_btc_price()
    difficulty, hashrate = get_difficulty_and_hashrate()

    miners = get_previous_miners()
    avg_hashrate_per_miner = 150
    stock_hashrate = miners * avg_hashrate_per_miner
    growth_rate = 0.15
    attracted_hashrate = int(stock_hashrate * growth_rate)
    total_hashrate = stock_hashrate + attracted_hashrate
    distribution = "2.80%"
    attracted_share_percent = round(attracted_hashrate / total_hashrate * 100, 2)
    useful_hashrate = int(total_hashrate * 0.972)

    values = [
        ["Дата", "Средний курс BTC", "Сложность", "Общий хешрейт, Th", "Доля привлеченного хешрейта, %"],
        [today, btc_price, difficulty, hashrate, attracted_share_percent],

        ["Кол-во майнеров", "Стоковый хешрейт", "Привлечённый хешрейт", "Распределение", "Хешрейт к распределению"],
        [miners, stock_hashrate, attracted_hashrate, distribution, 4830],

        ["Средний хешрейт на майнер", "Прирост хешрейта", "", "Партнер", "Разработчик"],
        [150, attracted_hashrate, "", "1%", "1.8%"],

        ["Коэфф. прироста", "Суммарный хешрейт", "", "Доход за 30 дней, BTC", "Доход за 30 дней, USDT"],
        ["15%", total_hashrate, "", 0.02573522, 2702.2],

        ["Полезный хешрейт, Th", useful_hashrate, "", 0.04632340, 4863.96]
    ]

    # Вставка ниже последней таблицы
    last_row = find_last_filled_row()
    sheet.update(f"A{last_row + 2}", values)

    send_telegram_message(
        f"✅ Таблица обновлена: {today}\n"
        f"BTC: {btc_price} USD\n"
        f"Сложность: {difficulty}\n"
        f"Хешрейт сети: {hashrate} Th/s\n"
        f"<a href='https://docs.google.com/spreadsheets/d/1SjT740pFA7zuZMgBYf5aT0IQCC-cv6pMsQpEXYgQSmU/edit'>Открыть таблицу</a>"
    )

    print("✅ Успешно")

except Exception as e:
    print(f"❌ Ошибка: {e}")
    send_telegram_message(f"❌ Ошибка при обновлении: {e}")
