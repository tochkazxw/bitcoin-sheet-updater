import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests
import datetime
import pytz

# Авторизация в Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)

# Открываем таблицу по ID
spreadsheet_id = "1SjT740pFA7zuZMgBYf5aT0IQCC-cv6pMsQpEXYgQSmU"
sheet = client.open_by_key(spreadsheet_id).sheet1

# Получение цены с Coindesk
def get_coindesk_price():
    try:
        r = requests.get("https://api.coindesk.com/v1/bpi/currentprice.json", timeout=10)
        r.raise_for_status()
        return float(r.json()["bpi"]["USD"]["rate_float"])
    except Exception as e:
        print("Ошибка запроса к Coindesk:", e)
        return None

# Получение цены с CoinGecko
def get_coingecko_price():
    try:
        r = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd", timeout=10)
        r.raise_for_status()
        data = r.json()
        return float(data["bitcoin"]["usd"])
    except Exception as e:
        print("Ошибка запроса к CoinGecko:", e)
        return None

# Получение сложности и хешрейта через blockchain.info API
def get_difficulty_and_hashrate():
    try:
        diff = float(requests.get("https://blockchain.info/q/getdifficulty", timeout=10).text)
        hashrate = float(requests.get("https://blockchain.info/q/hashrate", timeout=10).text)
        diff_str = f"{diff:.2E}"  # экспоненциальная запись
        hashrate_str = f"{int(hashrate)}"  # просто число без единиц
        return diff_str, hashrate_str
    except Exception as e:
        print("Ошибка получения данных с blockchain.info:", e)
        return "N/A", "N/A"

# Дата по Молдове UTC+3
def get_today_moldova():
    tz = pytz.timezone('Europe/Chisinau')
    now = datetime.datetime.now(tz)
    return now.strftime("%d.%m.%Y")

# Получаем цены из доступных источников
prices = [p for p in [get_coindesk_price(), get_coingecko_price()] if p is not None]
if not prices:
    print("Не удалось получить цены BTC ни с одного источника.")
    btc_avg = "N/A"
else:
    btc_avg = round(sum(prices) / len(prices), 2)

difficulty, hashrate = get_difficulty_and_hashrate()
today = get_today_moldova()

sheet.append_row([today, btc_avg, difficulty, hashrate])

print("✅ Таблица обновлена!")
