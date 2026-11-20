
import logging

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.database.connection import SessionLocal

logger = logging.getLogger(__name__)


def get_db():
    db: Session = SessionLocal()

    try:
        yield db

    except SQLAlchemyError:
        db.rollback()
        logger.exception("Database error during request")
        raise

    except Exception:
        db.rollback()
        logger.exception("Unexpected database session error")
        raise

    finally:
        db.close()
