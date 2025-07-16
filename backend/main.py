from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import create_engine, Column, Integer, String, MetaData, Table, select
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Database configuration
# Get database credentials from environment variables
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_DB = os.getenv("POSTGRES_DB")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "db")  # Default to 'db' for Docker environment

# Create database connection URL
DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:5432/{POSTGRES_DB}"

# Create SQLAlchemy engine
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Define database model
class TestTable(Base):
    """Test table model for demonstration purposes"""
    __tablename__ = "test_table"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)

# Create tables in the database
Base.metadata.create_all(bind=engine)

# Pydantic model for API request/response
class TestItem(BaseModel):
    """Test item schema for API operations"""
    name: str
    
    class Config:
        orm_mode = True

# Database session dependency
def get_db():
    """Dependency to get a database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

app = FastAPI(
    title="Talktor API",
    description="API for the Talktor project",
    version="0.1.0"
)

@app.get("/")
def read_root():
    """Root endpoint returning a welcome message"""
    return {"message": "Welcome to Talktor API"}

@app.get("/health")
def health_check():
    """Health check endpoint for monitoring"""
    return {"status": "ok"}

@app.get("/db-test")
def db_test(db = Depends(get_db)):
    """Test database connection endpoint"""
    try:
        # Try to execute a simple query
        result = db.execute(select(1)).scalar()
        return {"status": "ok", "connection": "successful", "test_query": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection error: {str(e)}")

@app.post("/items/", response_model=TestItem)
def create_item(item: TestItem, db = Depends(get_db)):
    """Create a new test item in the database"""
    db_item = TestTable(name=item.name)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

@app.get("/items/")
def read_items(db = Depends(get_db)):
    """Get all test items from the database"""
    items = db.query(TestTable).all()
    return items
