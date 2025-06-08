import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import re

# Налаштування сторінки
st.set_page_config(page_title="Аналіз риболовлі", layout="wide")
st.title("Аналіз риболовлі")

# Віджет для завантаження файлу
st.header("Завантаження даних")
uploaded_file = st.file_uploader("Виберіть файл Fishlog.txt", type=["txt"], help="Завантажте файл Fishlog.txt для аналізу")

# Ініціалізація base_df
base_df = None
max_weights = {}

# Функція для визначення типу наживки
def classify_bait(bait):
    if pd.isna(bait):
        return None
    bait = str(bait).strip()
    if bait.startswith("Circl"):
        return "Вертушки"
    elif bait.startswith("Devon"):
        return "Девони"
    elif bait.startswith("Musca"):
        return "Мушки"
    elif bait.startswith("Pilk"):
        return "Пілкери"
    elif bait.startswith("Pop"):
        return "Попери"
    elif bait.startswith("Tvis"):
        return "Твістери"
    elif bait.startswith("Vib"):
        return "Вібро"
    elif bait.startswith("Vob"):
        return "Воблери"
    elif bait.startswith("Spinner"):
        return "Спінери"
    else:
        return "Всі Біо"

# Обробка завантаженого файлу
if uploaded_file is not None:
    try:
        with st.spinner("Обробка файлу..."):
            # Зчитуємо файл
            base_df = pd.read_csv(uploaded_file, sep=":", names=["fish", "weight", "bait", "base", "location", "id", "time", "depth"], header=None)
            # Обробка стовпця time
            base_df["time"] = base_df["time"].str.replace("-", ":")
            base_df["time"] = pd.to_datetime(base_df["time"], format="%H:%M")
            base_df["time"] = base_df["time"].dt.strftime("%H:%M")
            # Валідація числових стовпців
            base_df['weight'] = pd.to_numeric(base_df['weight'], errors='coerce')
            base_df['depth'] = pd.to_numeric(base_df['depth'], errors='coerce')
            base_df['id'] = pd.to_numeric(base_df['id'], errors='coerce')
            base_df = base_df.dropna(subset=['weight', 'depth', 'id'])
            # Додаємо стовпець із типом наживки
            base_df['bait_type'] = base_df['bait'].apply(classify_bait)
            # Видаляємо записи з невідомими типами наживок
            base_df = base_df[base_df['bait_type'].notna()]
            # Обчислюємо максимальну вагу для кожного виду риби (id ≤ 9999)
            max_weights = base_df[base_df['id'] <= 9999].groupby('fish')['weight'].max().to_dict()
        st.success("Файл успішно завантажено")
    except Exception as e:
        st.error(f"Помилка при читанні файлу: {str(e)}")
        st.stop()
else:
    st.warning("Будь ласка, завантажте файл Fishlog.txt для продовження")
    st.stop()

# Бічна панель для фільтрів
with st.sidebar:
    st.header("Фільтри")
    my_base = st.selectbox("База", ["Всі"] + sorted(base_df["base"].unique().tolist()), help="Виберіть базу або 'Всі'")
    my_fish = st.selectbox("Риба", ["Всі"] + sorted(base_df["fish"].unique().tolist()), help="Виберіть рибу або 'Всі'")
    my_location = st.selectbox("Локація", ["Всі"] + sorted(base_df["location"].unique().tolist()), help="Виберіть локацію або 'Всі'")
    my_bait = st.selectbox("Наживка", ["Всі"] + sorted(base_df["bait"].unique().tolist()), help="Виберіть наживку або 'Всі'")
    my_weight = st.number_input("Мін. вага", value=0.0, step=1.0, help="Введіть мінімальну вагу")
    
    # Перемикач для всіх типів наживок
    if 'select_all_bait_types' not in st.session_state:
        st.session_state.select_all_bait_types = True
    
    select_all = st.checkbox("Вибрати/зняти всі типи наживок", value=st.session_state.select_all_bait_types, key="select_all_bait_types")
    
    # Спойлер для типів наживок
    with st.expander("Типи наживок"):
        bait_types = {
            "Всі Біо": st.checkbox("Всі Біо", value=st.session_state.select_all_bait_types, help="Наживки без специфічних префіксів", key="bait_type_bio"),
            "Вертушки": st.checkbox("Вертушки", value=st.session_state.select_all_bait_types, help="Наживки, що починаються з 'Circl'", key="bait_type_circl"),
            "Девони": st.checkbox("Девони", value=st.session_state.select_all_bait_types, help="Наживки, що починаються з 'Devon'", key="bait_type_devon"),
            "Мушки": st.checkbox("Мушки", value=st.session_state.select_all_bait_types, help="Наживки, що починаються з 'Musca'", key="bait_type_musca"),
            "Пілкери": st.checkbox("Пілкери", value=st.session_state.select_all_bait_types, help="Наживки, що починаються з 'Pilk'", key="bait_type_pilk"),
            "Попери": st.checkbox("Попери", value=st.session_state.select_all_bait_types, help="Наживки, що починаються з 'Pop'", key="bait_type_pop"),
            "Твістери": st.checkbox("Твістери", value=st.session_state.select_all_bait_types, help="Наживки, що починаються з 'Tvis'", key="bait_type_tvis"),
            "Вібро": st.checkbox("Вібро", value=st.session_state.select_all_bait_types, help="Наживки, що починаються з 'Vib'", key="bait_type_vib"),
            "Воблери": st.checkbox("Воблери", value=st.session_state.select_all_bait_types, help="Наживки, що починаються з 'Vob'", key="bait_type_vob"),
            "Спінери": st.checkbox("Спінери", value=st.session_state.select_all_bait_types, help="Наживки, що починаються з 'Spinner'", key="bait_type_spinner")
        }
        
        # Оновлення стану перемикача на основі окремих чекбоксів
        all_selected = all(bait_types.values())
        if all_selected != st.session_state.select_all_bait_types:
            st.session_state.select_all_bait_types = all_selected
    
    group_by = st.selectbox("Групувати за", ["Наживка", "Риба"], help="Виберіть, групувати за наживкою чи рибою")
    top_n_baits = st.number_input("Кількість наживок у графіку", value=10, min_value=1, step=1, help="Виберіть кількість наживок для відображення (топ-N за середньою вагою)")

# Кнопка оновлення в основній частині
if st.button("Оновити"):
    # Фільтрація
    f = base_df.copy()
    f = f[f['weight'] >= my_weight]
    if my_base != 'Всі':
        f = f[f['base'] == my_base]
    if my_fish != 'Всі':
        f = f[f['fish'] == my_fish]
    if my_location != 'Всі':
        f = f[f['location'] == my_location]
    if my_bait != 'Всі':
        f = f[f['bait'] == my_bait]
    
    # Фільтрація за типами наживок
    selected_bait_types = [bait_type for bait_type, selected in bait_types.items() if selected]
    if not selected_bait_types:
        st.error("Виберіть хоча б один тип наживки")
        st.stop()
    f = f[f['bait_type'].isin(selected_bait_types)]

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
            min_depth=('depth', 'min'),
            max_depth=('depth', 'max')
        ).sort_values(by=group_column, ascending=True)

        grouped_base['mean_weight'] = grouped_base['mean_weight'].astype(int)
        grouped_base['max_weight'] = grouped_base['max_weight'].astype(int)
        grouped_base['max_depth'] = grouped_base['max_depth'].astype(int)
        grouped_base['min_depth'] = grouped_base['min_depth'].astype(int)

        f_sorted = f.sort_values(by='weight', ascending=False)

        # Вивід
        header = f'Зведення по базі {my_base if my_base != "Всі" else "всі бази"}, ' \
                 f'рибі {my_fish if my_fish != "Всі" else "всі риби"}, ' \
                 f'локації {my_location if my_location != "Всі" else "всі локації"}, ' \
                 f'наживці {my_bait if my_bait != "Всі" else "всі наживки"}, ' \
                 f'вага >= {my_weight}, типи наживок: {", ".join(selected_bait_types)}'
        st.subheader(header)
        st.write(f"Всього записів: {len(f_sorted)}")

        # Зведена таблиця
        st.write("Зведена таблиця:")
        st.dataframe(grouped_base, use_container_width=True)

        # Всі записи зі стилізацією
        st.write("Усі записи (відсортовані за вагою):")
        
        def style_row(row):
            if row['id'] > 9999:
                return ['color: red'] * len(row)
            if row['fish'] in max_weights and row['weight'] > 0.8 * max_weights[row['fish']]:
                return ['color: blue'] * len(row)
            return [''] * len(row)

        styled_df = f_sorted.style.apply(style_row, axis=1)
        st.dataframe(styled_df, use_container_width=True, height=500)

        # Аналіз по годинах
        try:
            f['hour'] = pd.to_datetime(f['time'], format='%H:%M').dt.hour
            st.subheader("Аналіз по годинах")

            fish_count_per_hour = f.groupby('hour').size()
            st.markdown("**Кількість риб по годинах:**")
            st.bar_chart(fish_count_per_hour, x_label="Година", y_label="Кількість риб")

            sum_weight_per_hour = f.groupby('hour')['weight'].sum()
            st.markdown("**Сумарна вага по годинах:**")
            st.bar_chart(sum_weight_per_hour, x_label="Година", y_label="Сумарна вага (г)")
        except Exception as e:
            st.warning(f"Не вдалося виконати аналіз по годинах: {str(e)}")

        # Гістограма глибини лову
        st.subheader("Аналіз глибини вилову")
        try:
            bins = [0, 20, 250, 500, 1000, np.inf]
            labels = ['0-20', '21-250', '251-500', '501-1000', '1001+']
            f['depth_bin'] = pd.cut(f['depth'], bins=bins, labels=labels, right=False)

            depth_hist = f['depth_bin'].value_counts().reindex(labels, fill_value=0)
            st.markdown("**Розподіл кількості виловів по фіксованих діапазонах глибини (м):**")
            st.bar_chart(depth_hist, x_label="Діапазон глибини (м)", y_label="Кількість виловів")
        except Exception as e:
            st.warning(f"Не вдалося побудувати гістограму глибини: {str(e)}")

        # Графік залежності ваги риби від наживки
        st.subheader("Аналіз ваги риби за наживкою")
        try:
            bait_stats = f.groupby('bait').agg(
                mean_weight=('weight', 'mean'),
                fish_count=('fish', 'count')
            ).reset_index()
            bait_stats = bait_stats.sort_values(by='mean_weight', ascending=False).head(top_n_baits)
            fig = px.bar(
                bait_stats,
                y='bait',
                x='mean_weight',
                title=f"Середня вага риби для топ-{top_n_baits} наживок (кількість риб у підписах)",
                labels={'bait': 'Наживка', 'mean_weight': 'Середня вага (г)'},
                orientation='h',
                text=bait_stats['fish_count'].apply(lambda x: f"{x} риб")
            )
            fig.update_traces(textposition='auto')
            fig.update_layout(height=200 + top_n_baits * 30, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.warning(f"Не вдалося побудувати графік ваги за наживкою: {str(e)}")
