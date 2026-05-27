cast_names = [chr(i) for i in range(ord("A"), ord("Z") + 1)]
table_options = [f"{i}卓" for i in range(1, 21)]
cast_options = ["なし"] + cast_names
manual_cast_options = ["自動"] + cast_names
hour_options = list(range(24))
minute_options = list(range(60))
start_time_options = [f"{h:02d}:{m:02d}" for h in range(24) for m in [0, 30]]

rotation_time = 30