from datetime import datetime
from logging import Logger
from sqlalchemy.orm import joinedload
from sqlalchemy import and_, func
from app.backend.core.database import SessionLocal
from app.backend.schemas.crashed_container_schema import CrashedContainerBase, CrashedContainerLogs
from app.backend.models.container import Container
from app.backend.models.crashed_container import CrashedContainer
from app.backend.schemas.graph_stats_schema import GraphStats


class CrashedContainerRepository:

    @staticmethod
    def add_crashed_container(ct_crashed:CrashedContainerBase, logger:Logger):
        with SessionLocal() as db:
            container = db.query(Container).filter(Container.containerid == ct_crashed.container_id).first()
        
            crashed_container = CrashedContainer(
                logs = ct_crashed.logs,
                crashedon = datetime.now(),
                container = container
            )
            
            db.add(crashed_container)
            db.commit()
            db.refresh(crashed_container)
            
            logger.info(f"Container {ct_crashed.container_id} added to the crashed containers table")

            return crashed_container

    @staticmethod
    def get_container_logs(containerid: str, logsDate: datetime):
        with SessionLocal() as db:
            container_logs= db.query(CrashedContainer).filter(and_(CrashedContainer.containerid == containerid, func.date(CrashedContainer.crashedon) == logsDate.date())).with_entities(CrashedContainer.logs).all()
            return container_logs or None

    @staticmethod
    def get_all_crashed_containers(date:datetime) -> list[CrashedContainerLogs]:
        with SessionLocal() as db:
            crashed_containers = db.query(CrashedContainer.containerid, Container.containername, CrashedContainer.logs, CrashedContainer.crashedon).join(CrashedContainer.container).filter(func.date(CrashedContainer.crashedon) == date.date()).order_by(CrashedContainer.crashedon.asc()).all()
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
            
            rows = (
                db.query(
                    CrashedContainer.containerid,
                    Container.containername, 
                    func.count(CrashedContainer.containerid).label('crash_count'),
                    crash_date.label("crash_date")
                )
                .join(CrashedContainer.container)
                .filter(
                    crash_date >= date_from.date(),
                    crash_date <= date_to.date()
                )
                .group_by(
                    crash_date,
                    CrashedContainer.containerid,
                    Container.containername
                )
                .order_by(
                    crash_date.asc(),
                    Container.containername.asc()
                )
                .all()
            )
            
            return [
                GraphStats(
                    crashed_on = crash_date,
                    container_id=containerid,
                    container_name=containername,
                    crash_count=crash_count
                )
                for containerid, containername, crash_count, crash_date in rows
            ]