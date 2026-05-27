import streamlit as st
from streamlit_autorefresh import st_autorefresh
from time_utils import to_minutes, to_time, now_minutes_japan
from ui_helpers import status_mark
from state import init_session_state

from settings import (
    cast_names,
    table_options,
    cast_options,
    manual_cast_options,
    hour_options,
    minute_options,
    start_time_options,
    rotation_time,
)

from logic import (
    customer_set_time,
    customer_end_time,
    remaining_minutes,
    get_return_cast,
    is_return_time,
    create_schedule,
    find_manual_conflicts,
)

st.set_page_config(layout="wide")
#st_autorefresh(interval=60000, key="auto_refresh")


st.title("付け回し簡易シミュレーター Ver24 統合安定版")
st.caption("延長・手動付け替え・重複警告・10分前戻し・毎分自動再計算")

init_session_state(st)

now_minutes = now_minutes_japan()

st.success(f"現在時刻：{to_time(now_minutes)} / 1分ごとに自動更新・再計算")

casts = []

with st.expander("キャスト設定", expanded=False):
    selected_casts = st.multiselect(
        "出勤キャスト",
        cast_names,
        default=["A", "B", "C", "D"]
    )

    if selected_casts:
        cols = st.columns(min(len(selected_casts), 8))

        for i, cast in enumerate(selected_casts):
            with cols[i % min(len(selected_casts), 8)]:
                selected_time = st.selectbox(
                    f"{cast} 出勤時刻",
                    start_time_options,
                    index=start_time_options.index("18:00"),
                    key=f"cast_start_{cast}"
                )

                h, m = map(int, selected_time.split(":"))
                casts.append({"name": cast, "start": to_minutes(h, m)})

if st.session_state.customers and casts:
    st.session_state.planned_schedule = create_schedule(
    casts,
    st.session_state.customers,
    st.session_state.actual_assignments,
    rotation_time,
)

current_by_table = {}

for item in st.session_state.planned_schedule:
    start = item["開始"]
    end = start + rotation_time

    if start <= now_minutes < end:
        current_by_table[item["卓"]] = item

st.subheader(f"{st.session_state.selected_table} 操作")

selected_customer = st.session_state.customers.get(st.session_state.selected_table)

if selected_customer is not None:
    remain = remaining_minutes(selected_customer, now_minutes)

    if remain <= 0:
        selected_customer = None

if selected_customer is None:
    default_hour = 18
    default_minute = 0
    default_honshimei = "なし"
    default_jounai = "なし"
    current_set_time = 60
else:
    default_hour = selected_customer["start"] // 60
    default_minute = selected_customer["start"] % 60
    default_honshimei = selected_customer["honshimei_cast"]
    default_jounai = selected_customer["jounai_cast"]
    current_set_time = customer_set_time(selected_customer)

op1, op2, op3, op4, op5, op6 = st.columns([1, 1, 1, 1, 1, 1])

with op1:
    visit_hour = st.selectbox(
        "来店 時",
        hour_options,
        index=default_hour % 24,
        key=f"hour_{st.session_state.selected_table}"
    )

with op2:
    visit_minute = st.selectbox(
        "来店 分",
        minute_options,
        index=default_minute,
        key=f"minute_{st.session_state.selected_table}"
    )

with op3:
    honshimei = st.selectbox(
        "本指名",
        cast_options,
        index=cast_options.index(default_honshimei),
        key=f"honshimei_{st.session_state.selected_table}"
    )

with op4:
    jounai = st.selectbox(
        "場内指名",
        cast_options,
        index=cast_options.index(default_jounai),
        key=f"jounai_{st.session_state.selected_table}"
    )

with op5:
    st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
    if st.button("登録 / 更新", use_container_width=True):

        start = to_minutes(visit_hour, visit_minute)

        st.session_state.customers[st.session_state.selected_table] = {
            "table": st.session_state.selected_table,
            "start": start,
            "start_text": to_time(start),
            "honshimei_cast": honshimei,
            "jounai_cast": jounai,
            "set_time": current_set_time,
        }

        st.session_state.planned_schedule = create_schedule(
            casts,
            st.session_state.customers,
            st.session_state.actual_assignments,
            rotation_time
        )

        st.rerun()


with op6:
    st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
    if st.button("空席にする", use_container_width=True):
        if st.session_state.selected_table in st.session_state.customers:
            del st.session_state.customers[st.session_state.selected_table]

        keys_to_delete = [
            key for key in st.session_state.actual_assignments
            if key.startswith(f"{st.session_state.selected_table}_")
        ]

        for key in keys_to_delete:
            del st.session_state.actual_assignments[key]

        st.session_state.planned_schedule = create_schedule(
            casts,
            st.session_state.customers,
            st.session_state.actual_assignments,
            rotation_time
        )

        st.rerun()


if selected_customer is not None:
    remain = remaining_minutes(selected_customer, now_minutes)
    end_text = to_time(customer_end_time(selected_customer))

    st.info(
        f"現在セット時間：{customer_set_time(selected_customer)}分 / "
        f"退店予定：{end_text} / 残り：{remain}分"
    )

    ext1, ext2, ext3 = st.columns(3)

    with ext1:
        if st.button("30分延長", use_container_width=True):
            st.session_state.customers[st.session_state.selected_table]["set_time"] = (
                customer_set_time(selected_customer) + 30
            )

            st.session_state.planned_schedule = create_schedule(
                casts,
                st.session_state.customers,
                st.session_state.actual_assignments,
                rotation_time
            )

            st.rerun()

    with ext2:
        if st.button("60分延長", use_container_width=True):
            st.session_state.customers[st.session_state.selected_table]["set_time"] = (
                customer_set_time(selected_customer) + 60
            )

            st.session_state.planned_schedule = create_schedule(
                casts,
                st.session_state.customers,
                st.session_state.actual_assignments,
                rotation_time
            )

            st.rerun()

    with ext3:
        if st.button("延長なし", use_container_width=True):
            st.session_state.customers[st.session_state.selected_table]["set_time"] = 60

            st.session_state.planned_schedule = create_schedule(
                casts,
                st.session_state.customers,
                st.session_state.actual_assignments,
                rotation_time
            )

            st.rerun()


if st.button("全卓クリア", use_container_width=True):
    st.session_state.customers = {}
    st.session_state.planned_schedule = []
    st.session_state.actual_assignments = {}
    st.rerun()


manual_conflicts = find_manual_conflicts(st.session_state.actual_assignments)

if manual_conflicts:
    st.error("手動入力でキャスト重複があります")

    for conflict in manual_conflicts:
        st.write(
            f'{conflict["時間"]} / '
            f'{conflict["キャスト"]} / '
            f'重複卓：{conflict["重複卓"]}'
        )


st.divider()
st.subheader("卓カード一覧")

for row_start in range(0, 20, 5):
    cols = st.columns(5)

    for col_index, table_name in enumerate(table_options[row_start:row_start + 5]):
        customer = st.session_state.customers.get(table_name)
        latest = current_by_table.get(table_name)

        if customer is not None:
            remain = remaining_minutes(customer, now_minutes)

            if remain <= 0:
                latest = None

        if customer is None:
            current_cast = "-"
            status = "空席"
            remain_text = "-"
            visit_text = "-"
            honshimei_text = "-"
            jounai_text = "-"
            set_text = "-"
            schedule_lines = []
            extension = False

        elif latest is None:
            current_cast = "-"
            status = "未計算"
            remain_text = f"残{remaining_minutes(customer, now_minutes)}"
            visit_text = customer["start_text"]
            honshimei_text = customer["honshimei_cast"]
            jounai_text = customer["jounai_cast"]
            set_text = f'{customer_set_time(customer)}分'
            schedule_lines = [
                f'{row["時間"].split("〜")[0]} {row["キャスト"]} {row["種別"]}'
                for row in st.session_state.planned_schedule
                if row["卓"] == table_name
            ]
            extension = False

        else:
            remain = remaining_minutes(customer, now_minutes)
            current_cast = latest["キャスト"]
            status = latest["種別"]
            remain_text = f"残{remain}"
            visit_text = customer["start_text"]
            honshimei_text = customer["honshimei_cast"]
            jounai_text = customer["jounai_cast"]
            set_text = f'{customer_set_time(customer)}分'
            extension = 0 < remain <= 15

            schedule_lines = [
                f'{row["時間"].split("〜")[0]} {row["キャスト"]} {row["種別"]}'
                for row in st.session_state.planned_schedule
                if row["卓"] == table_name
            ]

        mark = status_mark(status, extension)
        selected_prefix = "▶ " if st.session_state.selected_table == table_name else ""

        label = (
            f"{selected_prefix}{mark} {table_name}\n"
            f"現:{current_cast}｜{status}\n"
            f"{remain_text}｜来:{visit_text}\n"
            f"本:{honshimei_text}\n"
            f"場:{jounai_text}"
)

        with cols[col_index]:
            if st.button(label, key=f"card_{table_name}", use_container_width=True):
                st.session_state.selected_table = table_name
                st.rerun()


st.divider()
st.subheader("実績登録")

selected_table = st.session_state.selected_table

table_rows = [
    row for row in st.session_state.planned_schedule
    if row["卓"] == selected_table
]

if not table_rows:
    st.info("選択中の卓にスケジュールがありません。")
else:
    for row in table_rows:
        row_time = row["開始"]
        manual_key = f"{selected_table}_{row_time}"

        c1, c2, c3, c4 = st.columns([1.2, 1, 1, 1])

        with c1:
            st.write(f'{row["時間"]}')

        with c2:
            st.write(f'予定：{row["キャスト"]}')

        with c3:
            selected_manual = st.selectbox(
                "実際",
                manual_cast_options,
                index=manual_cast_options.index(
                    st.session_state.actual_assignments.get(manual_key, "自動")
                ),
                key=f"manual_{manual_key}"
            )

        with c4:
           if st.button("反映", key=f"apply_{manual_key}", use_container_width=True):
                if selected_manual == "自動":
                    if manual_key in st.session_state.actual_assignments:
                        del st.session_state.actual_assignments[manual_key]
                else:
                    st.session_state.actual_assignments[manual_key] = selected_manual

                st.session_state.planned_schedule = create_schedule(
                    casts,
                    st.session_state.customers,
                    st.session_state.actual_assignments,
                    rotation_time
                )

                st.rerun()