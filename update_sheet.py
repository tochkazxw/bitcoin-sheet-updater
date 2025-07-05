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
        difficulty = "{:,.0f}".format(float(diff_str)).replace(",", " ")

        hashrate_ghs = float(hashrate_resp.text.strip())
        hashrate_ths = int(hashrate_ghs / 1000)

        return difficulty, hashrate_ths
    except Exception as e:
        print(f"Ошибка получения сложности и хешрейта: {e}")
        return "N/A", "N/A"

def safe_int(val, default=0):
    try:
        return int(str(val).replace(',', '').replace(' ', ''))
    except:
        return default

def safe_float(val, default=0.0):
    try:
        return float(str(val).replace(',', '.').replace('%', '').strip())
    except:
        return default

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)
sheet = client.open_by_key("1SjT740pFA7zuZMgBYf5aT0IQCC-cv6pMsQpEXYgQSmU").sheet1

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
credentials = service_account.Credentials.from_service_account_file("credentials.json", scopes=SCOPES)
service = build("sheets", "v4", credentials=credentials)

def read_previous_table_values():
    all_values = sheet.get_all_values()
    if not all_values:
        return None

    last_table_start = None
    for i in reversed(range(len(all_values))):
        if all_values[i] and all_values[i][0] == "Дата":
            last_table_start = i
            break

    if last_table_start is None:
        return None

    table_length = 11

    if last_table_start + table_length > len(all_values):
        return all_values[last_table_start:]
    else:
        return all_values[last_table_start:last_table_start + table_length]

try:
    today = get_today_moldova()

    prices = []
    for source_func in [get_coingecko_price, get_coindesk_price]:
        price = source_func()
        if price is not None:
            prices.append(price)
    btc_avg = round(sum(prices) / len(prices), 2) if prices else "N/A"

    difficulty, hashrate = get_difficulty_and_hashrate()

    previous_table = read_previous_table_values()

    miners = 1000
    stock_hashrate = 150000
    attracted_hashrate = 172500
    distribution = 0.028
    hashrate_distribution_value = 4830
    avg_hashrate_per_miner = 150
    increase_hashrate = 22500
    partner_share = 0.01
    developer_share = 0.018
    growth_coeff = 0.15
    total_hashrate = 172500
    btc_30d_income = 0.02573522
    btc_income_dev = 0.04632340
    useful_hashrate = 167670
    usdt_30d_income = 2702.2
    usdt_income_dev = 4863.96
    parthash = 1725
    rabhash = 3105
    tsotah = 0.0
    if previous_table:
        try:
            miners = safe_int(previous_table[2][1], miners)
            stock_hashrate = safe_int(previous_table[2][2], stock_hashrate)
            attracted_hashrate = safe_int(previous_table[2][3], attracted_hashrate)
            distribution = safe_float(previous_table[2][4], distribution)
            hashrate_distribution_value = safe_int(previous_table[3][4], hashrate_distribution_value)

            avg_hashrate_per_miner = safe_int(previous_table[4][0], avg_hashrate_per_miner)
            increase_hashrate = safe_int(previous_table[4][1], increase_hashrate)
            partner_share = safe_float(previous_table[4][3], partner_share)
            developer_share = safe_float(previous_table[4][4], developer_share)

            growth_coeff = safe_float(previous_table[5][0], growth_coeff)
            total_hashrate = safe_int(previous_table[5][1], total_hashrate)
            btc_30d_income = safe_float(previous_table[5][3], btc_30d_income)
            btc_income_dev = safe_float(previous_table[5][4], btc_income_dev)

            useful_hashrate = safe_int(previous_table[6][1], useful_hashrate)
            usdt_30d_income = safe_float(previous_table[6][3], usdt_30d_income)
            usdt_income_dev = safe_float(previous_table[6][4], usdt_income_dev)


            tsotah = round(attracted_hashrate / hashrate * 100, 2)

        except Exception as e:
            print(f"❌ Ошибка чтения данных из предыдущей таблицы: {e}")

    values = [
        ["Дата", "Средний курс BTC", "Сложность", "Общий хешрейт, Th", "Доля привлеченного хешрейта, %"],
        [today, btc_avg, difficulty, hashrate, tsotah],

        ["Кол-во майнеров", "Стоковый хешрейт", "Привлечённый хешрейт", "Распределение", "Хешрейт к распределению"],
        [miners, stock_hashrate, attracted_hashrate, distribution, hashrate_distribution_value],

        ["Средний хешрейт на майнер", "Прирост хешрейта", "", "Партнер", "Разработчик"],
        [avg_hashrate_per_miner, increase_hashrate, "", partner_share, developer_share],

        ["Коэфф. прироста", "Суммарный хешрейт", "", parthash, rabhash],
        [growth_coeff, total_hashrate, "Доход за 30 дней, BTC", btc_30d_income, btc_income_dev],

        ["Полезный хешрейт, Th", useful_hashrate, "Доход за 30 дней, USDT", usdt_30d_income, usdt_income_dev]
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
    try:
        send_telegram_message(f"❌ Ошибка при обновлении таблицы: {e}")
    except:
        pass
