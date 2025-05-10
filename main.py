import flet as ft
import pandas as pd

def main(page: ft.Page):
    page.title = "Fishlog Data"
    page.scroll = ft.ScrollMode.AUTO  # Додаємо прокрутку для великих таблиць

    # Поля введення
    base_input = ft.TextField(label="База", value="Всі")
    fish_input = ft.TextField(label="Риба", value="Всі")
    location_input = ft.TextField(label="Локація", value="Всі")
    weight_input = ft.TextField(label="Мін. вага", value="0")

    # Контейнер для таблиць
    tables_container = ft.Column()

    def update_tables(e):
        # Отримуємо значення з полів введення
        my_base = base_input.value if base_input.value.strip() else "Всі"
        my_fish = fish_input.value if fish_input.value.strip() else "Всі"
        my_location = location_input.value if location_input.value.strip() else "Всі"
        try:
            my_weight = float(weight_input.value) if weight_input.value.strip() else 0
        except ValueError:
            my_weight = 0

        # Завантаження даних з файлу
        column_names = ["fish", "weight", "bait", "base", "location", "id", "time", "depth"]
        try:
            base_df = pd.read_csv("Fishlog.txt", sep=":", names=column_names, header=None)
            base_df["time"] = base_df["time"].str.replace("-", ":")
            base_df["time"] = pd.to_datetime(base_df["time"], format="%H:%M")
            base_df["time"] = base_df["time"].dt.strftime("%H:%M")
        except FileNotFoundError:
            tables_container.controls.clear()
            tables_container.controls.append(ft.Text("Помилка: Файл Fishlog.txt не знайдено"))
            page.update()
            return

        # Фільтруємо за базою, рибою, локацією та вагою
        f = base_df.copy()  # Створюємо копію DataFrame
        f = f[f['weight'] > my_weight]  # Фільтрація за вагою
        if my_base not in (None, 'Всі'):
            f = f[f['base'] == my_base]
        if my_fish not in (None, 'Всі'):
            f = f[f['fish'] == my_fish]
        if my_location not in (None, 'Всі'):
            f = f[f['location'] == my_location]

        # Очищаємо попередні таблиці
        tables_container.controls.clear()

        # Перевірка на порожній результат
        if f.empty:
            tables_container.controls.append(ft.Text("Немає даних для заданих критеріїв"))
        else:
            # Групуємо за наживкою
            grouped_base = f.groupby(['bait']).agg(
                mean_weight=('weight', 'mean'),
                max_weight=('weight', 'max'),
                fish_count=('weight', 'size'),
                max_depth=('depth', 'max'),
                min_depth=('depth', 'min'),
            ).sort_values(by='bait', ascending=True)

            # Округлюємо числові стовпці до цілих чисел
            grouped_base['mean_weight'] = grouped_base['mean_weight'].astype(int)
            grouped_base['max_weight'] = grouped_base['max_weight'].astype(int)
            grouped_base['max_depth'] = grouped_base['max_depth'].astype(int)
            grouped_base['min_depth'] = grouped_base['min_depth'].astype(int)

            # Сортуємо f за вагою
            f_sorted = f.sort_values(by='weight', ascending=False)

            # Заголовок
            header = f'Зведення по базі {my_base if my_base not in (None, "Всі") else "всі бази"}, ' \
                     f'рибі {my_fish if my_fish not in (None, "Всі") else "всі риби"}, ' \
                     f'локації {my_location if my_location not in (None, "Всі") else "всі локації"}, ' \
                     f'вага > {my_weight}'
            tables_container.controls.append(ft.Text(header))
            tables_container.controls.append(ft.Text(f'Всього записів: {len(f_sorted)}'))

            # Таблиця для grouped_base
            tables_container.controls.append(ft.Text("Зведена таблиця:"))
            grouped_table = ft.DataTable(
                columns=[
                    ft.DataColumn(ft.Text("Наживка")),
                    ft.DataColumn(ft.Text("Середня вага")),
                    ft.DataColumn(ft.Text("Макс. вага")),
                    ft.DataColumn(ft.Text("Кількість")),
                    ft.DataColumn(ft.Text("Макс. глибина")),
                    ft.DataColumn(ft.Text("Мін. глибина")),
                ],
                rows=[
                    ft.DataRow(cells=[
                        ft.DataCell(ft.Text(str(index))),
                        ft.DataCell(ft.Text(str(row['mean_weight']))),
                        ft.DataCell(ft.Text(str(row['max_weight']))),
                        ft.DataCell(ft.Text(str(row['fish_count']))),
                        ft.DataCell(ft.Text(str(row['max_depth']))),
                        ft.DataCell(ft.Text(str(row['min_depth']))),
                    ])
                    for index, row in grouped_base.iterrows()
                ]
            )
            tables_container.controls.append(grouped_table)

            # Таблиця для f_sorted.head(20)
            tables_container.controls.append(ft.Text("Перші 20 записів (відсортовані за вагою):"))
            sorted_table = ft.DataTable(
                columns=[
                    ft.DataColumn(ft.Text(col)) for col in f_sorted.columns
                ],
                rows=[
                    ft.DataRow(cells=[
                        ft.DataCell(ft.Text(str(value))) for value in row
                    ])
                    for _, row in f_sorted.head(20).iterrows()
                ]
            )
            tables_container.controls.append(sorted_table)

        # Оновлюємо сторінку
        page.update()

    # Кнопка для оновлення таблиць
    update_button = ft.ElevatedButton("Оновити", on_click=update_tables)

    # Додаємо поля введення, кнопку і контейнер для таблиць
    page.add(
        ft.Column([
            base_input,
            fish_input,
            location_input,
            weight_input,
            update_button,
            tables_container
        ])
    )

    # Викликаємо оновлення таблиць при завантаженні сторінки
    update_tables(None)

# Запускаємо додаток у режимі HTML
ft.app(target=main, view=ft.AppView.WEB_BROWSER)