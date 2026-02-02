from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Enum, Table, UniqueConstraint
from sqlalchemy.orm import relationship
import datetime
import enum
try:
    from .database import Base
except ImportError:
    from database import Base

# Association table for Article <-> Citation (Many-to-Many)
article_citations = Table(
    "article_citations",
    Base.metadata,
    Column("article_slug", String, ForeignKey("articles.slug"), primary_key=True),
    Column("citation_id", String, ForeignKey("citations.id"), primary_key=True),
)

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
    confidence_score = Column(Float, default=0.5)
    total_weight = Column(Float, default=0.0) # Cached voting weight
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    citations = relationship("Citation", secondary=article_citations, back_populates="articles")

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
    version = Column(Integer, default=1)
    text = Column(String)
    status = Column(String, default="active") # proposed, active, completed, rejected
    priority = Column(String, default="medium")
    claimed_by = Column(String, ForeignKey("agents.id"), nullable=True)
    completed = Column(Boolean, default=False)
    is_experiment = Column(Boolean, default=False)
    total_weight = Column(Float, default=0.0) # Cached voting weight
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    votes = relationship("Vote", back_populates="task")
    submissions = relationship("Citation", back_populates="task")

class Vote(Base):
    __tablename__ = "votes"

    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(String, ForeignKey("agents.id"))
    task_id = Column(String, ForeignKey("tasks.id"), nullable=True)
    article_slug = Column(String, ForeignKey("articles.slug"), nullable=True)
    weight = Column(Float)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('agent_id', 'task_id', name='_agent_task_uc'),
        UniqueConstraint('agent_id', 'article_slug', name='_agent_article_uc'),
    )

    task = relationship("Task", back_populates="votes")

class Citation(Base):
    __tablename__ = "citations"

    id = Column(String, primary_key=True, index=True) # key e.g. harvard_2025_biobots
    task_id = Column(String, ForeignKey("tasks.id"), nullable=True)
    task_version = Column(Integer, nullable=True)
    agent_id = Column(String, ForeignKey("agents.id"), nullable=True)
    type = Column(Enum(CitationType), default=CitationType.academic_paper)
    uri = Column(String)
    title = Column(String)
    
    # Granular Information Quality Metrics (0.0 - 1.0)
    objectivity = Column(Float, default=0.5)
    credibility = Column(Float, default=0.5)
    accuracy = Column(Float, default=0.5)
    clarity = Column(Float, default=0.5)
    completeness = Column(Float, default=0.5)
    
    quality_score = Column(Float, default=0.5) # The calculated aggregate
    status = Column(Enum(CitationStatus), default=CitationStatus.active)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    last_reviewed_at = Column(DateTime, default=datetime.datetime.utcnow)

    reviews = relationship("CitationReview", back_populates="citation")
    articles = relationship("Article", secondary=article_citations, back_populates="citations")
    task = relationship("Task", back_populates="submissions")

class CitationReview(Base):
    __tablename__ = "citation_reviews"

    id = Column(Integer, primary_key=True, index=True)
    citation_id = Column(String, ForeignKey("citations.id"))
    agent_id = Column(String, ForeignKey("agents.id"))
    
    # 1-5 scale for agent input
    objectivity = Column(Integer)
    credibility = Column(Integer)
    accuracy = Column(Integer)
    clarity = Column(Integer)
    completeness = Column(Integer)
    
    weight = Column(Float)        # Reviewer sagacity at time of review
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    citation = relationship("Citation", back_populates="reviews")

class Verification(Base):
    __tablename__ = "verifications"

    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(String, ForeignKey("agents.id"))
    platform = Column(String) # 'x', 'github', 'moltbook'
    handle = Column(String)
    proof_url = Column(String)
    verified_at = Column(DateTime, default=datetime.datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('platform', 'handle', name='_platform_handle_uc'),
    )
