from passlib.context import CryptContext
from jose import jwt
from cryptography.fernet import Fernet
import os
from typing import Tuple

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(data: dict, secret: str, expires_delta: int = 3600) -> str:
    to_encode = data.copy()
    to_encode.update({"exp": expires_delta})
    return jwt.encode(to_encode, secret, algorithm="HS256")


def generate_fernet_key() -> bytes:
    key = os.environ.get("FERNET_KEY")
    if key:
        return key.encode()
    return Fernet.generate_key()


def encrypt_data(value: bytes, key: bytes) -> bytes:
    f = Fernet(key)
    return f.encrypt(value)


def decrypt_data(token: bytes, key: bytes) -> bytes:
    f = Fernet(key)
    return f.decrypt(token)
