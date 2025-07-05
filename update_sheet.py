import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests
import datetime
import pytz
from decimal import Decimal
import os
from google.oauth2 import service_account
from googleapiclient.discovery import build

# --- Конфигурация ---
SPREADSHEET_ID = "1SjT740pFA7zuZMgBYf5aT0IQCC-cv6pMsQpEXYgQSmU"
CREDENTIALS_FILE = "credentials.json"
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# --- Инициализация клиента Google Sheets ---
def init_google_sheets():
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets", 
                "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, scope)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(SPREADSHEET_ID).sheet1
        
        # Инициализация Google API
        SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
        credentials = service_account.Credentials.from_service_account_file(
            CREDENTIALS_FILE, scopes=SCOPES)
        service = build("sheets", "v4", credentials=credentials)
        
        return sheet, service
    except Exception as e:
        print(f"Ошибка инициализации Google Sheets: {e}")
        raise

# --- Telegram уведомления ---
def send_telegram_message(text):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram токен или chat ID не настроены")
        return
        
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML"
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
    except Exception as e:
        print(f"Ошибка отправки в Telegram: {e}")

# --- Получение данных ---
def get_current_date():
    tz = pytz.timezone('Europe/Chisinau')
    return datetime.datetime.now(tz).strftime("%d.%m.%Y")

def get_btc_price():
    apis = [
        {
            "name": "CoinDesk",
            "url": "https://api.coindesk.com/v1/bpi/currentprice.json",
            "parser": lambda r: float(r.json()["bpi"]["USD"]["rate_float"])
        },
        {
            "name": "CoinGecko",
            "url": "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd",
            "parser": lambda r: float(r.json()["bitcoin"]["usd"])
        }
    ]
    
    prices = []
    for api in apis:
        try:
            response = requests.get(api["url"], timeout=10)
            response.raise_for_status()
            prices.append(api["parser"](response))
            print(f"Успешно получен курс от {api['name']}")
        except Exception as e:
            print(f"Ошибка при запросе к {api['name']}: {e}")
    
    if not prices:
        raise ValueError("Не удалось получить курс BTC ни от одного источника")
    
    return round(sum(prices) / len(prices), 2)

def get_difficulty_and_hashrate():
    try:
        difficulty = requests.get("https://blockchain.info/q/getdifficulty", timeout=10).text
        hashrate = float(requests.get("https://blockchain.info/q/hashrate", timeout=10).text)
        return format(Decimal(difficulty), 'f'), str(int(hashrate))
    except Exception as e:
        print(f"Ошибка при получении сложности и хешрейта: {e}")
        return "N/A", "N/A"

# --- Основная логика ---
def main():
    try:
        # Инициализация
        sheet, service = init_google_sheets()
        
        # Получение данных
        today = get_current_date()
        btc_price = get_btc_price()
        difficulty, hashrate = get_difficulty_and_hashrate()
        
        print(f"Данные получены: {today}, BTC={btc_price}, сложность={difficulty}, хешрейт={hashrate}")
        
        # Определение строки для вставки
        all_values = sheet.get_all_values()
        insert_row = len(all_values) + 1
        
        # Подготовка данных
        values = [
            [today, btc_price, difficulty, hashrate, "=0.028"],
            ["=1000", "=150", f"=A{insert_row+1}*B{insert_row+1}", 
             f"=C{insert_row+2}*0.15", f"=C{insert_row+2}+D{insert_row+2}"],
            [f"=E{insert_row+2}-E{insert_row+2}*E{insert_row}", 
             f"=C{insert_row+2}+D{insert_row+2}", 
             f"=B{insert_row+3}*E{insert_row}", 
             f"=B{insert_row+3}*0.01", 
             f"=B{insert_row+3}*0.018"],
            ["", "", 
             f"=(30*86400*3.125*C{insert_row+3}*1E12)/(C{insert_row}*4294967296)", 
             f"=(30*86400*3.125*D{insert_row+3}*1E12)/(C{insert_row}*4294967296)", 
             ""],
            ["", "", 
             f"=C{insert_row+4}*B{insert_row}", 
             f"=D{insert_row+4}*B{insert_row}", 
             ""]
        ]
        
        # Вставка данных
        range_name = f"A{insert_row}:E{insert_row + len(values) - 1}"
        print(f"Вставляем данные в диапазон: {range_name}")
        
        body = {
            "values": values
        }
        
        result = service.spreadsheets().values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=range_name,
            valueInputOption="USER_ENTERED",
            body=body
        ).execute()
        
        print(f"Обновлено {result.get('updatedCells')} ячеек")
        
        # Отправка уведомления
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
    main()
