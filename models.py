from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Enum
from sqlalchemy.orm import relationship
import datetime
import enum
try:
    from .database import Base
except ImportError:
    from database import Base

class CitationType(enum.Enum):
    experiment = "experiment"
    academic_paper = "academic_paper"
    dataset = "dataset"
    code = "code"

class CitationStatus(enum.Enum):
    active = "active"
    retracted = "retracted"
    disputed = "disputed"

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
    competence_score = Column(Float, default=0.1)
    alignment_score = Column(Float, default=0.1)
    last_certified_at = Column(DateTime, nullable=True)
    exam_version_hash = Column(String, nullable=True)
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

class Citation(Base):
    __tablename__ = "citations"

    id = Column(String, primary_key=True, index=True) # key e.g. harvard_2025_biobots
    type = Column(Enum(CitationType), default=CitationType.academic_paper)
    uri = Column(String)
    title = Column(String)
    quality_score = Column(Float, default=0.5)
    status = Column(Enum(CitationStatus), default=CitationStatus.active)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    reviews = relationship("CitationReview", back_populates="citation")

class CitationReview(Base):
    __tablename__ = "citation_reviews"

    id = Column(Integer, primary_key=True, index=True)
    citation_id = Column(String, ForeignKey("citations.id"))
    agent_id = Column(String, ForeignKey("agents.id"))
    objectivity = Column(Integer) # 1-5
    credibility = Column(Integer) # 1-5
    clarity = Column(Integer)     # 1-5
    weight = Column(Float)        # Reviewer sagacity at time of review
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    citation = relationship("Citation", back_populates="reviews")
