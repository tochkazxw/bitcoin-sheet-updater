import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests
import datetime
import pytz
from decimal import Decimal
import os
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Конфигурация
SPREADSHEET_ID = "1SjT740pFA7zuZMgBYf5aT0IQCC-cv6pMsQpEXYgQSmU"
CREDENTIALS_FILE = "credentials.json"
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def init_google_sheets():
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, scope)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(SPREADSHEET_ID).sheet1
        
        SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
        credentials = service_account.Credentials.from_service_account_file(
            CREDENTIALS_FILE, scopes=SCOPES)
        service = build("sheets", "v4", credentials=credentials)
        
        return sheet, service
    except Exception as e:
        print(f"Ошибка инициализации Google Sheets: {e}")
        raise

def get_current_date():
    tz = pytz.timezone('Europe/Chisinau')
    return datetime.datetime.now(tz).strftime("%d.%m.%y")

def get_btc_price():
    apis = [
        {"name": "CoinDesk", "url": "https://api.coindesk.com/v1/bpi/currentprice.json",
         "parser": lambda r: float(r.json()["bpi"]["USD"]["rate_float"])},
        {"name": "CoinGecko", "url": "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd",
         "parser": lambda r: float(r.json()["bitcoin"]["usd"])}
    ]
    
    prices = []
    for api in apis:
        try:
            response = requests.get(api["url"], timeout=10)
            response.raise_for_status()
            prices.append(api["parser"](response))
        except Exception as e:
            print(f"Ошибка при запросе к {api['name']}: {e}")
    
    return round(sum(prices) / len(prices), 2) if prices else None

def get_difficulty_and_hashrate():
    try:
        difficulty = float(requests.get("https://blockchain.info/q/getdifficulty", timeout=10).text)
        hashrate = float(requests.get("https://blockchain.info/q/hashrate", timeout=10).text)
        return f"{difficulty:.2E}", f"{hashrate/1e12:,.0f}"
    except Exception as e:
        print(f"Ошибка при получении сложности и хешрейта: {e}")
        return "N/A", "N/A"

def calculate_values(btc_price, hashrate):
    try:
        hashrate = float(hashrate.replace(',', '')) if hashrate != "N/A" else 0
        
        # Основные параметры
        miners = 1000
        avg_hash_per_miner = 150
        stock_hashrate = miners * avg_hash_per_miner
        growth_rate = 0.15
        attracted_hashrate = stock_hashrate * growth_rate
        total_hashrate = stock_hashrate + attracted_hashrate
        distribution_percent = 0.028
        useful_hashrate = total_hashrate * (1 - distribution_percent)
        
        # Доходы
        partner_percent = 0.01
        dev_percent = 0.018
        
        partner_btc = (30*86400*3.125*attracted_hashrate*1e12)/(float(difficulty.split('E')[0])*(10**int(difficulty.split('E')[1]))*4294967296)
        dev_btc = partner_btc * (dev_percent/partner_percent)
        
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
            "dev_usdt": f"{dev_usdt:,.2f}"
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
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Ошибка отправки в Telegram: {e}")

def update_spreadsheet():
    try:
        sheet, service = init_google_sheets()
        
        # Получаем данные
        today = get_current_date()
        btc_price = get_btc_price()
        difficulty, hashrate = get_difficulty_and_hashrate()
        
        if not btc_price:
            raise ValueError("Не удалось получить курс BTC")
        
        # Вычисляем производные значения
        calculated = calculate_values(btc_price, hashrate)
        if not calculated:
            raise ValueError("Ошибка в расчетах")
        
        # Подготавливаем данные для вставки
        values = [
            ["Параметры сети", "Курс", "Сложность", "Общий хешрейт сети, Th", "В привлеченного хешрейта, %"],
            [today, btc_price, difficulty, hashrate, "0.04"],
            ["Количество майнеров", "Стоковый хешрейт, Th", "Привлеченный хешрейт, Th", "Распределение", "Хешрейт к распределению"],
            [calculated["miners"], calculated["stock_hashrate"], calculated["attracted_hashrate"], "2.80%", "4830"],
            ["Средний хешрейт на майнер", "Прирост хешрейта", "", "Партнер", "Разработчик"],
            ["150", "22500", "", "1.00%", "1.80%"],
            ["Коэфф. прироста", "Суммарный хешрейт", "", calculated["partner_btc"], calculated["dev_btc"]],
            ["15%", calculated["total_hashrate"], "Доход за 30 дней, BTC", "", ""],
            ["Полезный хешрейт, Th", calculated["useful_hashrate"], "Доход за 30 дней, USDT", calculated["partner_usdt"], calculated["dev_usdt"]]
        ]
        
        # Очищаем лист и вставляем данные
        sheet.clear()
        sheet.update("A1:E9", values)
        
        # Форматирование
        requests = [
            # Жирные заголовки
            {
                "repeatCell": {
                    "range": {"startRowIndex": 0, "endRowIndex": 1},
                    "cell": {"userEnteredFormat": {"textFormat": {"bold": True}}},
                    "fields": "userEnteredFormat.textFormat.bold"
                }
            },
            # Границы
            {
                "updateBorders": {
                    "range": {"startRowIndex": 0, "endRowIndex": 9, "startColumnIndex": 0, "endColumnIndex": 5},
                    "top": {"style": "SOLID", "color": {"red": 0, "green": 0, "blue": 0}},
                    "bottom": {"style": "SOLID", "color": {"red": 0, "green": 0, "blue": 0}},
                    "left": {"style": "SOLID", "color": {"red": 0, "green": 0, "blue": 0}},
                    "right": {"style": "SOLID", "color": {"red": 0, "green": 0, "blue": 0}},
                    "innerHorizontal": {"style": "SOLID", "color": {"red": 0.8, "green": 0.8, "blue": 0.8}},
                    "innerVertical": {"style": "SOLID", "color": {"red": 0.8, "green": 0.8, "blue": 0.8}}
                }
            }
        ]
        
        service.spreadsheets().batchUpdate(
            spreadsheetId=SPREADSHEET_ID,
            body={"requests": requests}
        ).execute()
        
        # Уведомление
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
