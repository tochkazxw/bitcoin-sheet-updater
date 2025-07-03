import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests
from bs4 import BeautifulSoup
import datetime
import json
import os

# Чтение JSON из переменной окружения
with open("credentials.json", "r") as f:
    data = json.load(f)

with open("credentials.json", "w") as f:
    json.dump(data, f)

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)

# Открытие таблицы
spreadsheet_id = "1BUXPs17GrBNAXM0NSgfig3RlJAHNcJlMQ8GvHbK5GpU"
sheet = client.open_by_key(spreadsheet_id).sheet1

# Получение курса биткоина
def get_binance():
    r = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT")
    return float(r.json()["price"])

def get_coindesk():
    r = requests.get("https://api.coindesk.com/v1/bpi/currentprice.json")
    return float(r.json()["bpi"]["USD"]["rate_float"])

btc_prices = [get_binance(), get_coindesk()]
btc_avg = round(sum(btc_prices) / len(btc_prices), 2)

# Сложность и хешрейт
def get_difficulty_and_hashrate():
    r = requests.get("https://bits.media/difficulty/bitcoin/")
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

difficulty, hashrate = get_difficulty_and_hashrate()
today = datetime.date.today().strftime("%d.%m.%Y")

# Запись строки в таблицу
sheet.append_row([today, btc_avg, difficulty, hashrate])
print("Таблица обновлена!")
