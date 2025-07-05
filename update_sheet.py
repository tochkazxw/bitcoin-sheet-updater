# ... все твои импорты и авторизации ...

def read_last_table():
    all_values = sheet.get_all_values()
    start_indexes = [i for i, row in enumerate(all_values) if row and row[0] == "Дата"]
    if not start_indexes:
        return None
    last_start = start_indexes[-1]
    return all_values[last_start:last_start+10]

def get_miners_from_last_table(last_table):
    if last_table and len(last_table) > 3:
        miners_str = last_table[3][0]
        if miners_str.isdigit():
            return int(miners_str)
    return 1000

def get_value_from_table(last_table, row_idx, col_idx, default):
    try:
        val = last_table[row_idx][col_idx]
        if val.strip() == "":
            return default
        return val
    except:
        return default

try:
    today = get_today_moldova()

    prices = []
    for source_func in [get_coingecko_price, get_coindesk_price]:
        price = source_func()
        if price is not None:
            prices.append(price)
    btc_avg = round(sum(prices)/len(prices), 2) if prices else "N/A"

    difficulty, hashrate = get_difficulty_and_hashrate()

    last_table = read_last_table()

    miners = get_miners_from_last_table(last_table)

    # Можно подставить другие значения из last_table, например, распределения, партнеров и т.д.
    # Ниже пример как взять данные, если нужно:
    # stock_hashrate = 150 * miners
    # attracted_hashrate = int(stock_hashrate * 1.15)

    stock_hashrate = 150 * miners
    attracted_hashrate = int(stock_hashrate * 1.15)
    total_hashrate = stock_hashrate + attracted_hashrate
    attracted_share_percent = round(attracted_hashrate / total_hashrate * 100, 2)

    values = [
        ["Дата", "Средний курс BTC", "Сложность", "Общий хешрейт, Th", "Доля привлеченного хешрейта, %"],
        [today, btc_avg, difficulty, hashrate, attracted_share_percent],

        ["Кол-во майнеров", "Стоковый хешрейт", "Привлечённый хешрейт", "Распределение", "Хешрейт к распределению"],
        [miners, stock_hashrate, attracted_hashrate, 0.028, 4830],

        ["Средний хешрейт на майнер", "Прирост хешрейта", "", "Партнер", "Разработчик"],
        [150, attracted_hashrate - stock_hashrate, "", 0.01, 0.018],

        ["Коэфф. прироста", "Суммарный хешрейт", "", 1725, 3105],
        [0.15, total_hashrate, "Доход за 30 дней, BTC", 0.02573522, 0.04632340],

        ["Полезный хешрейт, Th", total_hashrate - int(total_hashrate * 0.028), "Доход за 30 дней, USDT", 2702.2, 4863.96]
    ]

    last_row = len(sheet.get_all_values())
    start_row = last_row + 2

    for i, row in enumerate(values):
        sheet.insert_row(row, start_row + i)

    send_telegram_message(
        f"✅ Таблица обновлена: {today}\n"
        f"Средний курс BTC: {btc_avg}\n"
        f"Сложность: {difficulty}\n"
        f"Хешрейт: {total_hashrate} Th/s\n"
        f"<a href='https://docs.google.com/spreadsheets/d/1SjT740pFA7zuZMgBYf5aT0IQCC-cv6pMsQpEXYgQSmU/edit'>Ссылка на таблицу</a>"
    )

    print("✅ Обновление таблицы завершено.")

except Exception as e:
    print(f"❌ Ошибка: {e}")
    send_telegram_message(f"❌ Ошибка при обновлении таблицы: {e}")
