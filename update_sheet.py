import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests
import datetime
import pytz
from decimal import Decimal
import os
from google.oauth2 import service_account
from googleapiclient.discovery import build

# --- Авторизация ---
scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)
sheet = client.open_by_key("1SjT740pFA7zuZMgBYf5aT0IQCC-cv6pMsQpEXYgQSmU").sheet1

# --- Google Sheets API ---
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
credentials = service_account.Credentials.from_service_account_file("credentials.json", scopes=SCOPES)
service = build("sheets", "v4", credentials=credentials)

# --- Telegram ---
def send_telegram_message(text):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        return
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    try:
        requests.post(url, data=payload, timeout=10)
    except Exception as e:
        print(f"Telegram error: {e}")

# --- Дата ---
def get_today_moldova():
    tz = pytz.timezone('Europe/Chisinau')
    now = datetime.datetime.now(tz)
    return now.strftime("%d.%m.%Y")

# --- Курс BTC ---
def get_btc_price():
    apis = [
        ("CoinDesk", "https://api.coindesk.com/v1/bpi/currentprice.json", lambda r: float(r.json()["bpi"]["USD"]["rate_float"])),
        ("CoinGecko", "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd", lambda r: float(r.json()["bitcoin"]["usd"]))
    ]
    prices = []
    for name, url, parser in apis:
        try:
            r = requests.get(url, timeout=10)
            r.raise_for_status()
            prices.append(parser(r))
        except Exception as e:
            print(f"{name} API error: {e}")
    return round(sum(prices) / len(prices), 2) if prices else None

# --- Сложность и хешрейт ---
def get_difficulty_and_hashrate():
    try:
        difficulty = requests.get("https://blockchain.info/q/getdifficulty", timeout=10).text
        hashrate = float(requests.get("https://blockchain.info/q/hashrate", timeout=10).text)
        return format(Decimal(difficulty), 'f'), str(int(hashrate))
    except Exception as e:
        print(f"Blockchain.info error: {e}")
        return "N/A", "N/A"

# --- Основные данные ---
today = get_today_moldova()
btc_avg = get_btc_price()
difficulty, hashrate = get_difficulty_and_hashrate()

if not btc_avg:
    send_telegram_message("⚠️ Не удалось получить курс BTC!")
    exit(1)

# --- Найти первую свободную строку ---
all_rows = sheet.get_all_values()
r = len(all_rows) + 1

# --- Формулы и данные ---
values = [
    [today, btc_avg, difficulty, hashrate, "=0.028"],
    ["=1000", "=150", f"=A{r+1}*B{r+1}", f"=C{r+2}*0.15", f"=C{r+2}+D{r+2}"],
    [f"=E{r+2}-E{r+2}*E{r}", f"=C{r+2}+D{r+2}", f"=B{r+3}*E{r}", f"=B{r+3}*0.01", f"=B{r+3}*0.018"],
    ["", "", f"=(30*86400*3.125*C{r+3}*1E12)/(C{r}*4294967296)", f"=(30*86400*3.125*D{r+3}*1E12)/(C{r}*4294967296)", ""],
    ["", "", f"=C{r+4}*B{r}", f"=D{r+4}*B{r}", ""]
]

# --- Вставка данных ---
try:
    service.spreadsheets().values().update(
        spreadsheetId=sheet.spreadsheet.id,
        range=f"A{r}:E{r + len(values) - 1}",
        valueInputOption="USER_ENTERED",
        body={"values": values}
    ).execute()

    # Принудительное обновление формул (опционально)
    service.spreadsheets().batchUpdate(
        spreadsheetId=sheet.spreadsheet.id,
        body={"requests": [{"repeatCell": {
            "range": {"sheetId": sheet.id},
            "fields": "userEnteredValue",
        }}]}
    ).execute()

    # Уведомление в Telegram
    send_telegram_message(
        f"✅ Таблица обновлена: {today}\n"
        f"BTC: ${btc_avg}\n"
        f"Сложность: {difficulty}\n"
        f"Хешрейт: {hashrate} Th/s\n"
        f"Ссылка: https://docs.google.com/spreadsheets/d/1SjT740pFA7zuZMgBYf5aT0IQCC-cv6pMsQpEXYgQSmU/edit"
    )
except Exception as e:
    send_telegram_message(f"❌ Ошибка при обновлении таблицы: {e}")
