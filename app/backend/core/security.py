import secrets
from pathlib import Path
from datetime import datetime, timezone, timedelta
from fastapi import HTTPException, Request
import jwt

SECRET_FILE = Path("/app/app/data/jwt_secret.key")

def load_or_create_jwt_secret() -> str:
    if SECRET_FILE.exists():
        return SECRET_FILE.read_text().strip()
    
    SECRET_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    new_token = secrets.token_hex(64)
    SECRET_FILE.write_text(new_token)
    return new_token

JWT_SECRET = load_or_create_jwt_secret()

def create_token(data:dict, expires_minutes:int = 60):
    to_encode= data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)
    to_encode["exp"] = expire
  
    return jwt.encode(to_encode, JWT_SECRET, algorithm='HS256')


def require_admin(request: Request):
    
    token = request.cookies.get("token")
    if not token:
        raise HTTPException(status_code=401, detail="Missing token")

    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    if payload.get("sub") != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")

    return payload