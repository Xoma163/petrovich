from cryptography import fernet

from petrovich.settings import env


class Fernet:
    _cipher_suite: fernet.Fernet = fernet.Fernet(env.str("SECRET_KEY").encode())

    @classmethod
    def encrypt(cls, _str: str) -> str:
        return cls._cipher_suite.encrypt(_str.encode()).decode()

    @classmethod
    def decrypt(cls, encrypted_str: str) -> str:
        return cls._cipher_suite.decrypt(encrypted_str.encode()).decode()
