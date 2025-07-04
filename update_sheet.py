import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests
import datetime
import pytz
from google.oauth2 import service_account
from googleapiclient.discovery import build
from decimal import Decimal
import os

# Авторизация
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)
sheet = client.open_by_key("1SjT740pFA7zuZMgBYf5aT0IQCC-cv6pMsQpEXYgQSmU").sheet1

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
credentials = service_account.Credentials.from_service_account_file("credentials.json", scopes=SCOPES)
service = build("sheets", "v4", credentials=credentials)

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

# Получение строки начала нового блока
all_rows = sheet.get_all_values()
start_row = len(all_rows) + 2
r = start_row

# Получение данных
today = get_today_moldova()
prices = [p for p in [get_coindesk_price(), get_coingecko_price()] if p]
btc_avg = round(sum(prices) / len(prices), 2) if prices else "N/A"
difficulty, hashrate = get_difficulty_and_hashrate()
share_attracted = 0.04
distribution = "2.80%"
partner_share = "1.00%"
developer_share = "1.80%"

# Табличный шаблон
block = [
    ["Дата", "Средний курс BTC", "Сложность", "Общий хешрейт сети, Th", "Доля привлечённого хешрейта, %"],
    [today, btc_avg, difficulty, hashrate, share_attracted],
    [],
    ["Кол-во майнеров", "Стоковый хешрейт, Th", "Привлечённый хешрейт, Th", "Распределение", "Хешрейт к распределению"],
    ["1000", "150000", "", distribution, ""],
    [],
    ["Средний хеш на майнер", "Прирост хешрейта, Th", "-", "Партнёр", "Разработчик"],
    ["150", "22500", "-", partner_share, developer_share],
    [],
    ["Коэфф. прироста", "Суммарный хешрейт, Th", "-", "Партнёр хешрейт", "Разработчик хешрейт"],
    ["15%", "", "-", "", ""],
    [],
    ["Полезный хешрейт, Th", "Доход 30 дней,BTC(Партнёр)", "Доход 30 дней,BTC(Разработчик)"],
    ["", "", ""],
    ["", "Доход 30 дней,USDT(Партнёр)", "Доход 30 дней,USDT(Разработчик)"],
    ["", "", ""],
]

# Вставка строк
for i, row in enumerate(block):
    sheet.insert_row(row, index=start_row + i)

# Вставка формул
sheet.update_acell(f"C{r+4}", f"=B{r+4}+B{r+6}")  # привлечённый хешрейт
sheet.update_acell(f"E{r+4}", f"=C{r+4}*D{r+4}")  # хешрейт к распределению
sheet.update_acell(f"B{r+10}", f"=C{r+4}")        # суммарный хешрейт
sheet.update_acell(f"D{r+10}", f"=E{r+4}*D{r+8}")  # хеш партнёр
sheet.update_acell(f"E{r+10}", f"=E{r+4}*E{r+8}")  # хеш разработчик
sheet.update_acell(f"A{r+13}", f"=B{r+10}*0.9736")  # полезный хешрейт
sheet.update_acell(f"B{r+13}", f"=(30*86400*3.125*D{r+10}*1000000000000)/(C{r+1}*4294967296)")  # BTC партнёр
sheet.update_acell(f"C{r+13}", f"=(30*86400*3.125*E{r+10}*1000000000000)/(C{r+1}*4294967296)")  # BTC разработчик
sheet.update_acell(f"B{r+15}", f"=B{r+13}*B{r+1}")  # USDT партнёр
sheet.update_acell(f"C{r+15}", f"=C{r+13}*B{r+1}")  # USDT разработчик

# Telegram
send_telegram_message(
    f"✅ Таблица обновлена: {today}\n"
    f"Средний курс BTC (USD): {btc_avg}\n"
    f"Сложность: {difficulty}\n"
    f"Хешрейт: {hashrate} Th/s\n"
    f"Ссылка: https://docs.google.com/spreadsheets/d/1SjT740pFA7zuZMgBYf5aT0IQCC-cv6pMsQpEXYgQSmU/edit?usp=sharing"
)
