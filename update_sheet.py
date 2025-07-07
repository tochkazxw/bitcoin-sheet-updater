import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests
import datetime

# Авторизация
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)

# Открытие таблицы по ID
spreadsheet_id = "1SjT740pFA7zuZMgBYf5aT0IQCC-cv6pMsQpEXYgQSmU"
sheet = client.open_by_key(spreadsheet_id).sheet1

def get_binance_price():
    r = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT", timeout=10)
    r.raise_for_status()
    data = r.json()
    return float(data["price"])

def get_coindesk_price():
    r = requests.get("https://api.coindesk.com/v1/bpi/currentprice.json", timeout=10)
    r.raise_for_status()
    return float(r.json()["bpi"]["USD"]["rate_float"])

def get_difficulty_and_hashrate():
    try:
        diff = float(requests.get("https://blockchain.info/q/getdifficulty", timeout=10).text)
        hashrate = float(requests.get("https://blockchain.info/q/hashrate", timeout=10).text)
        # Форматируем сложность в экспоненциальной записи
        diff_str = f"{diff:.2E}"
        # Хешрейт — просто число, без преобразований и единиц
        hashrate_str = f"{int(hashrate)}"
        return diff_str, hashrate_str
    except Exception as e:
        print("Ошибка при получении сложности и хешрейта:", e)
        return "N/A", "N/A"

prices = [p for p in [get_binance_price(), get_coindesk_price()] if p is not None]
btc_avg = round(sum(prices) / len(prices), 2) if prices else "N/A"

difficulty, hashrate = get_difficulty_and_hashrate()
today = datetime.date.today().strftime("%d.%m.%Y")

sheet.append_row([today, btc_avg, difficulty, hashrate])

print("✅ Таблица обновлена!")
