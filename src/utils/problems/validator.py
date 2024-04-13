import re
from django.core.validators import ValidationError

def validation_zip_file_name(input_string):
    pattern = r'^[a-zA-Z0-9_]+$'

    if not re.match(pattern, input_string):
        raise ValidationError("檔案名稱只能包含 A-Z a-z 0-9 _")
