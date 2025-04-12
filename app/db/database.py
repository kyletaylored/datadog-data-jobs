from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Get database connection details from environment variables
DB_USER = os.environ.get("DATABASE_USERNAME", "datadog")
DB_PASSWORD = os.environ.get("DATABASE_PASSWORD", "datadog")
DB_HOST = os.environ.get("DATABASE_HOST", "db")
DB_PORT = os.environ.get("DATABASE_PORT", "5432")
DB_NAME = os.environ.get("DATABASE_NAME", "datadog")

# Create the database URL
SQLALCHEMY_DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Create the SQLAlchemy engine
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Create a session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create a base class for SQLAlchemy models
Base = declarative_base()
