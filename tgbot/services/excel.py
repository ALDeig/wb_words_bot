import xlsxwriter

from .mpstats import SalesInDay, RequestRow, WordRow


def _create_worksheet(name) -> tuple[xlsxwriter.Workbook, xlsxwriter.Workbook.worksheet_class]:
    workbook = xlsxwriter.Workbook(name)
    worksheet = workbook.add_worksheet()
    worksheet.set_column("A:A", 15)
    worksheet.set_column("B:B", 30)
    worksheet.set_column("C:C", 50)
    worksheet.set_column("D:D", 30)
    worksheet.set_column("E:E", 30)
    return workbook, worksheet


# def save_file_with_words_by_search_query(name: str, data: list[dict]):
#     workbook, worksheet = _create_worksheet(name)
#     worksheet.write_row(0, 0, ("Слово", "Словоформы", "Кол-во вхождений", "Сумм. частотность"))
#     row = 1
#     col = 0
#     data = sorted(data, key=lambda product: int(product["keys_count_sum"]), reverse=True)
#     for elem in data:
#         row_data = (
#             elem["word"],
#             ", ".join(elem["words"]),
#             elem["keys_count_sum"]
#         )
#         worksheet.write_row(row, col, row_data)
#         row += 1
#     workbook.close()


def save_file_with_words_by_scu(name: str, words: list[WordRow]):
    workbook, worksheet = _create_worksheet(name)
    # worksheet.write_row(0, 0, ("Ключевое слово", "Частотность", "Количество результатов"))
    worksheet.write_row(0, 0, ("Номер", "Слово", "Словоформы", "Кол-во вхождений", "Сумм. частотность"))
    # worksheet.write_row(1, 0, (f"Всего слов: {len(words)}", ))
    row = 1
    col = 0
    cnt = 1
    for item in words:
        row_data = (cnt, item.word, item.word_forms, item.count, item.total)
        worksheet.write_row(row, col, row_data)
        row += 1
        cnt += 1
    workbook.close()


def save_file_with_request(name: str, requests: list[RequestRow]):
    workbook, worksheet = _create_worksheet(name)
    worksheet.write_row(0, 0, ("Номер", "Запрос", "Частота"))
    # worksheet.write_row(1, 0, (f"Всего запросов: {len(requests)}", ))
    row = 1
    col = 0
    cnt = 1
    for request in requests:
        row_data = (cnt, request.request, request.count)
        worksheet.write_row(row, col, row_data)
        row += 1
        cnt += 1
    workbook.close()


def save_file_with_sales_by_scu(name: str, sales: list[SalesInDay]):
    workbook, worksheet = _create_worksheet(name)
    worksheet.write_row(0, 0, ("Дата", "Продажи", "Остаток", "Цена со скидкой"))
    row = 1
    col = 0
    for elem in sales:
        row_data = (str(elem.date), elem.sales, elem.balance, elem.price)
        worksheet.write_row(row, col, row_data)
        row += 1
    workbook.close()
