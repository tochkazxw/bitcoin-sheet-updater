import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests
import datetime
import pytz

# Авторизация
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)
spreadsheet_id = "1SjT740pFA7zuZMgBYf5aT0IQCC-cv6pMsQpEXYgQSmU"
sheet = client.open_by_key(spreadsheet_id).sheet1

# Функции получения данных
def get_coindesk_price():
    try:
        r = requests.get("https://api.coindesk.com/v1/bpi/currentprice.json", timeout=10)
        r.raise_for_status()
        return float(r.json()["bpi"]["USD"]["rate_float"])
    except Exception as e:
        print("Ошибка запроса к Coindesk:", e)
        return None

def get_coingecko_price():
    try:
        r = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd", timeout=10)
        r.raise_for_status()
        data = r.json()
        return float(data["bitcoin"]["usd"])
    except Exception as e:
        print("Ошибка запроса к CoinGecko:", e)
        return None

def get_difficulty_and_hashrate():
    try:
        diff = float(requests.get("https://blockchain.info/q/getdifficulty", timeout=10).text)
        hashrate = float(requests.get("https://blockchain.info/q/hashrate", timeout=10).text)
        diff_str = f"{diff:.2E}"
        hashrate_str = f"{int(hashrate)}"
        return diff_str, hashrate_str
    except Exception as e:
        print("Ошибка получения сложности и хешрейта:", e)
        return "N/A", "N/A"

def get_today_moldova():
    tz = pytz.timezone('Europe/Chisinau')
    now = datetime.datetime.now(tz)
    return now.strftime("%d.%m.%Y")

headers = ["Дата", "Средний курс BTC", "Сложность сети", "Хешрейт сети"]

# Проверяем, есть ли данные в таблице, если нет — добавляем заголовки
rows = sheet.get_all_values()
if len(rows) == 0:
    sheet.append_row(headers)
    print("Добавлены заголовки")

prices = [p for p in [get_coindesk_price(), get_coingecko_price()] if p is not None]
if not prices:
    print("Не удалось получить цены BTC ни с одного источника.")
    btc_avg = "N/A"
else:
    btc_avg = round(sum(prices) / len(prices), 2)

difficulty, hashrate = get_difficulty_and_hashrate()
today = get_today_moldova()

sheet.append_row([today, str(btc_avg), difficulty, hashrate])
print("✅ Таблица обновлена!")

# Добавляем рамки на всю таблицу
spreadsheet = client.open_by_key(spreadsheet_id)
worksheet_id = sheet._properties['sheetId']

all_values = sheet.get_all_values()
row_count = len(all_values)
col_count = len(headers)

border_request = {
    "requests": [
        {
            "updateBorders": {
                "range": {
                    "sheetId": worksheet_id,
                    "startRowIndex": 0,
                    "endRowIndex": row_count,
                    "startColumnIndex": 0,
                    "endColumnIndex": col_count
                },
                "top":    {"style": "SOLID", "width": 1, "color": {"red": 0, "green": 0, "blue": 0}},
                "bottom": {"style": "SOLID", "width": 1, "color": {"red": 0, "green": 0, "blue": 0}},
                "left":   {"style": "SOLID", "width": 1, "color": {"red": 0, "green": 0, "blue": 0}},
                "right":  {"style": "SOLID", "width": 1, "color": {"red": 0, "green": 0, "blue": 0}},
                "innerHorizontal": {"style": "SOLID", "width": 1, "color": {"red": 0, "green": 0, "blue": 0}},
                "innerVertical":   {"style": "SOLID", "width": 1, "color": {"red": 0, "green": 0, "blue": 0}}
            }
        }
    ]
}

spreadsheet.batch_update(border_request)
print("✅ Рамки добавлены ко всей таблице!")
