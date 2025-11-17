from fastapi import APIRouter, Depends
from app.backend.core.security import require_admin
from app.backend.schemas.crashed_container_schema import CrashedContainerLogs
from app.backend.schemas.chart_stats_schema import ChartStats
from app.backend.services.stats_service import StatsService

router = APIRouter(prefix="/crashed_containers", tags=["Crashed Containers"], dependencies=[Depends(require_admin)])

@router.get("", response_model=list[CrashedContainerLogs])
def list_crashed_containers(date_from:str, date_to:str):
    return StatsService.get_crashed_containers(date_from, date_to)

@router.get("/chart-stats", response_model=list[ChartStats])
def get_crashed_containers_graph_stats(date_from:str, date_to:str):
    return StatsService.get_crashed_containers_chart_stats(date_from, date_to)