from argon2 import PasswordHasher
import bcrypt

password_hasher = PasswordHasher()

def verify_hash(user_input: str, stored: str) -> bool:
    
    # Argon2
    if stored.startswith("$argon2"):
        try:
            return password_hasher.verify(stored, user_input)
        except Exception:
            return False
    
    # Bcrypt
    if stored.startswith("$2"):
        try:
            return bcrypt.checkpw(user_input.encode(), stored.encode())
        except Exception:
            return False
    
    # Plain Text
    return user_input == stored