import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests
import datetime
import pytz
from google.oauth2 import service_account
from googleapiclient.discovery import build
import os
from decimal import Decimal

# Авторизация
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)
sheet = client.open_by_key("1SjT740pFA7zuZMgBYf5aT0IQCC-cv6pMsQpEXYgQSmU").sheet1

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
credentials = service_account.Credentials.from_service_account_file("credentials.json", scopes=SCOPES)
service = build("sheets", "v4", credentials=credentials)

# Получение sheetId
spreadsheet = service.spreadsheets().get(spreadsheetId=sheet.spreadsheet.id).execute()
sheet_id = next(s["properties"]["sheetId"] for s in spreadsheet["sheets"] if s["properties"]["title"] == sheet.title)

# Telegram
def send_telegram_message(text):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        return
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    try:
        requests.post(url, data=payload, timeout=10)
    except:
        pass

# Дата
def get_today_moldova():
    tz = pytz.timezone('Europe/Chisinau')
    now = datetime.datetime.now(tz)
    return now.strftime("%d.%m.%Y")

# Курс BTC
def get_coindesk_price():
    try:
        r = requests.get("https://api.coindesk.com/v1/bpi/currentprice.json", timeout=10)
        return float(r.json()["bpi"]["USD"]["rate_float"])
    except:
        return None

def get_coingecko_price():
    try:
        r = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd", timeout=10)
        return float(r.json()["bitcoin"]["usd"])
    except:
        return None

# Сложность и хешрейт
def get_difficulty_and_hashrate():
    try:
        difficulty = requests.get("https://blockchain.info/q/getdifficulty", timeout=10).text
        hashrate = float(requests.get("https://blockchain.info/q/hashrate", timeout=10).text)
        return format(Decimal(difficulty), 'f'), str(int(hashrate))
    except:
        return "N/A", "N/A"

# Основные данные
today = get_today_moldova()
prices = [p for p in [get_coindesk_price(), get_coingecko_price()] if p]
btc_avg = round(sum(prices) / len(prices), 2) if prices else "N/A"
difficulty, hashrate = get_difficulty_and_hashrate()

# Стартовая строка
all_rows = sheet.get_all_values()
r = len(all_rows) + 2

# Формулы (корректные и с процентами)
values = [
    ["Дата", "Средний курс BTC", "Сложность", "Общий хешрейт сети, Th", "Доля привлечённого хешрейта, %"],
    [today, btc_avg, difficulty, hashrate, "=4%"],

    ["Кол-во майнеров", "Стоковый хешрейт, Th", "Привлечённый хешрейт, Th", "Распределение", "Хешрейт к распределению"],
    ["1000", "150000", f"=B{r+3}*E{r+1}", "=2,8%", f"=C{r+3}*D{r+3}"],

    ["Средний хеш на майнер", "Прирост хешрейта, Th", "-", "Партнёр", "Разработчик"],
    [f"=B{r+3}/A{r+3}", f"=C{r+3}-B{r+3}", "-", "=1%", "=1,8%"],

    ["Коэфф. прироста", "Суммарный хешрейт, Th", "-", "Партнёр хешрейт", "Разработчик хешрейт"],
    [f"=(B{r+5}-B{r+3})/B{r+3}", f"=B{r+3}+B{r+5}", "-", f"=E{r+3}*D{r+5}", f"=E{r+3}*E{r+5}"],

    ["Полезный хешрейт, Th", "Доход 30 дней,BTC(Партнёр)", "Доход 30 дней,BTC(Разработчик)"],
    [f"=B{r+7}*0,9736", f"=3,125*D{r+7}*1E12/(C{r+1}*2^32)", f"=3,125*E{r+7}*1E12/(C{r+1}*2^32)"],

    ["", "Доход 30 дней,USDT(Партнёр)", "Доход 30 дней,USDT(Разработчик)"],
    ["", f"=B{r+9}*B{r+1}", f"=C{r+9}*B{r+1}"]
]

# Вставка значений
range_str = f"A{r}:E{r + len(values) - 1}"
service.spreadsheets().values().update(
    spreadsheetId=sheet.spreadsheet.id,
    range=range_str,
    valueInputOption="USER_ENTERED",
    body={"values": values}
).execute()

# Применение процентного формата для нужных ячеек
format_request = {
    "requests": [
        {
            "repeatCell": {
                "range": {
                    "sheetId": sheet_id,
                    "startRowIndex": r - 1,
                    "endRowIndex": r - 1 + len(values),
                    "startColumnIndex": 3,
                    "endColumnIndex": 5
                },
                "cell": {
                    "userEnteredFormat": {
                        "numberFormat": {
                            "type": "PERCENT",
                            "pattern": "0.00%"
                        }
                    }
                },
                "fields": "userEnteredFormat.numberFormat"
            }
        }
    ]
}
service.spreadsheets().batchUpdate(spreadsheetId=sheet.spreadsheet.id, body=format_request).execute()

# Telegram
send_telegram_message(
    f"✅ Таблица обновлена: {today}\n"
    f"Средний курс BTC (USD): {btc_avg}\n"
    f"Сложность: {difficulty}\n"
    f"Хешрейт: {hashrate} Th/s\n"
    f"Ссылка: https://docs.google.com/spreadsheets/d/1SjT740pFA7zuZMgBYf5aT0IQCC-cv6pMsQpEXYgQSmU/edit?usp=sharing"
)
