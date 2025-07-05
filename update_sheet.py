import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests
import datetime
import pytz
from googleapiclient.discovery import build
from google.oauth2 import service_account
import os

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

def find_last_table(sheet, header="Дата", table_rows=11):
    all_values = sheet.get_all_values()
    if not all_values:
        return None, None

    last_table_start = None
    for i in reversed(range(len(all_values))):
        if len(all_values[i]) > 0 and all_values[i][0] == header:
            last_table_start = i
            break

    if last_table_start is None:
        return None, None

    table_data = all_values[last_table_start:last_table_start + table_rows]
    return table_data, last_table_start

# --- Авторизация Google Sheets ---

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)
sheet = client.open_by_key("1SjT740pFA7zuZMgBYf5aT0IQCC-cv6pMsQpEXYgQSmU").sheet1

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
credentials = service_account.Credentials.from_service_account_file("credentials.json", scopes=SCOPES)
service = build("sheets", "v4", credentials=credentials)

try:
    today = get_today_moldova()

    prices = []
    for source_func in [get_coingecko_price, get_coindesk_price]:
        price = source_func()
        if price is not None:
            prices.append(price)
    btc_avg = round(sum(prices)/len(prices), 2) if prices else "N/A"

    difficulty, hashrate = get_difficulty_and_hashrate()

    previous_table, start_row = find_last_table(sheet)

    # Дефолтные значения, если не нашли предыдущую таблицу
    miners = 1000
    stock_hashrate = 150000
    attracted_hashrate = 172500
    total_hashrate = 172500
    attracted_share_percent = 0.04
    growth_coeff = 0.15
    avg_hashrate_per_miner = 150
    increase_hashrate = attracted_hashrate - stock_hashrate
    useful_hashrate = total_hashrate - int(total_hashrate * 0.028)
    btc_30d_income = 0.02573522
    usdt_30d_income = 2702.2
    partner_share = 0.01
    developer_share = 0.018
    distribution = 0.028
    hashrate_distribution_value = 4830
    btc_income_dev = 0.04632340
    usdt_income_dev = 4863.96
    some_value_1725 = 1725
    some_value_3105 = 3105

    if previous_table:
        try:
            miners = int(previous_table[2][1])
            stock_hashrate = int(previous_table[2][2])
            attracted_hashrate = int(previous_table[2][3])
            distribution = float(previous_table[2][4])
            hashrate_distribution_value = int(previous_table[3][4])

            avg_hashrate_per_miner = int(previous_table[4][0])
            increase_hashrate = int(previous_table[4][1])
            partner_share = float(previous_table[4][3])
            developer_share = float(previous_table[4][4])

            growth_coeff = float(previous_table[5][0])
            total_hashrate = int(previous_table[5][1])
            btc_30d_income = float(previous_table[5][3])
            btc_income_dev = float(previous_table[5][4])

            useful_hashrate = int(previous_table[6][1])
            usdt_30d_income = float(previous_table[6][3])
            usdt_income_dev = float(previous_table[6][4])
        except Exception as e:
            print(f"Ошибка чтения данных из предыдущей таблицы: {e}")

    # Формируем новую таблицу
    values = [
        ["Дата", "Средний курс BTC", "Сложность", "Общий хешрейт, Th", "Доля привлеченного хешрейта, %"],
        [today, btc_avg, difficulty, hashrate, attracted_share_percent],

        ["Кол-во майнеров", "Стоковый хешрейт", "Привлечённый хешрейт", "Распределение", "Хешрейт к распределению"],
        [miners, stock_hashrate, attracted_hashrate, distribution, hashrate_distribution_value],

        ["Средний хешрейт на майнер", "Прирост хешрейта", "", "Партнер", "Разработчик"],
        [avg_hashrate_per_miner, increase_hashrate, "", partner_share, developer_share],

        ["Коэфф. прироста", "Суммарный хешрейт", "", some_value_1725, some_value_3105],
        [growth_coeff, total_hashrate, "Доход за 30 дней, BTC", btc_30d_income, btc_income_dev],

        ["Полезный хешрейт, Th", useful_hashrate, "Доход за 30 дней, USDT", usdt_30d_income, usdt_income_dev]
    ]

    # Вставляем новую таблицу под предыдущей с пустой строкой
    insert_start_row = start_row + len(previous_table) + 2 if start_row is not None else len(sheet.get_all_values()) + 2

    for i, row in enumerate(values):
        sheet.insert_row(row, insert_start_row + i)

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
    try:
        send_telegram_message(f"❌ Ошибка при обновлении таблицы: {e}")
    except:
        pass
