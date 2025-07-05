import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests
import datetime
import pytz
import os
import time
import socket
import warnings
from decimal import Decimal
from google.oauth2 import service_account
from googleapiclient.discovery import build
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

warnings.filterwarnings("ignore", category=DeprecationWarning)

SPREADSHEET_ID = "1SjT740pFA7zuZMgBYf5aT0IQCC-cv6pMsQpEXYgQSmU"
CREDENTIALS_FILE = "credentials.json"
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
MAX_RETRIES = 3
REQUEST_TIMEOUT = 10

def init_google_sheets():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(SPREADSHEET_ID).sheet1

    SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
    credentials = service_account.Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
    service = build("sheets", "v4", credentials=credentials)

    return sheet, service

def get_current_date():
    tz = pytz.timezone('Europe/Chisinau')
    return datetime.datetime.now(tz).strftime("%d.%m.%y")

def safe_api_request(url, parser, retries=MAX_RETRIES):
    for attempt in range(retries):
        try:
            response = requests.get(url, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            return parser(response)
        except (requests.exceptions.RequestException, socket.gaierror) as e:
            print(f"Попытка {attempt + 1} из {retries} не удалась для {url}: {e}")
            if attempt < retries - 1:
                time.sleep(2)
    return None

def get_btc_price():
    apis = [
        {
            "name": "CoinGecko",
            "url": "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd",
            "parser": lambda r: float(r.json()["bitcoin"]["usd"])
        },
        {
            "name": "Alternative.me",
            "url": "https://api.alternative.me/v2/ticker/bitcoin/",
            "parser": lambda r: float(r.json()["data"]["1"]["quotes"]["USD"]["price"])
        }
    ]

    prices = []
    for api in apis:
        price = safe_api_request(api["url"], api["parser"])
        if price is not None:
            prices.append(price)
            print(f"Курс успешно получен от {api['name']}")
    
    return round(sum(prices) / len(prices), 2) if prices else None

def get_difficulty_and_hashrate():
    try:
        # Можно заменить на реальный API
        difficulty = 1.17e14
        hashrate = 965130501885  # хешрейт в H/s
        return f"{difficulty:.2E}", f"{hashrate / 1e12:,.0f}"  # Вернём TH/s
    except Exception as e:
        print(f"Ошибка получения сложности и хешрейта: {e}")
        return "1.17E+14", "965,130"

def calculate_values(btc_price, difficulty_str, hashrate_str):
    try:
        difficulty = float(difficulty_str.replace(',', ''))
        hashrate = float(hashrate_str.replace(',', ''))

        miners = 1000
        avg_hash_per_miner = 150
        stock_hashrate = miners * avg_hash_per_miner
        growth_rate = 0.15
        attracted_hashrate = stock_hashrate * growth_rate
        total_hashrate = stock_hashrate + attracted_hashrate
        distribution_percent = 0.028
        useful_hashrate = total_hashrate * (1 - distribution_percent)

        partner_percent = 0.01
        dev_percent = 0.018

        partner_btc = (30 * 86400 * 3.125 * attracted_hashrate * 1e12) / (difficulty * 4294967296)
        dev_btc = partner_btc * (dev_percent / partner_percent)

        partner_usdt = partner_btc * btc_price
        dev_usdt = dev_btc * btc_price

        return {
            "miners": miners,
            "stock_hashrate": f"{stock_hashrate:,.0f}",
            "attracted_hashrate": f"{attracted_hashrate:,.0f}",
            "total_hashrate": f"{total_hashrate:,.0f}",
            "useful_hashrate": f"{useful_hashrate:,.0f}",
            "partner_btc": f"{partner_btc:.8f}",
            "dev_btc": f"{dev_btc:.8f}",
            "partner_usdt": f"{partner_usdt:,.2f}",
            "dev_usdt": f"{dev_usdt:,.2f}",
            "hashrate_to_distribute": f"{useful_hashrate * partner_percent:,.0f}"
        }
    except Exception as e:
        print(f"Ошибка расчетов: {e}")
        return None

def send_telegram_message(text):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "HTML"}
    try:
        requests.post(url, json=payload, timeout=REQUEST_TIMEOUT)
    except Exception as e:
        print(f"Ошибка отправки в Telegram: {e}")

def update_spreadsheet():
    try:
        sheet, service = init_google_sheets()
        today = get_current_date()
        btc_price = get_btc_price()
        difficulty, hashrate = get_difficulty_and_hashrate()

        if btc_price is None:
            raise ValueError("Не удалось получить курс BTC")

        calculated = calculate_values(btc_price, difficulty, hashrate)
        if not calculated:
            raise ValueError("Ошибка в расчетах производных значений")

        values = [
            ["Параметры сети", "Курс", "Сложность", "Общий хешрейт сети, Th", "В привлеченного хешрейта, %"],
            [today, btc_price, difficulty, hashrate, "0.04"],
            ["Количество майнеров", "Стоковый хешрейт, Th", "Привлеченный хешрейт, Th", "Распределение", "Хешрейт к распределению"],
            [calculated["miners"], calculated["stock_hashrate"], calculated["attracted_hashrate"], "2.80%", calculated["hashrate_to_distribute"]],
            ["Средний хешрейт на майнер", "Прирост хешрейта", "", "Партнер", "Разработчик"],
            ["150", "22500", "", "1.00%", "1.80%"],
            ["Коэфф. прироста", "Суммарный хешрейт", "", calculated["partner_btc"], calculated["dev_btc"]],
            ["15%", calculated["total_hashrate"], "Доход за 30 дней, BTC", "", ""],
            ["Полезный хешрейт, Th", calculated["useful_hashrate"], "Доход за 30 дней, USDT", calculated["partner_usdt"], calculated["dev_usdt"]]
        ]

        sheet.clear()
        sheet.update(range_name="A1:E9", values=values)

        spreadsheet = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
        sheet_id = next((s['properties']['sheetId'] for s in spreadsheet['sheets'] if s['properties']['title'] == sheet.title), None)
        if sheet_id is None:
            raise ValueError("Не удалось получить sheetId")

        formatting_requests = [
            {
                "repeatCell": {
                    "range": {"sheetId": sheet_id, "startRowIndex": 0, "endRowIndex": 1},
                    "cell": {"userEnteredFormat": {"textFormat": {"bold": True}}},
                    "fields": "userEnteredFormat.textFormat.bold"
                }
            },
            {
                "updateBorders": {
                    "range": {
                        "sheetId": sheet_id,
                        "startRowIndex": 0,
                        "endRowIndex": len(values),
                        "startColumnIndex": 0,
                        "endColumnIndex": 5
                    },
                    "top": {"style": "SOLID", "color": {"red": 0, "green": 0, "blue": 0}},
                    "bottom": {"style": "SOLID", "color": {"red": 0, "green": 0, "blue": 0}},
                    "left": {"style": "SOLID", "color": {"red": 0, "green": 0, "blue": 0}},
                    "right": {"style": "SOLID", "color": {"red": 0, "green": 0, "blue": 0}},
                    "innerHorizontal": {"style": "SOLID", "color": {"red": 0.8, "green": 0.8, "blue": 0.8}},
                    "innerVertical": {"style": "SOLID", "color": {"red": 0.8, "green": 0.8, "blue": 0.8}}
                }
            }
        ]

        service.spreadsheets().batchUpdate(spreadsheetId=SPREADSHEET_ID, body={"requests": formatting_requests}).execute()

        message = (
            f"✅ Таблица успешно обновлена\n"
            f"Дата: {today}\n"
            f"Курс BTC: ${btc_price}\n"
            f"Сложность: {difficulty}\n"
            f"Хешрейт: {hashrate} Th/s\n"
            f"Ссылка: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit"
        )
        send_telegram_message(message)

    except Exception as e:
        error_msg = f"❌ Ошибка при обновлении таблицы: {str(e)}"
        print(error_msg)
        send_telegram_message(error_msg)
        raise

if __name__ == "__main__":
    update_spreadsheet()
