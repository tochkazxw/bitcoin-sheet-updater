# Заголовки для заголовочной строки
headers = ["Параметры сети", "Курс", "Сложность", "Общий хешрейт сети, Th"]
# Подписи над значениями (можно дублировать заголовки или конкретные пояснения)
labels = ["Дата", "Средний курс BTC (USD)", "Сложность сети", "Хешрейт сети (Th/s)"]
# Значения
data_row = [today, str(btc_avg), difficulty, hashrate]

# Добавляем строки
sheet.append_row(headers)
sheet.append_row(labels)
sheet.append_row(data_row)

# Общее количество строк
row_count = len(sheet.get_all_values())
start_header = row_count - 3  # Заголовки
start_labels = row_count - 2  # Подписи
start_data = row_count - 1    # Значения

# Запрос для форматирования
requests_body = {
    "requests": [
        # Форматируем заголовок — фон синий, текст белый и жирный
        {
            "repeatCell": {
                "range": {
                    "sheetId": sheet_id,
                    "startRowIndex": start_header,
                    "endRowIndex": start_header + 1,
                    "startColumnIndex": 0,
                    "endColumnIndex": 4
                },
                "cell": {
                    "userEnteredFormat": {
                        "backgroundColor": {"red": 0.2, "green": 0.4, "blue": 0.8},
                        "textFormat": {"foregroundColor": {"red": 1, "green": 1, "blue": 1}, "bold": True}
                    }
                },
                "fields": "userEnteredFormat(backgroundColor,textFormat)"
            }
        },
        # Форматируем подписи — фон светло-серый, текст черный, жирный
        {
            "repeatCell": {
                "range": {
                    "sheetId": sheet_id,
                    "startRowIndex": start_labels,
                    "endRowIndex": start_labels + 1,
                    "startColumnIndex": 0,
                    "endColumnIndex": 4
                },
                "cell": {
                    "userEnteredFormat": {
                        "backgroundColor": {"red": 0.9, "green": 0.9, "blue": 0.9},
                        "textFormat": {"foregroundColor": {"red": 0, "green": 0, "blue": 0}, "bold": True}
                    }
                },
                "fields": "userEnteredFormat(backgroundColor,textFormat)"
            }
        },
        # Форматируем данные — фон белый, текст черный
        {
            "repeatCell": {
                "range": {
                    "sheetId": sheet_id,
                    "startRowIndex": start_data,
                    "endRowIndex": start_data + 1,
                    "startColumnIndex": 0,
                    "endColumnIndex": 4
                },
                "cell": {
                    "userEnteredFormat": {
                        "backgroundColor": {"red": 1, "green": 1, "blue": 1},
                        "textFormat": {"foregroundColor": {"red": 0, "green": 0, "blue": 0}}
                    }
                },
                "fields": "userEnteredFormat(backgroundColor,textFormat)"
            }
        },
        # Границы для всех строк
        {
            "updateBorders": {
                "range": {
                    "sheetId": sheet_id,
                    "startRowIndex": start_header,
                    "endRowIndex": start_data + 1,
                    "startColumnIndex": 0,
                    "endColumnIndex": 4
                },
                "top": {"style": "SOLID", "width": 1, "color": {"red": 0, "green": 0, "blue": 0}},
                "bottom": {"style": "SOLID", "width": 1, "color": {"red": 0, "green": 0, "blue": 0}},
                "left": {"style": "SOLID", "width": 1, "color": {"red": 0, "green": 0, "blue": 0}},
                "right": {"style": "SOLID", "width": 1, "color": {"red": 0, "green": 0, "blue": 0}},
                "innerHorizontal": {"style": "SOLID", "width": 1, "color": {"red": 0, "green": 0, "blue": 0}},
                "innerVertical": {"style": "SOLID", "width": 1, "color": {"red": 0, "green": 0, "blue": 0}}
            }
        }
    ]
}

# Отправляем запрос
service.spreadsheets().batchUpdate(spreadsheetId="1SjT740pFA7zuZMgBYf5aT0IQCC-cv6pMsQpEXYgQSmU", body=requests_body).execute()
print(f"✅ Данные за {today} добавлены и оформлены с подписями.")
