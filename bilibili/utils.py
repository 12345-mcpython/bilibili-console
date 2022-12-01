import re


def format_time(time):
    if time > 60 * 60:
        fmt = "{}:{}:{}"
        hour = time // (60 * 60)
        minute = (time - (hour * 60 * 60)) // 60
        sec = time - (hour * 60 * 60) - minute * 60
        if minute < 10:
            fmt = "{}:0{}:{}"
        if sec < 10:
            fmt = "{}:{}:0{}"
        if sec < 10 and minute < 10:
            fmt = "{}:0{}:0{}"
        if hour > 10:
            fmt = "1" + fmt
        return fmt.format(hour, minute, sec)
    else:
        fmt = "{}:{}"
        minute = time // 60
        if minute < 10:
            fmt = "0{}:{}"
        sec = time - minute * 60
        if sec < 10:
            fmt = "{}:0{}"
        if sec < 10 and minute < 10:
            fmt = "0{}:0{}"
        return fmt.format(minute, sec)


def validateTitle(title):
    rstr = r"[\/\\\:\*\?\"\<\>\|]"  # '/ \ : * ? " < > |'
    new_title = re.sub(rstr, "_", title)  # 替换为下划线
    return new_title