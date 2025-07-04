# ... [весь код выше остаётся без изменений до блока rows]

# --- Формируем данные для таблицы ---
rows = [
    ["Дата", "Средний курс BTC", "Сложность", "Общий хешрейт сети, Th", "Доля привлечённого хешрейта, %"],
    [today, str(btc_avg), difficulty, hashrate, str(attracted_percent)],

    ["Кол-во майнеров", "Стоковый хешрейт, Th", "Привлечённый хешрейт, Th", "Распределение", "Хешрейт к распределению"],
    [num_miners, stock_hashrate, attracted_hashrate, distribution, hashrate_distribution_ratio],

    ["Средний хеш на майнер", "Прирост хешрейта, Th", "-", "Партнёр", "Разработчик"],
    [avg_hashrate_per_miner, hashrate_growth, "-", partner_share, developer_share],

    ["Коэфф. прироста", "Суммарный хешрейт, Th", "-", "Партнёр хешрейт", "Разработчик хешрейт"],
    [growth_coefficient, total_hashrate, "-", partner_hashrate, developer_hashrate],

    ["Полезный хешрейт, Th", useful_hashrate],
    ["Доход за 30 дней, BTC (Партнёр)", partner_earnings_btc],
    ["Доход за 30 дней, BTC (Разработчик)", developer_earnings_btc],
    ["Доход за 30 дней, USDT (Партнёр)", partner_earnings_usdt],
    ["Доход за 30 дней, USDT (Разработчик)", developer_earnings_usdt]
]

# --- Записываем в Google Sheet ---
for row in rows:
    sheet.append_row([str(cell) for cell in row])

# --- Уведомление в Telegram ---
send_telegram_message(
    f"✅ Таблица обновлена: {today}\n"
    f"Средний курс BTC (USD): {btc_avg}\n"
    f"Сложность: {difficulty}\n"
    f"Общий хешрейт: {hashrate}\n"
    f"Доля привлечённого хешрейта: {attracted_percent}%\n"
    f"Ссылка на таблицу: https://docs.google.com/spreadsheets/d/1SjT740pFA7zuZMgBYf5aT0IQCC-cv6pMsQpEXYgQSmU/edit?usp=sharing"
)
