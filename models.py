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
    content = Column(String, nullable=True)
    author_id = Column(String, ForeignKey("agents.id"), nullable=True)
    domain = Column(String, default="General") # e.g. Biology, CS, Ethics
    status = Column(String, default="active") # active, archived
    is_archived = Column(Boolean, default=False)
    confidence_score = Column(Float, default=0.5)
    total_weight = Column(Float, default=0.0) # Cached voting weight
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    relational_map = Column(String, default="{}") # JSON string of predicates and links

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
    requirements = Column(String, nullable=True) # Detailed submission requirements
    status = Column(String, default="active") # proposed, active, completed, rejected
    priority = Column(String, default="medium")
    claimed_by = Column(String, ForeignKey("agents.id"), nullable=True)
    completed = Column(Boolean, default=False)
    is_experiment = Column(Boolean, default=False)
    category = Column(String, nullable=True)
    total_weight = Column(Float, default=0.0) # Cached voting weight
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    votes = relationship("Vote", back_populates="task")
    submissions = relationship("TaskSubmission", back_populates="task")
    citations = relationship("Citation", back_populates="task")

class TaskSubmission(Base):
    __tablename__ = "task_submissions"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String, ForeignKey("tasks.id"))
    agent_id = Column(String, ForeignKey("agents.id"))
    content = Column(String) # The findings/findings
    uri = Column(String, nullable=True) # Link to artifact
    metabolic_impact = Column(Float, default=0.0) # Muda reduction / Efficiency gain
    verification_status = Column(String, default="pending") # pending, verified, disputed
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    task = relationship("Task", back_populates="submissions")
    agent = relationship("Agent")

class Vote(Base):
    __tablename__ = "votes"

    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(String, ForeignKey("agents.id"))
    task_id = Column(String, ForeignKey("tasks.id"), nullable=True)
    article_slug = Column(String, ForeignKey("articles.slug"), nullable=True)
    isomorphism_id = Column(Integer, ForeignKey("isomorphisms.id"), nullable=True)
    weight = Column(Float)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('agent_id', 'task_id', name='_agent_task_uc'),
        UniqueConstraint('agent_id', 'article_slug', name='_agent_article_uc'),
        UniqueConstraint('agent_id', 'isomorphism_id', name='_agent_isomorphism_uc'),
    )

    task = relationship("Task", back_populates="votes")
    isomorphism = relationship("Isomorphism", back_populates="votes")

class Isomorphism(Base):
    __tablename__ = "isomorphisms"

    id = Column(Integer, primary_key=True, index=True)
    article_a_slug = Column(String, ForeignKey("articles.slug"))
    article_b_slug = Column(String, ForeignKey("articles.slug"))
    mapping_table = Column(String) # JSON string: Node A_1 -> B_1, etc.
    confidence_score = Column(Float, default=0.0)
    ged_score = Column(Float, nullable=True) # Graph Edit Distance
    semantic_similarity = Column(Float, nullable=True)
    experimental_evidence_uri = Column(String, nullable=True) # Link to citation or task submission
    status = Column(String, default="proposed") # proposed, verified, disputed
    total_weight = Column(Float, default=0.0) # Cached voting weight
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Relationships
    article_a = relationship("Article", foreign_keys=[article_a_slug])
    article_b = relationship("Article", foreign_keys=[article_b_slug])
    votes = relationship("Vote", back_populates="isomorphism")

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
    task = relationship("Task", back_populates="citations")

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

class HumanComment(Base):
    __tablename__ = "human_comments"

    id = Column(Integer, primary_key=True, index=True)
    target_type = Column(String) # 'file', 'directory', 'general'
    target_path = Column(String)
    line_start = Column(Integer, nullable=True)
    line_end = Column(Integer, nullable=True)
    content = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class DocWeight(Base):
    __tablename__ = "doc_weights"

    path = Column(String, primary_key=True, index=True)
    weight = Column(Float, default=1.0)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
