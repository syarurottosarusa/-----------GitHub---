def status_mark(status, extension):
    if status == "10分前戻し" and extension:
        return "🟪⚠️"
    if extension:
        return "🟨"
    if status == "本指名":
        return "🟥"
    if status == "場内指名":
        return "🟧"
    if status == "10分前戻し":
        return "🟪"
    if status == "ヘルプ":
        return "🟦"
    if status == "手動":
        return "🟩"
    if status == "手動重複注意":
        return "⚠️"
    if status == "フリー":
        return "⬜"
    return "⬛"