from django.contrib.auth.hashers import make_password, check_password

def hash_password(raw: str) -> str:
    return make_password(raw)

def verify_password(raw: str, hashed: str) -> bool:
    return check_password(raw, hashed)
