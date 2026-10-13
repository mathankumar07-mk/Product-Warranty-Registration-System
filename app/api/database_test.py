from fastapi import APIRouter, HTTPException
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.core.database import engine

__test__ = False

router = APIRouter()


@router.get("/database-test")
def database_connection_check() -> dict[str, str]:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except SQLAlchemyError as error:
        raise HTTPException(
            status_code=500,
            detail="Unable to connect to the database",
        ) from error

    return {"message": "Database connected successfully"}