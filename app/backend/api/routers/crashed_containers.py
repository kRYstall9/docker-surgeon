from fastapi import APIRouter
from app.backend.schemas.crashed_container_schema import CrashedContainerLogs
from app.backend.schemas.graph_stats_schema import GraphStats
from app.backend.services.stats_service import StatsService

router = APIRouter(prefix="/crashed_containers", tags=["Crashed Containers"])

@router.get("", response_model=list[CrashedContainerLogs])
def list_crashed_containers(date:str):
    return StatsService.get_crashed_containers(date)

@router.get("/chart-stats", response_model=list[GraphStats])
def get_crashed_containers_graph_stats(date:str):
    return StatsService.get_crashed_containers_chart_stats(date)