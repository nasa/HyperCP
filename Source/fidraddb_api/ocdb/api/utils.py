from typing import Optional, Union


def encrypt(txt: str, salt: Optional[Union[str, bytes]] = None) -> str:
    import hashlib

    if salt is None:
        # noinspection InsecureHash
        h = hashlib.sha512(txt.encode('utf-8'))
        return h.hexdigest()
    else:
        if isinstance(salt, str):
            salt = salt.encode('utf-8')

        h = hashlib.pbkdf2_hmac('sha512', txt.encode('utf-8'), salt, 100000)
        return h.hex()
