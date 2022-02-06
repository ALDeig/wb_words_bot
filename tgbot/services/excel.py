import xlsxwriter

from .mpstats import WORD_ROW, SALES_IN_DAY


def _create_worksheet(name) -> tuple[xlsxwriter.Workbook, xlsxwriter.Workbook.worksheet_class]:
    workbook = xlsxwriter.Workbook(name)
    worksheet = workbook.add_worksheet()
    worksheet.set_column("A:A", 30)
    worksheet.set_column("B:B", 50)
    worksheet.set_column("C:C", 30)
    return workbook, worksheet


def save_file_with_words_by_search_query(name: str, data: list[dict]):
    workbook, worksheet = _create_worksheet(name)
    worksheet.write_row(0, 0, ("Слово", "Словоформы", "Сумм. частотность"))
    row = 1
    col = 0
    data = sorted(data, key=lambda product: int(product["keys_count_sum"]), reverse=True)
    for elem in data:
        row_data = (
            elem["word"],
            ", ".join(elem["words"]),
            elem["keys_count_sum"]
        )
        worksheet.write_row(row, col, row_data)
        row += 1
    workbook.close()


def save_file_with_words_by_scu(name: str, words: list[WORD_ROW]):
    workbook, worksheet = _create_worksheet(name)
    worksheet.write_row(0, 0, ("Ключевое слово", "Частотность", "Количество результатов"))
    row = 1
    col = 0
    for elem in words:
        row_data = (elem.word, elem.count, elem.total)
        worksheet.write_row(row, col, row_data)
        row += 1
    workbook.close()


def save_file_with_sales_by_scu(name: str, sales: list[SALES_IN_DAY]):
    workbook, worksheet = _create_worksheet(name)
    worksheet.write_row(0, 0, ("Дата", "Продажи", "Остаток", "Цена со скидкой"))
    row = 1
    col = 0
    for elem in sales:
        row_data = (elem.day, elem.sales, elem.balance, elem.price)
        worksheet.write_row(row, col, row_data)
        row += 1
    workbook.close()
