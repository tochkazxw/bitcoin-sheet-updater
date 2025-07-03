import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests
from bs4 import BeautifulSoup
import datetime
import json

# Авторизация в Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)

# Открытие таблицы
spreadsheet_id = "1SjT740pFA7zuZMgBYf5aT0IQCC-cv6pMsQpEXYgQSmU"
sheet = client.open_by_key(spreadsheet_id).sheet1

# Получение курса BTC с Binance
def get_binance():
    try:
        r = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT", timeout=10)
        r.raise_for_status()
        data = r.json()
        if "price" in data:
            return float(data["price"])
        else:
            print("Binance вернул неожиданный ответ:", data)
            return None
    except Exception as e:
        print("Ошибка запроса к Binance:", e)
        return None

# Временно отключаем Coindesk, если у тебя проблемы с DNS
def get_coindesk():
    try:
        r = requests.get("https://api.coindesk.com/v1/bpi/currentprice.json", timeout=10)
        r.raise_for_status()
        return float(r.json()["bpi"]["USD"]["rate_float"])
    except Exception as e:
        print("Ошибка запроса к Coindesk:", e)
        return None

# Получение сложности и хешрейта
def get_difficulty_and_hashrate():
    try:
        r = requests.get("https://bits.media/difficulty/bitcoin/", timeout=10)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        rows = soup.find_all("div", class_="coininfo-line")
        difficulty = hashrate = "N/A"
        for row in rows:
            text = row.get_text()
            if "Сложность сети" in text:
                difficulty = row.find_next("div").text.strip()
            if "Хешрейт" in text:
                hashrate = row.find_next("div").text.strip()
        return difficulty, hashrate
    except Exception as e:
        print("Ошибка получения сложности и хешрейта:", e)
        return "N/A", "N/A"

# Получение данных
btc_prices = [price for price in [get_binance(), get_coindesk()] if price is not None]
btc_avg = round(sum(btc_prices) / len(btc_prices), 2) if btc_prices else "N/A"
difficulty, hashrate = get_difficulty_and_hashrate()
today = datetime.date.today().strftime("%d.%m.%Y")

# Запись в таблицу
sheet.append_row([today, btc_avg, difficulty, hashrate])
print("✅ Таблица обновлена!")
