import streamlit as st
import pandas as pd
import numpy as np
import os
import plotly.express as px

# Налаштування сторінки
st.set_page_config(page_title="Аналіз риболовлі", layout="wide")
st.title("Аналіз риболовлі")

# Завантаження даних
column_names = ["fish", "weight", "bait", "base", "location", "id", "time", "depth"]
file_path = "/workspaces/codespaces-blank/Fishlog.txt"

# Перевірка наявності файлу
if not os.path.exists(file_path):
    st.error(f"Помилка: Файл {file_path} не знайдено")
    st.stop()

try:
    base_df = pd.read_csv(file_path, sep=":", names=column_names, header=None)
    base_df["time"] = base_df["time"].str.replace("-", ":")
    base_df["time"] = pd.to_datetime(base_df["time"], format="%H:%M")
    base_df["time"] = base_df["time"].dt.strftime("%H:%M")
except Exception as e:
    st.error(f"Помилка при читанні файлу: {str(e)}")
    st.stop()

# Бічна панель для фільтрів
with st.sidebar:
    st.header("Фільтри")
    my_base = st.selectbox("База", ["Всі"] + sorted(base_df["base"].unique().tolist()), help="Виберіть базу або 'Всі'")
    my_fish = st.selectbox("Риба", ["Всі"] + sorted(base_df["fish"].unique().tolist()), help="Виберіть рибу або 'Всі'")
    my_location = st.selectbox("Локація", ["Всі"] + sorted(base_df["location"].unique().tolist()), help="Виберіть локацію або 'Всі'")
    my_bait = st.selectbox("Наживка", ["Всі"] + sorted(base_df["bait"].unique().tolist()), help="Виберіть наживку або 'Всі'")
    my_weight = st.number_input("Мін. вага", value=0.0, step=1.0, help="Введіть мінімальну вагу")
    group_by = st.selectbox("Групувати за", ["Наживка", "Риба"], help="Виберіть, групувати за наживкою чи рибою")
    top_n_baits = st.number_input("Кількість наживок у графіку", value=10, min_value=1, step=1, help="Виберіть кількість наживок для відображення (топ-N за середньою вагою)")

# Кнопка оновлення в основній частині
if st.button("Оновити"):
    # Фільтрація
    f = base_df.copy()
    f = f[f['weight'] > my_weight]
    if my_base not in (None, 'Всі'):
        f = f[f['base'] == my_base]
    if my_fish not in (None, 'Всі'):
        f = f[f['fish'] == my_fish]
    if my_location not in (None, 'Всі'):
        f = f[f['location'] == my_location]
    if my_bait not in (None, 'Всі'):
        f = f[f['bait'] == my_bait]

    # Вивід результатів
    if f.empty:
        st.warning("Немає даних для заданих критеріїв")
    else:
        # Групування
        group_column = 'bait' if group_by == "Наживка" else 'fish'
        grouped_base = f.groupby([group_column]).agg(
            mean_weight=('weight', 'mean'),
            max_weight=('weight', 'max'),
            fish_count=('weight', 'size'),
            max_depth=('depth', 'max'),
            min_depth=('depth', 'min'),
        ).sort_values(by=group_column, ascending=True)

        grouped_base['mean_weight'] = grouped_base['mean_weight'].astype(int)
        grouped_base['max_weight'] = grouped_base['max_weight'].astype(int)
        grouped_base['max_depth'] = grouped_base['max_depth'].astype(int)
        grouped_base['min_depth'] = grouped_base['min_depth'].astype(int)

        f_sorted = f.sort_values(by='weight', ascending=False)

        # Вивід
        header = f'Зведення по базі {my_base if my_base not in (None, "Всі") else "всі бази"}, ' \
                 f'рибі {my_fish if my_fish not in (None, "Всі") else "всі риби"}, ' \
                 f'локації {my_location if my_location not in (None, "Всі") else "всі локації"}, ' \
                 f'наживці {my_bait if my_bait not in (None, "Всі") else "всі наживки"}, ' \
                 f'вага > {my_weight}'
        st.subheader(header)
        st.write(f"Всього записів: {len(f_sorted)}")

        # Зведена таблиця
        st.write("Зведена таблиця:")
        st.dataframe(grouped_base, use_container_width=True)

        # Перші 20 записів зі стилізацією
        st.write("Перші 20 записів (відсортовані за вагою):")
        
        # Функція стилізації для цілого рядка
        def style_row(row):
            if row['id'] > 9999:
                return ['color: red'] * len(row)
            return [''] * len(row)

        # Застосовуємо стилізацію до всіх стовпців
        styled_df = f_sorted.head(20).style.apply(style_row, axis=1)
        st.dataframe(styled_df, use_container_width=True)

        # Аналіз по годинах
        try:
            # Витягуємо годину з time (уже у форматі рядка HH:MM)
            f["hour"] = pd.to_datetime(f["time"], format="%H:%M").dt.hour

            st.subheader("Аналіз по годинах")

            # Кількість риб по годинах
            fish_count_per_hour = f.groupby("hour")["fish"].count()
            st.markdown("**Кількість риб по годинах:**")
            st.bar_chart(fish_count_per_hour, x_label="Година", y_label="Кількість риб")

            # Сумарна вага по годинах
            sum_weight_per_hour = f.groupby("hour")["weight"].sum()
            st.markdown("**Сумарна вага по годинах:**")
            st.bar_chart(sum_weight_per_hour, x_label="Година", y_label="Сумарна вага (г)")
        except Exception as e:
            st.warning(f"Не вдалося виконати аналіз по годинах: {str(e)}")

        # Гістограма глибини лову з бінуванням
        st.subheader("Аналіз глибини вилову")
        try:
            # Створення фіксованих діапазонів
            bins = [0, 20, 250, 500, 1000, np.inf]
            labels = ['0-20', '21-250', '251-500', '501-1000', '1001+']
            f["depth_bin"] = pd.cut(f["depth"], bins=bins, labels=labels, right=False)

            # Підрахунок кількості записів у кожному біні
            depth_hist = f["depth_bin"].value_counts().sort_index()

            # Виведення гістограми
            st.markdown("**Розподіл кількості виловів по фіксованих діапазонах глибини (м):**")
            st.bar_chart(depth_hist, x_label="Діапазон глибини (м)", y_label="Кількість виловів")
        except Exception as e:
            st.warning(f"Не вдалося побудувати гістограму глибини: {str(e)}")

        # Графік залежності ваги риби від наживки
        st.subheader("Аналіз ваги риби за наживкою")
        try:
            # Групування за наживкою для середньої ваги та кількості риб
            bait_stats = f.groupby("bait").agg(
                mean_weight=("weight", "mean"),
                fish_count=("fish", "count")
            ).reset_index()
            # Сортуємо за середньою вагою і беремо топ-N наживок
            bait_stats = bait_stats.sort_values(by="mean_weight", ascending=False).head(top_n_baits)
            # Створюємо горизонтальну стовпчикову діаграму
            fig = px.bar(bait_stats, y="bait", x="mean_weight", 
                         title=f"Середня вага риби для топ-{top_n_baits} наживок (кількість риб у підписах)",
                         labels={"bait": "Наживка", "mean_weight": "Середня вага (г)"},
                         orientation='h',
                         text=bait_stats["fish_count"].apply(lambda x: f"{x} риб"))
            # Налаштування тексту та висоти графіку
            fig.update_traces(textposition="auto")
            fig.update_layout(height=200 + top_n_baits * 30, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.warning(f"Не вдалося побудувати графік ваги за наживкою: {str(e)}")