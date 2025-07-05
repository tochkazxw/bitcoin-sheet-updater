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

# Авторизация Google Sheets API (если нужно форматирование — пока не используется)
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
credentials = service_account.Credentials.from_service_account_file("credentials.json", scopes=SCOPES)
service = build("sheets", "v4", credentials=credentials)

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
            print("✅ Telegram уведомление отправлено.")
        else:
            print(f"❌ Ошибка Telegram: {r.text}")
    except Exception as e:
        print(f"❌ Ошибка при отправке Telegram: {e}")

def get_today_moldova():
    tz = pytz.timezone('Europe/Chisinau')
    return datetime.datetime.now(tz).strftime("%d.%m.%Y")

def get_coingecko_price():
    try:
        r = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd", timeout=10)
        return float(r.json()["bitcoin"]["usd"])
    except Exception as e:
        print(f"Ошибка CoinGecko: {e}")
        return None

def get_coindesk_price():
    try:
        r = requests.get("https://api.coindesk.com/v1/bpi/currentprice.json", timeout=10)
        return float(r.json()["bpi"]["USD"]["rate_float"])
    except Exception as e:
        print(f"Ошибка CoinDesk: {e}")
        return None

def get_difficulty_and_hashrate():
    try:
        diff_resp = requests.get("https://blockchain.info/q/getdifficulty", timeout=10)
        hashrate_resp = requests.get("https://blockchain.info/q/hashrate", timeout=10)

        diff_str = diff_resp.text.strip()
        difficulty = diff_str if 'e' not in diff_str.lower() else f"{float(diff_str):.0f}"

        hashrate_ghs = float(hashrate_resp.text.strip())
        hashrate_ths = int(hashrate_ghs / 1000)

        return difficulty, hashrate_ths
    except Exception as e:
        print(f"Ошибка получения сложности и хешрейта: {e}")
        return "N/A", "N/A"

def read_previous_miners():
    try:
        col_a = sheet.col_values(1)
        for idx, val in enumerate(col_a):
            if val == "Кол-во майнеров":
                row_num = idx + 1
                miners_cell = sheet.cell(row_num + 1, 1).value
                if miners_cell and miners_cell.isdigit():
                    return int(miners_cell)
                break
        return 1000
    except Exception as e:
        print(f"Ошибка чтения количества майнеров: {e}")
        return 1000

try:
    today = get_today_moldova()

    prices = []
    for source_func in [get_coingecko_price, get_coindesk_price]:
        price = source_func()
        if price is not None:
            prices.append(price)
    btc_avg = round(sum(prices)/len(prices), 2) if prices else "N/A"

    difficulty, hashrate = get_difficulty_and_hashrate()

    miners = read_previous_miners()

    stock_hashrate = 150 * miners
    attracted_hashrate = int(stock_hashrate * 1.15)
    total_hashrate = stock_hashrate + attracted_hashrate
    attracted_share_percent = round(attracted_hashrate / total_hashrate * 100, 2)

    values = [
        ["Дата", "Средний курс BTC", "Сложность", "Общий хешрейт, Th", "Доля привлеченного хешрейта, %"],
        [today, btc_avg, difficulty, hashrate, attracted_share_percent],

        ["Кол-во майнеров", "Стоковый хешрейт", "Привлечённый хешрейт", "Распределение", "Хешрейт к распределению"],
        [miners, stock_hashrate, attracted_hashrate, 0.028, 4830],

        ["Средний хешрейт на майнер", "Прирост хешрейта", "", "Партнер", "Разработчик"],
        [150, attracted_hashrate - stock_hashrate, "", 0.01, 0.018],

        ["Коэфф. прироста", "Суммарный хешрейт", "", 1725, 3105],
        ["15%", total_hashrate, "Доход за 30 дней, BTC", 0.02573522, 0.04632340],

        ["Полезный хешрейт, Th", total_hashrate - int(total_hashrate * 0.028), "Доход за 30 дней, USDT", 2702.2, 4863.96]
    ]

    last_row = len(sheet.get_all_values())
    start_row = last_row + 2

    for i, row in enumerate(values):
        sheet.insert_row(row, start_row + i)

    send_telegram_message(
        f"✅ Таблица обновлена: {today}\n"
        f"Средний курс BTC: {btc_avg}\n"
        f"Сложность: {difficulty}\n"
        f"Хешрейт: {total_hashrate} Th/s\n"
        f"<a href='https://docs.google.com/spreadsheets/d/1SjT740pFA7zuZMgBYf5aT0IQCC-cv6pMsQpEXYgQSmU/edit'>Ссылка на таблицу</a>"
    )

    print("✅ Обновление таблицы завершено.")

except Exception as e:
    print(f"❌ Ошибка: {e}")
    send_telegram_message(f"❌ Ошибка при обновлении таблицы: {e}")
