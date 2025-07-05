import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests
import datetime
import pytz
from googleapiclient.discovery import build
from google.oauth2 import service_account
import os

# --- Функции вспомогательные ---

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

# --- Авторизация и подключение к Google Sheets ---

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)
sheet = client.open_by_key("1SjT740pFA7zuZMgBYf5aT0IQCC-cv6pMsQpEXYgQSmU").sheet1

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
credentials = service_account.Credentials.from_service_account_file("credentials.json", scopes=SCOPES)
service = build("sheets", "v4", credentials=credentials)

# --- Функция чтения предыдущих данных таблицы (последняя добавленная) ---

def read_previous_table_values():
    # Получаем все значения
    all_values = sheet.get_all_values()
    if not all_values:
        return None  # Таблица пустая

    # Найдём индекс, с которого начинается последняя таблица — по ключевому заголовку "Дата"
    last_table_start = None
    for i in reversed(range(len(all_values))):
        if all_values[i] and all_values[i][0] == "Дата":
            last_table_start = i
            break

    if last_table_start is None:
        return None

    # Считаем сколько строк занимает таблица (в нашем примере 11 строк)
    table_length = 11

    if last_table_start + table_length > len(all_values):
        # Если таблица неполная, берём до конца
        return all_values[last_table_start:]
    else:
        return all_values[last_table_start:last_table_start + table_length]

# --- Основной блок ---

try:
    today = get_today_moldova()

    prices = []
    for source_func in [get_coingecko_price, get_coindesk_price]:
        price = source_func()
        if price is not None:
            prices.append(price)
    btc_avg = round(sum(prices)/len(prices), 2) if prices else "N/A"

    difficulty, hashrate = get_difficulty_and_hashrate()

    previous_table = read_previous_table_values()

    # По умолчанию значения, если нет предыдущей таблицы
    miners = 1000
    stock_hashrate = 150000
    attracted_hashrate = 172500
    total_hashrate = 172500
    attracted_share_percent = 0.04

    # Если предыдущая таблица есть — пытаемся прочитать и использовать предыдущие данные (миннеры, хешрейты и т.д.)
    if previous_table:
        try:
            # Предположим, что данные лежат в фиксированных позициях в таблице, например:
            # Кол-во майнеров — строка 2 в таблице (index 1), столбец 1 (0-based)
            miners_val = previous_table[2][1]
            if miners_val.isdigit():
                miners = int(miners_val)

            stock_hashrate_val = previous_table[2][2]
            attracted_hashrate_val = previous_table[2][3]
            total_hashrate_val = previous_table[4][1]
            attracted_share_percent_val = previous_table[1][4]

            # Приводим к нужным типам
            stock_hashrate = int(stock_hashrate_val.replace(',', '').replace(' ', '')) if stock_hashrate_val else 150 * miners
            attracted_hashrate = int(attracted_hashrate_val.replace(',', '').replace(' ', '')) if attracted_hashrate_val else int(stock_hashrate * 1.15)
            total_hashrate = int(total_hashrate_val.replace(',', '').replace(' ', '')) if total_hashrate_val else stock_hashrate + attracted_hashrate
            attracted_share_percent = float(attracted_share_percent_val) if attracted_share_percent_val else round(attracted_hashrate / total_hashrate * 100, 2)

        except Exception as e:
            print(f"Ошибка обработки предыдущих данных: {e}")

    values = [
        ["Дата", "Средний курс BTC", "Сложность", "Общий хешрейт, Th", "Доля привлеченного хешрейта, %"],
        [today, btc_avg, difficulty, hashrate, attracted_share_percent],

        ["Кол-во майнеров", "Стоковый хешрейт", "Привлечённый хешрейт", "Распределение", "Хешрейт к распределению"],
        [miners, stock_hashrate, attracted_hashrate, 0.028, 4830],

        ["Средний хешрейт на майнер", "Прирост хешрейта", "", "Партнер", "Разработчик"],
        [150, attracted_hashrate - stock_hashrate, "", 0.01, 0.018],

        ["Коэфф. прироста", "Суммарный хешрейт", "", 1725, 3105],
        [0.15, total_hashrate, "Доход за 30 дней, BTC", 0.02573522, 0.04632340],

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
    try:
        send_telegram_message(f"❌ Ошибка при обновлении таблицы: {e}")
    except:
        pass
