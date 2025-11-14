from logging import Logger
from app.backend.core.database import SessionLocal
from app.backend.schemas.container_schema import ContainerCreate
from app.backend.models.container import Container
from typing import List

class ContainerRepository:
    
    @staticmethod
    def get_all_containers():
        with SessionLocal() as db:
            return db.query(Container).order_by(Container.containername.desc()).all()

    @staticmethod
    def add_containers(containers: List[ContainerCreate], logger:Logger):
        with SessionLocal() as db:
            containers_to_add = []
            
            containers_ids = [c.cid for c in containers]
            
            existing = (db.query(Container).filter(Container.containerid.in_(containers_ids))).all()
            existing_ids = {row.containerid for row in existing}
            
            containers_to_add = [
                Container(containername=c.name, containerid=c.cid)
                for c in containers
                if c.cid not in existing_ids
            ]
            
            if containers_to_add:
                db.add_all(containers_to_add)
                db.commit()
                db.refresh_all(containers_to_add)
                logger.info(f"Containers added: {[container.containername for container in containers_to_add]}")
            else:
                logger.info("No new containers to add (all already present)")
                
            return containers_to_add