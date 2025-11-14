from fastapi import APIRouter
from app.backend.api.routers import crashed_containers

api_router = APIRouter()
api_router.include_router(crashed_containers.router)