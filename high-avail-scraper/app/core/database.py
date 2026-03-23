from sqlalchemy import create_engine, Column, String, Integer, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime

DATABASE_URL = "postgresql://admin:adminpass@localhost:5432/scraper_results"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class ScrapeLog(Base):
    __tablename__ = "scrape_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    url = Column(String)
    status_code = Column(Integer)
    html_size = Column(Integer)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)


ScrapeResult = ScrapeLog

Base.metadata.create_all(bind=engine)