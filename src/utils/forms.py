import re

from datetime import datetime

from pytz import UnknownTimeZoneError, timezone


def validate_time_format(time_string: str):
    pattern = r"^[+-][0-9][0-9]:[0-5][0-9]:[0-5][0-9]$"
    return re.match(pattern, time_string) is not None


def validate_country_format(time_string: str):
    try:
        start_time_list = str(time_string).split(" ")

        time_str = f"{start_time_list[0]} {start_time_list[1]}"
        country_name = start_time_list[2]

        datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
        timezone(country_name)

    except (ValueError, UnknownTimeZoneError):
        raise ValueError(
            f"{time_string} 格式錯誤 請提供有效的日期和時間格式（例如：2023-01-01 14:06:00 Asia/Taipei）"
        )

    return time_string
