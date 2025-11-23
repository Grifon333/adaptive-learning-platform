import uuid

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from .database import Base


class UserRole(str, Enum):
    student = "student"
    instructor = "instructor"
    admin = "admin"


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    role = Column(String(50), nullable=False, default=UserRole.student)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    avatar_url = Column(String(500), nullable=True)
    last_login = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    profile = relationship(
        "StudentProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )

    learning_paths = relationship("LearningPath", back_populates="student")
    knowledge_states = relationship("KnowledgeState", back_populates="student")


class StudentProfile(Base):
    __tablename__ = "student_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    cognitive_profile = Column(
        JSONB, nullable=True, default=lambda: {"memory": 0.5, "attention": 0.5}
    )
    learning_preferences = Column(
        JSONB,
        nullable=True,
        default=lambda: {
            "visual": 0.25,
            "auditory": 0.25,
            "kinesthetic": 0.25,
            "reading": 0.25,
        },
    )
    timezone = Column(String(50), nullable=True, default="UTC")
    study_schedule = Column(JSONB, nullable=True, default=lambda: {})
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="profile")


class LearningPath(Base):
    __tablename__ = "learning_paths"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    goal_concepts = Column(JSONB, nullable=False)
    status = Column(String(50), default="active")  # 'active', 'completed', 'abandoned'
    estimated_time = Column(Integer, nullable=True)  # Total time, min
    actual_time = Column(Integer, default=0)
    completion_percentage = Column(Float, default=0.0)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    completed_at = Column(DateTime, nullable=True)

    student = relationship("User", back_populates="learning_paths")
    steps = relationship(
        "LearningStep",
        back_populates="path",
        cascade="all, delete-orphan",
        order_by="LearningStep.step_number",
    )


class LearningStep(Base):
    __tablename__ = "learning_steps"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    path_id = Column(
        UUID(as_uuid=True),
        ForeignKey("learning_paths.id", ondelete="CASCADE"),
        nullable=False,
    )
    step_number = Column(Integer, nullable=False)
    concept_id = Column(String(100), nullable=False)
    resources = Column(JSONB, nullable=False, default=[])
    estimated_time = Column(Integer, nullable=True)
    actual_time = Column(Integer, nullable=True)
    difficulty = Column(Float, nullable=True)
    status = Column(
        String(50), default="pending"
    )  # 'pending', 'in_progress', 'completed'
    score = Column(Float, nullable=True)  # Test/quiz score
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    path = relationship("LearningPath", back_populates="steps")


class KnowledgeState(Base):
    __tablename__ = "knowledge_states"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    concept_id = Column(String(100), nullable=False, index=True)
    mastery_level = Column(Float, default=0.0)  # 0.0 to 1.0
    confidence = Column(Float, default=0.0)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    student = relationship("User", back_populates="knowledge_states")
