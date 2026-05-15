from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, String, Integer, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from typing import List, Optional

app = FastAPI(title="Read It Later API")

# Allow CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SQLALCHEMY_DATABASE_URL = "sqlite:///./readitlater.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class LinkModel(Base):
    __tablename__ = "links"
    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, unique=True, index=True)
    title = Column(String, default="No title")
    tags = Column(String, default="")
    created_at = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

class LinkCreate(BaseModel):
    url: str
    title: Optional[str] = None
    tags: Optional[str] = ""

class LinkResponse(BaseModel):
    id: int
    url: str
    title: str
    tags: str
    created_at: datetime

@app.post("/links", response_model=LinkResponse)
def create_link(link: LinkCreate):
    db = SessionLocal()
    
    title = link.title if link.title and link.title.strip() else link.url.replace("https://", "").replace("http://", "").split("/")[0]
    db_link = LinkModel(url=link.url, title=title, tags=link.tags or "")
    db.add(db_link)
    db.commit()
    db.refresh(db_link)
    db.close()
    return db_link

@app.get("/links", response_model=List[LinkResponse])
def get_links(skip: int = 0, limit: int = 100):
    db = SessionLocal()
    links = db.query(LinkModel).order_by(LinkModel.created_at.desc()).offset(skip).limit(limit).all()
    db.close()
    return links

@app.get("/search")
def search_links(q: str):
    db = SessionLocal()
    results = db.query(LinkModel).filter((LinkModel.title.contains(q)) | (LinkModel.tags.contains(q))).all()
    db.close()
    return {"results": results}

@app.delete("/links/{link_id}")
def delete_link(link_id: int):
    db = SessionLocal()
    link = db.query(LinkModel).filter(LinkModel.id == link_id).first()
    if not link:
        db.close()
        raise HTTPException(status_code=404, detail="Link not found")
    db.delete(link)
    db.commit()
    db.close()
    return {"message": "Link deleted"}