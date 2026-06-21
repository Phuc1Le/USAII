from sqlalchemy import (
    create_engine, Column, Integer, String, Text, DateTime, ForeignKey
)
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime, timezone

DATABASE_URL = "sqlite:///./app.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})


class Base(DeclarativeBase):
    pass


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    category = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    idea = Column(Text, nullable=False)
    goal = Column(Text, nullable=True)
    # status ∈ {intake, clarifying, goal_select, plan_gen, plan_review, execution}
    status = Column(String, nullable=False, default="intake")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

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
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    project = relationship("Project", back_populates="decisions")


def init_db():
    Base.metadata.create_all(engine)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()