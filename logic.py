from time_utils import to_time


def customer_set_time(customer):
    return customer.get("set_time", 60)


def customer_end_time(customer):
    return customer["start"] + customer_set_time(customer)


def remaining_minutes(customer, now_minutes):
    return min(
        customer_set_time(customer),
        max(0, customer_end_time(customer) - now_minutes)
    )


def get_return_cast(customer):
    if customer["honshimei_cast"] != "なし":
        return customer["honshimei_cast"]

    if customer["jounai_cast"] != "なし":
        return customer["jounai_cast"]

    return "なし"


def is_return_time(customer, current_time):
    return current_time >= customer_end_time(customer) - 10

def create_schedule(casts, customers, manual_assignments, rotation_time):
    customer_list = list(customers.values())

    if not customer_list:
        return []

    schedule = []
    used_casts_by_time = {}
    used_history_by_table = {}

    current_time = min(c["start"] for c in customer_list)
    last_time = max(customer_end_time(c) for c in customer_list)

    while current_time < last_time:
        used_casts_by_time[current_time] = []

        active_customers = [
            c for c in customer_list
            if c["start"] <= current_time < customer_end_time(c)
        ]

        active_customers = sorted(
            active_customers,
            key=lambda c: (
                0 if is_return_time(c, current_time) and get_return_cast(c) != "なし"
                else 1 if c["honshimei_cast"] != "なし"
                else 2 if c["jounai_cast"] != "なし"
                else 3
            )
        )

        for customer in active_customers:
            table = customer["table"]
            used_history_by_table.setdefault(table, [])

            available_casts = [
                c["name"] for c in sorted(casts, key=lambda c: c["start"])
                if c["start"] <= current_time
                and c["name"] not in used_casts_by_time[current_time]
            ]

            assignment_key = f"{table}_{current_time}"
            actual_cast = manual_assignments.get(assignment_key)

            selected_cast = "空きなし"
            status = "空きなし"

            if actual_cast is not None and actual_cast != "自動":
                selected_cast = actual_cast
                status = "手動" if actual_cast in available_casts else "手動重複注意"

            else:
                return_cast = get_return_cast(customer)

                if is_return_time(customer, current_time) and return_cast != "なし":
                    if return_cast in available_casts:
                        selected_cast = return_cast
                        status = "10分前戻し"
                    elif available_casts:
                        selected_cast = available_casts[0]
                        status = "ヘルプ"
                    else:
                        selected_cast = "空きなし"
                        status = "ヘルプ不可"

                elif customer["honshimei_cast"] != "なし":
                    target = customer["honshimei_cast"]

                    if target in available_casts:
                        selected_cast = target
                        status = "本指名"
                    elif available_casts:
                        selected_cast = available_casts[0]
                        status = "ヘルプ"
                    else:
                        selected_cast = "空きなし"
                        status = "ヘルプ不可"

                elif customer["jounai_cast"] != "なし":
                    target = customer["jounai_cast"]

                    if target in available_casts:
                        selected_cast = target
                        status = "場内指名"
                    elif available_casts:
                        selected_cast = available_casts[0]
                        status = "ヘルプ"
                    else:
                        selected_cast = "空きなし"
                        status = "ヘルプ不可"

                else:
                    if available_casts:
                        unused = [
                            name for name in available_casts
                            if name not in used_history_by_table[table]
                        ]

                        selected_cast = unused[0] if unused else available_casts[0]
                        status = "フリー"

            if selected_cast not in ["空きなし", "ヘルプ不可"]:
                used_casts_by_time[current_time].append(selected_cast)

                if selected_cast not in used_history_by_table[table]:
                    used_history_by_table[table].append(selected_cast)

            schedule.append({
                "開始": current_time,
                "時間": f"{to_time(current_time)}〜{to_time(current_time + rotation_time)}",
                "卓": table,
                "キャスト": selected_cast,
                "種別": status,
            })

        current_time += rotation_time

    return sorted(schedule, key=lambda x: (x["開始"], x["卓"]))

def find_manual_conflicts(manual_assignments):
    conflicts = {}

    for key, cast in manual_assignments.items():
        if cast == "自動":
            continue

        table, time_text = key.rsplit("_", 1)
        time_value = int(time_text)
        conflict_key = (time_value, cast)

        if conflict_key not in conflicts:
            conflicts[conflict_key] = []

        conflicts[conflict_key].append(table)

    result = []

    for (time_value, cast), tables in conflicts.items():
        if len(tables) >= 2:
            result.append({
                "時間": to_time(time_value),
                "キャスト": cast,
                "重複卓": "、".join(tables)
            })

    return result