from fastapi import APIRouter, Response, HTTPException
from app.backend.core.state import config
from app.backend.core.password_utils import verify_hash
from app.backend.core.security import create_token

router = APIRouter()

@router.post("/auth/login")
def login(body:dict , response: Response):
    password = body.get("password")
    
    if not verify_hash(password, config.admin_password):
        raise HTTPException(status_code=401, detail="Invalid password")
    
    token = create_token({"sub": "admin"})
    
    response.set_cookie(
        key="token",
        value=token,
        httponly=True,
        max_age=3600,
        path="/"
    )
    
    return {"ok": True}

@router.post("/logout")
def logout(response:Response):
    response.delete_cookie("token")
    return {"ok": True}
    
