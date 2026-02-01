from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
import datetime
try:
    from .database import Base
except ImportError:
    from database import Base

class Article(Base):
    __tablename__ = "articles"

    slug = Column(String, primary_key=True, index=True)
    title = Column(String)
    status = Column(String, default="active") # active, archived
    is_archived = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

class Agent(Base):
    __tablename__ = "agents"

    id = Column(String, primary_key=True, index=True) # e.g., agent:aragog
    sagacity = Column(Float, default=0.1)
    contributions = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Task(Base):
    __tablename__ = "tasks"

    id = Column(String, primary_key=True, index=True) # Hash of description
    text = Column(String)
    status = Column(String, default="active") # proposed, active, completed, rejected
    priority = Column(String, default="medium")
    claimed_by = Column(String, ForeignKey("agents.id"), nullable=True)
    completed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    votes = relationship("Vote", back_populates="task")

class Vote(Base):
    __tablename__ = "votes"

    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(String, ForeignKey("agents.id"))
    task_id = Column(String, ForeignKey("tasks.id"))
    weight = Column(Float)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    task = relationship("Task", back_populates="votes")
