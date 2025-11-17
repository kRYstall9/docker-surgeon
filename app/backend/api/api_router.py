from fastapi import APIRouter
from app.backend.api.routers import auth, crashed_containers

api_router = APIRouter()
api_router.include_router(crashed_containers.router)
api_router.include_router(auth.router)