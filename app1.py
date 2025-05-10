import streamlit as st
import pandas as pd

st.title("Fishlog Data")

# Поля введення
my_base = st.text_input("База", value="Всі")
my_fish = st.text_input("Риба", value="Всі")
my_location = st.text_input("Локація", value="Всі")
my_weight = st.number_input("Мін. вага", value=0.0, step=1.0)

# Кнопка оновлення
if st.button("Оновити"):
    # Завантаження даних
    column_names = ["fish", "weight", "bait", "base", "location", "id", "time", "depth"]
    try:
        base_df = pd.read_csv("Fishlog.txt", sep=":", names=column_names, header=None)
        base_df["time"] = base_df["time"].str.replace("-", ":")
        base_df["time"] = pd.to_datetime(base_df["time"], format="%H:%M")
        base_df["time"] = base_df["time"].dt.strftime("%H:%M")
    except FileNotFoundError:
        st.error("Помилка: Файл Fishlog.txt не знайдено")
        st.stop()

    # Фільтрація
    f = base_df.copy()
    f = f[f['weight'] > my_weight]
    if my_base not in (None, 'Всі'):
        f = f[f['base'] == my_base]
    if my_fish not in (None, 'Всі'):
        f = f[f['fish'] == my_fish]
    if my_location not in (None, 'Всі'):
        f = f[f['location'] == my_location]

    if f.empty:
        st.write("Немає даних для заданих критеріїв")
    else:
        # Групування
        grouped_base = f.groupby(['bait']).agg(
            mean_weight=('weight', 'mean'),
            max_weight=('weight', 'max'),
            fish_count=('weight', 'size'),
            max_depth=('depth', 'max'),
            min_depth=('depth', 'min'),
        ).sort_values(by='bait', ascending=True)

        grouped_base['mean_weight'] = grouped_base['mean_weight'].astype(int)
        grouped_base['max_weight'] = grouped_base['max_weight'].astype(int)
        grouped_base['max_depth'] = grouped_base['max_depth'].astype(int)
        grouped_base['min_depth'] = grouped_base['min_depth'].astype(int)

        f_sorted = f.sort_values(by='weight', ascending=False)

        # Вивід
        header = f'Зведення по базі {my_base if my_base not in (None, "Всі") else "всі бази"}, ' \
                 f'рибі {my_fish if my_fish not in (None, "Всі") else "всі риби"}, ' \
                 f'локації {my_location if my_location not in (None, "Всі") else "всі локації"}, ' \
                 f'вага > {my_weight}'
        st.write(header)
        st.write(f"Всього записів: {len(f_sorted)}")
        st.write("Зведена таблиця:")
        st.dataframe(grouped_base)
        st.write("Перші 20 записів (відсортовані за вагою):")
        st.dataframe(f_sorted.head(20))
