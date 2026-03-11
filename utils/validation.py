import re

def validate_username(username: str):
    username_regex = r"^[a-zA-Z0-9._]{3,20}$"
    return bool(re.match(username_regex, username))

def validate_password(password:str):
    password_regex = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$"
    return bool(re.match(password_regex, password))