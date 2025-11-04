from logging import Logger
from app.DAL.database import SessionLocal
from app.DAL.models import Container, CrashedContainer
from datetime import datetime
from typing import List,Tuple

def get_all_containers():
    with SessionLocal() as db:
        return db.query(Container).order_by(Container.containername.desc()).all()
    
def add_containers(containers: List[Tuple[str, str]], logger:Logger):
    with SessionLocal() as db:
        containers_to_add = []
        
        containers_ids = [c[1] for c in containers]
        
        existing = (db.query(Container).filter(Container.containerid.in_(containers_ids))).all()
        existing_ids = {row.containerid for row in existing}
        
        containers_to_add = [
            Container(containername=name, containerid=cid)
            for name, cid in containers
            if cid not in existing_ids
        ]
        
        if containers_to_add:
            db.add_all(containers_to_add)
            db.commit()
            logger.info(f"Containers added: {[container.containername for container in containers_to_add]}")
        else:
            logger.info("No new containers to add (all already present)")
            
        return containers_to_add

def add_crashed_container(container_id:str, logs:str, logger:Logger):
    with SessionLocal() as db:
        container = db.query(Container).filter(Container.containerid == container_id).first()
        crashed_container = CrashedContainer(
            logs = logs,
            crashedon = datetime.now(),
            container = container
        )
        db.add(crashed_container)
        db.commit()
        
        logger.info(f"Container {container_id} added to the crashed containers table")

        return crashed_container