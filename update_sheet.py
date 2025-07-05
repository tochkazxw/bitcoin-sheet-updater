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
        creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTS_FILE, scope)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(SPREADSHEET_ID).sheet1
        
        SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
        credentials = service_account.Credentials.from_service_account_file(
            CREDENTS_FILE, scopes=SCOPES)
        service = build("sheets", "v4", credentials=credentials)
        
        return sheet, service
    except Exception as e:
        print(f"Ошибка инициализации Google Sheets: {e}")
        raise

# --- Получение данных ---
def get_current_date():
    tz = pytz.timezone('Europe/Chisinau')
    return datetime.datetime.now(tz).strftime("%d.%m.%Y")

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
        difficulty = requests.get("https://blockchain.info/q/getdifficulty", timeout=10).text
        hashrate = float(requests.get("https://blockchain.info/q/hashrate", timeout=10).text)
        return format(Decimal(difficulty), 'f'), str(int(hashrate))
    except Exception as e:
        print(f"Ошибка при получении сложности и хешрейта: {e}")
        return "N/A", "N/A"

# --- Основная функция ---
def update_spreadsheet():
    try:
        sheet, service = init_google_sheets()
        
        # Получаем данные
        today = get_current_date()
        btc_price = get_btc_price() or 0  # Запасное значение
        difficulty, hashrate = get_difficulty_and_hashrate()
        
        # Очищаем лист перед вставкой новых данных
        sheet.clear()
        
        # Подготавливаем данные с заголовками
        headers = ["Дата", "Курс BTC", "Сложность", "Хешрейт сети, Th/s", "Распределение %"]
        data = [
            [today, btc_price, difficulty, hashrate, "=0.028"],
            ["=1000", "=150", "=A2*B2", "=C2*0.15", "=C2+D2"],
            ["=E2-E2*E1", "=C2+D2", "=B3*E1", "=B3*0.01", "=B3*0.018"],
            ["", "", "=(30*86400*3.125*C3*1E12)/(C1*4294967296)", 
             "=(30*86400*3.125*D3*1E12)/(C1*4294967296)", ""],
            ["", "", "=C4*B1", "=D4*B1", ""]
        ]
        values = [headers] + data
        
        # Вставляем данные
        service.spreadsheets().values().update(
            spreadsheetId=SPREADSHEET_ID,
            range="A1:E5",  # Фиксированный диапазон для первых 5 строк
            valueInputOption="USER_ENTERED",
            body={"values": values}
        ).execute()
        
        print("Данные успешно обновлены!")
        
    except Exception as e:
        print(f"Критическая ошибка: {e}")
        raise

if __name__ == "__main__":
    update_spreadsheet()
