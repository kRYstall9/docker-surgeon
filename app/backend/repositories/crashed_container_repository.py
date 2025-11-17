from datetime import datetime
from logging import Logger
from sqlalchemy import and_, func
from app.backend.core.database import SessionLocal
from app.backend.schemas.crashed_container_schema import CrashedContainerBase, CrashedContainerLogs
from app.backend.models.crashed_container import CrashedContainer
from app.backend.schemas.chart_stats_schema import ChartStats


class CrashedContainerRepository:

    @staticmethod
    def add_crashed_container(ct_crashed:CrashedContainerBase, logger:Logger):
        with SessionLocal() as db:      
            crashed_container = CrashedContainer(
                logs = ct_crashed.logs,
                crashedon = datetime.now(),
                container_id = ct_crashed.container_id,
                container_name = ct_crashed.container_name
            )
            
            db.add(crashed_container)
            db.commit()
            db.refresh(crashed_container)
            
            logger.info(f"Container {ct_crashed.container_id} added to the crashed containers table")

            return crashed_container

    @staticmethod
    def get_all_crashed_containers(date_from:datetime, date_to:datetime) -> list[CrashedContainerLogs]:
        with SessionLocal() as db:
            
            crash_date = func.date(CrashedContainer.crashedon)
            date_from_str = date_from.strftime("%Y-%m-%d")
            date_to_str = date_to.strftime("%Y-%m-%d")
            
            
            crashed_containers = db.query(CrashedContainer.container_id, CrashedContainer.container_name, CrashedContainer.logs, CrashedContainer.crashedon).filter(crash_date >= date_from_str, crash_date <= date_to_str).order_by(CrashedContainer.crashedon.asc()).all()
            return [
                CrashedContainerLogs(
                    container_id=container_id,
                    container_name=container_name,
                    crashed_on=crashed_on,
                    logs=logs
                )
                for container_id, container_name, logs, crashed_on in crashed_containers
            ]

    @staticmethod
    def get_crashed_containers_stats_by_date(date_from:datetime, date_to:datetime):
        with SessionLocal() as db:
            
            crash_date = func.date(CrashedContainer.crashedon)
            
            date_from_str = date_from.strftime("%Y-%m-%d")
            date_to_str = date_to.strftime("%Y-%m-%d")
            
            rows = (
                db.query(
                    CrashedContainer.container_id,
                    CrashedContainer.container_name, 
                    func.count(CrashedContainer.container_id).label('crash_count'),
                    crash_date.label("crash_date")
                )
                .filter(
                    crash_date >= date_from_str,
                    crash_date <= date_to_str
                )
                .group_by(
                    crash_date,
                    CrashedContainer.container_name
                )
                .order_by(
                    crash_date.asc(),
                    CrashedContainer.container_name.asc()
                )
                .all()
            )
            
            return [
                ChartStats(
                    crashed_on = crash_date,
                    container_id=containerid,
                    container_name=containername,
                    crash_count=crash_count
                )
                for containerid, containername, crash_count, crash_date in rows
            ]