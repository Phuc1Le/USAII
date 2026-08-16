from sqlalchemy import (
    Column, Integer, String, Text, DateTime, ForeignKey, UniqueConstraint
)
from sqlalchemy.orm import DeclarativeBase, relationship
from datetime import datetime, timezone
from pgvector.sqlalchemy import Vector


class Base(DeclarativeBase):
    pass


class User(Base):
    """Who owns a project.

    Deliberately has no email or password yet: identity currently comes from an
    X-User-Id header the client sends, which separates people's data but does not
    prove who they are. Adding real login later means adding columns here and
    changing where get_current_user reads the id from — no data migration, and
    nothing that already filters by user_id has to change.
    """

    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    # what the client sends as X-User-Id: an opaque value it generated and stored
    # itself, so it never has to ask the backend who it is. Replaced by the subject
    # of a verified token once real login exists.
    client_key = Column(String, nullable=False, unique=True)
    # a name the person can read, e.g. "local-dev" — not used for lookups
    display_name = Column(String, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    projects = relationship("Project", back_populates="user")


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String, nullable=False)
    category = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    idea = Column(Text, nullable=False)
    goal = Column(Text, nullable=True)
    # status ∈ {intake, clarifying, goal_select, plan_gen, plan_review, execution}
    status = Column(String, nullable=False, default="intake")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="projects")
    steps = relationship("Step", back_populates="project", cascade="all, delete-orphan")
    milestones = relationship("Milestone", back_populates="project", cascade="all, delete-orphan")
    chat_sessions = relationship("ChatSession", back_populates="project", cascade="all, delete-orphan")
    decisions = relationship("Decision", back_populates="project", cascade="all, delete-orphan")


class Step(Base):
    __tablename__ = "steps"

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    order_index = Column(Integer, nullable=False)
    # status ∈ {todo, in_progress, blocked, deferred, done}
    status = Column(String, nullable=False, default="todo")
    intended_start = Column(String, nullable=True)  # ISO date string, e.g. "2026-06-20"
    intended_end = Column(String, nullable=True)
    
    # filled in when the step is marked done — see Phase 4 cross-step memory
    outcome_summary = Column(Text, nullable=True)

    project = relationship("Project", back_populates="steps")
    tasks = relationship("Task", back_populates="step", cascade="all, delete-orphan")
    milestone = relationship("Milestone", back_populates="step", uselist=False)
    dependencies = relationship(
        "StepDependency",
        foreign_keys="StepDependency.step_id",
        cascade="all, delete-orphan",
    )


class StepDependency(Base):
    __tablename__ = "step_dependencies"

    step_id = Column(Integer, ForeignKey("steps.id"), primary_key=True)
    depends_on_step_id = Column(Integer, ForeignKey("steps.id"), primary_key=True)


class Task(Base):
    __tablename__ = "tasks"
    # tasks are generated lazily on first read of a step; two concurrent readers
    # would otherwise both find the step empty and both insert a full set
    __table_args__ = (
        UniqueConstraint("step_id", "order_index", name="uq_tasks_step_order"),
    )

    id = Column(Integer, primary_key=True)
    step_id = Column(Integer, ForeignKey("steps.id"), nullable=False)
    title = Column(String, nullable=False)
    detail = Column(Text, nullable=True)
    # status ∈ {todo, done}
    status = Column(String, nullable=False, default="todo")
    order_index = Column(Integer, nullable=False, default=0)

    step = relationship("Step", back_populates="tasks")


class Milestone(Base):
    __tablename__ = "milestones"

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    title = Column(String, nullable=False)
    step_id = Column(Integer, ForeignKey("steps.id"), nullable=True)
    achieved_at = Column(DateTime, nullable=True)

    project = relationship("Project", back_populates="milestones")
    step = relationship("Step", back_populates="milestone")


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    # scope_type ∈ {step, project}
    scope_type = Column(String, nullable=False, default="project")
    scope_step_id = Column(Integer, ForeignKey("steps.id"), nullable=True)
    summary = Column(Text, nullable=True)
    summary_message_count = Column(Integer, nullable=True)

    project = relationship("Project", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"), nullable=False)
    # role ∈ {user, assistant}
    role = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    session = relationship("ChatSession", back_populates="messages")


class Decision(Base):
    __tablename__ = "decisions"

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    content = Column(Text, nullable=False)
    embedding = Column(Vector(3072), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    project = relationship("Project", back_populates="decisions")