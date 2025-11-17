from logging import Logger
from app.backend.core.database import SessionLocal
from app.backend.schemas.user_schema import User as UserSchema
from app.backend.models.user import User

class UserRepository:
    
    @staticmethod
    def get_user(uid: int):
        with SessionLocal() as db:
            return db.query(User).filter(User.id == uid).first()

    @staticmethod
    def update_user(user:UserSchema, logger:Logger):
        with SessionLocal() as db:
            db_user = db.query(User).filter(User.id == user.id).first()
            
            if not db_user:
                logger.error(f"User with id {user.id} not found for update")
                return None
            
            db_user.username = user.username
            db_user.password = user.password
            
            db.commit()
            db.refresh(db_user)
            
            logger.info(f"User with id {user.id} updated successfully")
            
            return db_user