from utils.forms import validate_country_format, validate_time_format


def contest_initial_data_format(initial_data: dict):
    for key, value in initial_data.items():

        if value == "" or (len(value) > 9 and key != "start_time"):
            continue

        if key in ("short_name", "name") or value in ("0", "1"):
            continue

        if key == "start_time":
            initial_data[key] = validate_country_format(time_string=value)
            continue

        if validate_time_format(time_string=value) is False:
            initial_data[key] = f"{value}:00"

    return initial_data
