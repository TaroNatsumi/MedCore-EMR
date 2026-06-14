import json
from cryptography.fernet import Fernet
from django.conf import settings

# In a real production environment, this key should be loaded from environment variables (.env)
# For the prototype, we generate a static key if one doesn't exist in settings.
# A Fernet key is a 32-url-safe-base64-encoded bytes.
_FALLBACK_KEY = b'wA6bXmC4n5v5tO_47-x6zH6b_4T7H-uXkH8I3vWw3Y4='

def get_encryption_key():
    return getattr(settings, 'ENCRYPTION_KEY', _FALLBACK_KEY)

def encrypt_payload(data_dict: dict) -> bytes:
    """
    Encrypts a Python dictionary into a Fernet-encrypted AES-256 byte string.
    """
    key = get_encryption_key()
    f = Fernet(key)
    json_data = json.dumps(data_dict).encode('utf-8')
    encrypted_data = f.encrypt(json_data)
    return encrypted_data

def decrypt_payload(encrypted_bytes: bytes) -> dict:
    """
    Decrypts a Fernet-encrypted AES-256 byte string back into a Python dictionary.
    """
    key = get_encryption_key()
    f = Fernet(key)
    decrypted_json = f.decrypt(encrypted_bytes).decode('utf-8')
    return json.loads(decrypted_json)
