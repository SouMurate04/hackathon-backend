import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_async_engine(
    DATABASE_URL,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)

Base = declarative_base()

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session