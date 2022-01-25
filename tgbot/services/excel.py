import xlsxwriter
import json


def save_file_xlsx(name: str, data: list[dict]):
    workbook = xlsxwriter.Workbook(name)
    worksheet = workbook.add_worksheet()
    worksheet.set_column("A:A", 30)
    worksheet.set_column("B:B", 50)
    worksheet.set_column("C:C", 25)
    worksheet.set_column("D:D", 30)
    worksheet.write_row(0, 0, ("Слово", "Словоформы", "Кол-во вхождений", "Сумм. частотность"))
    row = 1
    col = 0
    data = sorted(data, key=lambda product: int(product["keys_count_sum"]), reverse=True)
    for elem in data:
        row_data = (
            elem["word"],
            ", ".join(elem["words"]),
            elem["count"],
            elem["keys_count_sum"]
        )
        worksheet.write_row(row, col, row_data)
        row += 1
    workbook.close()
