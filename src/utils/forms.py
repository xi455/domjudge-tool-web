from datetime import datetime

from pytz import UnknownTimeZoneError, timezone


def validate_country_format(time_string: str):
    """
    Validates the format of a time string and extracts the country name.

    Args:
        time_string (str): The time string to be validated.

    Returns:
        tuple: A tuple containing a boolean value indicating whether the format is valid,
               and the result time if the format is valid, or None otherwise.
    """
    try:
        start_time_list = str(time_string).split(" ")

        time_str = f"{start_time_list[0]} {start_time_list[1]}"
        country_name = start_time_list[2]

        dt = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
        tz = timezone(country_name)
        result_time = tz.localize(dt)

    except (ValueError, IndexError, UnknownTimeZoneError):
        return False, None

    return True, result_time
